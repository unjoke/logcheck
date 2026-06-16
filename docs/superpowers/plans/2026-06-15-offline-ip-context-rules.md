---
change: add-offline-ip-context-rules
design-doc: docs/superpowers/specs/2026-06-15-offline-ip-context-rules-design.md
base-ref: f95403e0f28219aee630bed44884bfc2110103ab
---

# Offline IP Context Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic offline source-address context and a public-source cluster rule without introducing GeoIP, DNS, maps, remote lookup, scanning, blocking, or external reporting.

**Architecture:** Create a focused `logcheck/ip_context.py` classifier backed by Python's `ipaddress` module. Parser code attaches classification metadata to events, and the rule engine uses that metadata in a post-processing rule that only emits `behavior.public_source_cluster` for globally routable sources with repeated suspicious findings.

**Tech Stack:** Python 3.12, standard-library `ipaddress`, dataclasses, pytest, existing Logcheck parser/rule/model modules.

---

## File Structure

- Create `logcheck/ip_context.py`: owns IP classification and serialization into plain dictionaries.
- Modify `logcheck/parsers.py`: attaches `metadata["source_address_context"]` when `source_address` is extracted.
- Modify `logcheck/rules.py`: adds the public-source cluster contextual rule.
- Create `tests/test_ip_context.py`: tests classifier categories and parser metadata.
- Modify `tests/test_rules.py`: tests public-source cluster creation and non-global suppression.
- Update `openspec/changes/add-offline-ip-context-rules/tasks.md`: tracks implementation completion.

## Implementation Note

This plan documents the implementation that has already been committed in `f95403e feat: add offline ip context rules`. If re-executing from a pre-implementation base, follow the TDD steps below in order.

### Task 1: Offline IP Context Classifier

**Files:**
- Create: `logcheck/ip_context.py`
- Create: `tests/test_ip_context.py`

- [x] **Step 1: Write the failing classifier tests**

```python
from logcheck.ip_context import classify_ip_address


def test_classify_private_address_as_non_global():
    context = classify_ip_address("192.168.2.1")

    assert context.is_valid is True
    assert context.is_global is False
    assert context.category == "private"
    assert "private" in context.reason.lower()


def test_classify_documentation_address_as_non_global():
    context = classify_ip_address("203.0.113.10")

    assert context.is_valid is True
    assert context.is_global is False
    assert context.category == "documentation"
    assert "documentation" in context.reason.lower()


def test_classify_public_address_as_global():
    context = classify_ip_address("8.8.8.8")

    assert context.is_valid is True
    assert context.is_global is True
    assert context.category == "global"
    assert "globally routable" in context.reason.lower()


def test_classify_invalid_address_returns_stable_context():
    context = classify_ip_address("999.1.1.1")

    assert context.is_valid is False
    assert context.is_global is False
    assert context.category == "invalid"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ip_context.py -q`

Expected before implementation: FAIL with `ModuleNotFoundError: No module named 'logcheck.ip_context'`.

- [x] **Step 3: Implement minimal classifier**

```python
from __future__ import annotations

from dataclasses import dataclass
import ipaddress


DOCUMENTATION_NETWORKS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("2001:db8::/32"),
)


@dataclass(frozen=True)
class IPContext:
    address: str
    is_valid: bool
    version: int | None
    category: str
    is_global: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "address": self.address,
            "is_valid": self.is_valid,
            "version": self.version,
            "category": self.category,
            "is_global": self.is_global,
            "reason": self.reason,
        }


def classify_ip_address(address: str) -> IPContext:
    try:
        ip_obj = ipaddress.ip_address(address)
    except ValueError:
        return IPContext(address, False, None, "invalid", False, "Invalid IP address format.")

    if any(ip_obj in network for network in DOCUMENTATION_NETWORKS):
        return IPContext(address, True, ip_obj.version, "documentation", False, "Documentation or test address range.")
    if ip_obj.is_private:
        return IPContext(address, True, ip_obj.version, "private", False, "Private address used inside local networks.")
    if ip_obj.is_loopback:
        return IPContext(address, True, ip_obj.version, "loopback", False, "Loopback address reserved for local host use.")
    if ip_obj.is_link_local:
        return IPContext(address, True, ip_obj.version, "link-local", False, "Link-local address reserved for local network discovery.")
    if ip_obj.is_multicast:
        return IPContext(address, True, ip_obj.version, "multicast", False, "Multicast address is not globally routable.")
    if ip_obj.is_unspecified:
        return IPContext(address, True, ip_obj.version, "unspecified", False, "Unspecified address is not a routable source.")
    if ip_obj.is_reserved:
        return IPContext(address, True, ip_obj.version, "reserved", False, "Reserved address range is not globally routable.")
    if not ip_obj.is_global:
        return IPContext(address, True, ip_obj.version, "documentation", False, "Documentation or special-use address range.")

    return IPContext(address, True, ip_obj.version, "global", True, "Globally routable public source address.")
```

- [x] **Step 4: Run tests to verify classifier passes**

Run: `python -m pytest tests/test_ip_context.py -q`

Expected after implementation: PASS.

### Task 2: Parser Metadata Attachment

**Files:**
- Modify: `logcheck/parsers.py`
- Modify: `tests/test_ip_context.py`

- [x] **Step 1: Write the failing parser metadata test**

```python
from logcheck.parsers import parse_line


def test_parse_line_preserves_source_address_context_metadata():
    event = parse_line(
        "access.log",
        1,
        '8.8.8.8 - - [01/Sep/2021:01:37:25 +0000] "GET /index.php HTTP/1.1" 200 512',
    )

    assert event.metadata["source_address_context"]["address"] == "8.8.8.8"
    assert event.metadata["source_address_context"]["category"] == "global"
    assert event.metadata["source_address_context"]["is_global"] is True
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ip_context.py::test_parse_line_preserves_source_address_context_metadata -q`

Expected before parser change: FAIL with missing `source_address_context`.

- [x] **Step 3: Attach context in parser**

In `logcheck/parsers.py`, import the classifier:

```python
from .ip_context import classify_ip_address
```

For auth and application matches, compute `source_address = _extract_ip(line)` once and pass:

```python
metadata={
    "source_address_context": classify_ip_address(source_address).to_dict()
    if source_address
    else None
}
```

For access-log matches, add context while preserving existing metadata:

```python
metadata={
    **metadata,
    "source_address_context": classify_ip_address(source_address).to_dict(),
}
```

- [x] **Step 4: Run parser-focused tests**

Run: `python -m pytest tests/test_ip_context.py tests/test_parsers.py -q`

Expected after implementation: PASS.

### Task 3: Public Source Cluster Rule

**Files:**
- Modify: `logcheck/rules.py`
- Modify: `tests/test_rules.py`

- [x] **Step 1: Write failing rule tests**

Add tests asserting:

```python
public_clusters = [
    finding
    for finding in findings
    if finding.rule_id == "behavior.public_source_cluster"
]
self.assertEqual(len(public_clusters), 1)
self.assertEqual(public_clusters[0].source_address, "8.8.8.8")
self.assertIn("globally routable", public_clusters[0].explanation.lower())
self.assertLessEqual(len(public_clusters[0].evidence), 5)
```

And suppression:

```python
self.assertFalse(
    any(
        finding.rule_id == "behavior.public_source_cluster"
        for finding in findings
    )
)
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_public_source_cluster_created_for_global_source_with_multiple_signals tests/test_rules.py::RuleTests::test_public_source_cluster_suppresses_private_and_documentation_sources -q
```

Expected before rule implementation: FAIL because no `behavior.public_source_cluster` is emitted.

- [x] **Step 3: Implement the rule**

In `logcheck/rules.py`, add:

```python
findings.extend(_public_source_cluster_findings(findings, events))
```

Then implement helpers that read parser metadata, fall back to `classify_ip_address()`, group findings by `source_address`, suppress non-global sources, and emit one medium-severity bounded-evidence finding per global source.

- [x] **Step 4: Run focused rule tests**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_public_source_cluster_created_for_global_source_with_multiple_signals tests/test_rules.py::RuleTests::test_public_source_cluster_suppresses_private_and_documentation_sources -q
```

Expected after implementation: PASS.

### Task 4: Verification And Commit

**Files:**
- Modify: `openspec/changes/add-offline-ip-context-rules/tasks.md`

- [x] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_ip_context.py tests/test_rules.py::RuleTests::test_public_source_cluster_created_for_global_source_with_multiple_signals tests/test_rules.py::RuleTests::test_public_source_cluster_suppresses_private_and_documentation_sources -q
```

Expected: `7 passed`.

- [x] **Step 2: Run parser and rules regression tests**

Run:

```bash
python -m pytest tests/test_parsers.py tests/test_rules.py -q
```

Expected: all selected parser and rule tests pass.

- [x] **Step 3: Run full verification**

Run:

```bash
python -m pytest -q
python -m py_compile logcheck/ip_context.py logcheck/parsers.py logcheck/rules.py
```

Expected: full test suite passes and py_compile exits 0.

- [x] **Step 4: Mark implementation tasks complete**

Update `openspec/changes/add-offline-ip-context-rules/tasks.md` so implementation and verification tasks are checked.

- [x] **Step 5: Commit and push**

Run:

```bash
git add -- logcheck/ip_context.py logcheck/parsers.py logcheck/rules.py tests/test_ip_context.py tests/test_rules.py openspec/changes/add-offline-ip-context-rules
git commit -m "feat: add offline ip context rules"
git push origin codex/optimize-access-log-detection-rules
```

Expected: commit `f95403e feat: add offline ip context rules` exists on the remote branch.

## Self-Review

- Spec coverage: The plan maps to both OpenSpec requirements: preserving offline source address context and highlighting repeated suspicious activity from public sources while suppressing non-global sources.
- Placeholder scan: No placeholder tasks remain.
- Type consistency: The plan consistently uses `classify_ip_address`, `IPContext`, `source_address_context`, and `behavior.public_source_cluster`.
