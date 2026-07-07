# Phase 4 Extension Template

This document is the reusable baseline for future provider / capability / graph
extensions.

## 1. Extension contract

Every new extension should expose:

- stable identity
- human-readable name
- module / entrypoint metadata
- availability flag
- source marker
- `extra` metadata for non-breaking growth

## 2. Provider extension

When adding a provider:

- define a stable provider name
- describe tool support and streaming support
- keep the discovery contract buildable without instantiation
- cover registration and lookup with a contract test

## 3. Capability extension

When adding a capability provider:

- define a capability id and tool name
- keep the tool definition JSON-schema friendly
- ensure capability discovery can list the contract
- validate agent-scoped discovery if the capability is gated

## 4. Graph extension

When adding a graph:

- define a stable graph id
- expose builder metadata
- keep graph construction callable through the registry
- validate discovery and build behavior in a contract test

## 5. Contract test checklist

- the sample extension can be discovered
- the contract shape stays stable
- the extension can be built or executed
- the test is reusable as a future template

## 6. Review rule

Any new extension PR should link to this template and add at least one
contract-level test that can be copied by the next extension.
