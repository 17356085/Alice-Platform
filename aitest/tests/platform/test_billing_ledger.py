"""Price table, invoice-cycle and reconciliation tests."""

from datetime import date
from decimal import Decimal

from aitest.platform.billing import BillingLedger, PricingCatalog, monthly_period


def test_catalog_has_formal_plans_and_monthly_period():
    plans = PricingCatalog().list()
    assert {plan["plan_id"] for plan in plans} == {"free", "pro", "enterprise"}
    assert monthly_period(2026, 2) == (date(2026, 2, 1), date(2026, 2, 28))


def test_invoice_is_idempotent_and_reconciles_exact_payment(tmp_path):
    ledger = BillingLedger(tmp_path / "billing.json")
    usage = {"token_usage": 10_000_000, "run_count": 1_001, "storage_bytes": 0}
    first = ledger.create_invoice("org-a", "pro", usage, date(2026, 7, 1), date(2026, 7, 31))
    second = ledger.create_invoice("org-a", "pro", usage, date(2026, 7, 1), date(2026, 7, 31))
    assert first["invoice_id"] == second["invoice_id"]
    ledger.issue(first["invoice_id"])
    ledger.record_payment(first["invoice_id"], Decimal(first["total"]), "psp-test-1")
    result = ledger.reconcile(first["invoice_id"])
    assert result["status"] == "matched"
    assert ledger.get(first["invoice_id"])["status"] == "paid"


def test_reconciliation_detects_underpayment(tmp_path):
    ledger = BillingLedger(tmp_path / "billing.json")
    invoice = ledger.create_invoice("org-a", "pro", {}, date(2026, 7, 1), date(2026, 7, 31))
    ledger.record_payment(invoice["invoice_id"], "1.00", "psp-test-2")
    assert ledger.reconcile(invoice["invoice_id"])["status"] == "underpaid"
