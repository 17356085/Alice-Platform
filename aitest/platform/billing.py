"""Deterministic billing domain: price catalog, monthly invoices and reconciliation.

Payment collection is intentionally an adapter boundary. A real PSP must be
provided by deployment configuration; local mode records an externally-issued
payment reference but never pretends to charge a card.
"""

from __future__ import annotations

import json
import threading
import uuid
from calendar import monthrange
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


CENT = Decimal("0.01")


@dataclass(frozen=True)
class PricePlan:
    plan_id: str
    name: str
    monthly_base: Decimal
    included_tokens: int
    included_runs: int
    token_overage: Decimal
    run_overage: Decimal
    storage_gb_month: Decimal
    currency: str = "USD"

    def to_dict(self) -> dict:
        result = asdict(self)
        for key, value in list(result.items()):
            if isinstance(value, Decimal):
                result[key] = str(value)
        return result


DEFAULT_PLANS = {
    "free": PricePlan("free", "Free", Decimal("0.00"), 1_000_000, 100, Decimal("0.000010"), Decimal("0.00"), Decimal("0.00")),
    "pro": PricePlan("pro", "Pro", Decimal("49.00"), 10_000_000, 1_000, Decimal("0.000008"), Decimal("0.02"), Decimal("0.02")),
    "enterprise": PricePlan("enterprise", "Enterprise", Decimal("499.00"), 100_000_000, 10_000, Decimal("0.000005"), Decimal("0.01"), Decimal("0.01")),
}


class PricingCatalog:
    def __init__(self, plans: dict[str, PricePlan] | None = None):
        self._plans = dict(plans or DEFAULT_PLANS)

    def get(self, plan_id: str) -> PricePlan:
        try:
            return self._plans[plan_id]
        except KeyError as exc:
            raise ValueError(f"Unknown billing plan: {plan_id}") from exc

    def list(self) -> list[dict]:
        return [plan.to_dict() for plan in self._plans.values()]


def monthly_period(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    return start, date(year, month, monthrange(year, month)[1])


def current_month_period() -> tuple[date, date]:
    now = datetime.now(timezone.utc)
    return monthly_period(now.year, now.month)


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_invoice(plan: PricePlan, usage: dict, period_start: date, period_end: date, org_id: str) -> dict:
    tokens = max(0, int(usage.get("token_usage", usage.get("tokens", 0)) or 0))
    runs = max(0, int(usage.get("run_count", usage.get("runs", 0)) or 0))
    storage_bytes = max(0, int(usage.get("storage_bytes", 0) or 0))
    storage_gb = Decimal(storage_bytes) / Decimal(1024 ** 3)
    token_units = max(0, tokens - plan.included_tokens)
    run_units = max(0, runs - plan.included_runs)
    lines = [
        {"description": f"{plan.name} monthly base", "quantity": 1, "unit_price": str(plan.monthly_base), "amount": str(_money(plan.monthly_base))},
        {"description": "Token overage", "quantity": token_units, "unit_price": str(plan.token_overage), "amount": str(_money(Decimal(token_units) * plan.token_overage))},
        {"description": "Run overage", "quantity": run_units, "unit_price": str(plan.run_overage), "amount": str(_money(Decimal(run_units) * plan.run_overage))},
        {"description": "Storage GB-month", "quantity": str(storage_gb), "unit_price": str(plan.storage_gb_month), "amount": str(_money(storage_gb * plan.storage_gb_month))},
    ]
    total = _money(sum((Decimal(line["amount"]) for line in lines), Decimal("0")))
    return {
        "invoice_id": f"inv_{uuid.uuid4().hex[:16]}", "org_id": org_id, "plan_id": plan.plan_id,
        "currency": plan.currency, "period_start": period_start.isoformat(), "period_end": period_end.isoformat(),
        "usage": {"tokens": tokens, "runs": runs, "storage_bytes": storage_bytes}, "lines": lines,
        "subtotal": str(total), "total": str(total), "status": "draft", "payments": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


class BillingLedger:
    """Small durable ledger used by local/CI mode and as a PSP reconciliation boundary."""

    def __init__(self, path: str | Path | None = None, catalog: PricingCatalog | None = None):
        self.path = Path(path) if path else Path("governance/.data/billing_state.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.catalog = catalog or PricingCatalog()
        self._lock = threading.Lock()
        self._state = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"invoices": {}, "payments": [], "reconciliations": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"invoices": {}, "payments": [], "reconciliations": []}

    def _save(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def create_invoice(self, org_id: str, plan_id: str, usage: dict, period_start: date | None = None, period_end: date | None = None) -> dict:
        start, end = (period_start, period_end) if period_start and period_end else current_month_period()
        plan = self.catalog.get(plan_id)
        with self._lock:
            for invoice in self._state["invoices"].values():
                if invoice["org_id"] == org_id and invoice["period_start"] == start.isoformat() and invoice["period_end"] == end.isoformat():
                    return invoice
            invoice = calculate_invoice(plan, usage, start, end, org_id)
            self._state["invoices"][invoice["invoice_id"]] = invoice
            self._save()
            return invoice

    def issue(self, invoice_id: str) -> dict:
        invoice = self.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice not found: {invoice_id}")
        if invoice["status"] == "draft":
            invoice["status"] = "issued"
            self._save()
        return invoice

    def get(self, invoice_id: str) -> dict | None:
        return self._state["invoices"].get(invoice_id)

    def list(self, org_id: str | None = None) -> list[dict]:
        invoices = list(self._state["invoices"].values())
        return [item for item in invoices if not org_id or item["org_id"] == org_id]

    def record_payment(self, invoice_id: str, amount: Decimal | str, gateway_reference: str, currency: str = "USD") -> dict:
        invoice = self.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice not found: {invoice_id}")
        if not gateway_reference:
            raise ValueError("gateway_reference is required; no live payment provider is configured")
        payment = {"payment_id": f"pay_{uuid.uuid4().hex[:16]}", "invoice_id": invoice_id, "amount": str(_money(Decimal(str(amount)))), "currency": currency, "gateway_reference": gateway_reference, "status": "received", "created_at": datetime.now(timezone.utc).isoformat()}
        with self._lock:
            self._state["payments"].append(payment)
            invoice["payments"].append(payment["payment_id"])
            self._save()
        return payment

    def reconcile(self, invoice_id: str) -> dict:
        invoice = self.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice not found: {invoice_id}")
        payments = [p for p in self._state["payments"] if p["invoice_id"] == invoice_id and p["status"] == "received"]
        paid = _money(sum((Decimal(p["amount"]) for p in payments), Decimal("0")))
        expected = Decimal(invoice["total"])
        result = {"invoice_id": invoice_id, "expected": str(expected), "received": str(paid), "difference": str(_money(paid - expected)), "status": "matched" if paid == expected else ("underpaid" if paid < expected else "overpaid"), "checked_at": datetime.now(timezone.utc).isoformat()}
        invoice["status"] = "paid" if result["status"] == "matched" else invoice["status"]
        self._state["reconciliations"].append(result)
        self._save()
        return result


_ledger: BillingLedger | None = None


def get_billing_ledger() -> BillingLedger:
    global _ledger
    if _ledger is None:
        _ledger = BillingLedger()
    return _ledger
