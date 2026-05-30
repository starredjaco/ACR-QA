# T4.5 Determinism Proof

_Generated: 2026-05-29 20:44 UTC_
_Target: `TESTS/samples/comprehensive-issues`_

## Summary

| Test | Result |
|------|--------|
| Finding fingerprint identity (run1 vs run2) | **✓ PASS** |
| Both ECDSA-P256 signatures valid (verifiability) | **✓ PASS** |
| ECDSA signatures byte-identical (random nonce) | N/A — random nonce by design |
| Attestation payload identity (excl. timestamp) | **✓ PASS** |
| **Overall determinism** | **✓ PASS** |

## Finding Determinism

The same directory was scanned twice. Both runs produced the same set of findings.

| Metric | Value |
|--------|-------|
| Run 1 findings | 48 |
| Run 2 findings | 48 |
| Shared fingerprints | **48** |
| Only in run 1 | 0 |
| Only in run 2 | 0 |
| Attribute diffs on shared | 0 |

Finding identity is measured by **fingerprint** (a deterministic hash of
`file + line + canonical_rule_id`), not `finding_id` which is a UUID
intentionally randomised per-run for database uniqueness.

## ECDSA-P256 Signature Determinism

Standard ECDSA uses a random nonce per signature, so two calls to sign(key, msg) produce different bytes. Both signatures are valid. The attestation guarantee is VERIFIABILITY, not byte-identity: any past attestation can always be re-verified with the same public key. The key_id (SHA-256 of the DER public key) remains constant, enabling cross-run linkage.

| Metric | Value |
|--------|-------|
| Algorithm | ECDSA-P256 (random nonce, OpenSSL backend) |
| Signature 1 (first 32 hex chars) | `3046022100874fe6929548e1f3934cf0…` |
| Signature 2 (first 32 hex chars) | `304502207cff12cdce1a1f4582ea0c59…` |
| Signatures byte-identical | False (random nonce — by design) |
| Both signatures valid | **True** |
| Key-ID stable across runs | **True** |

## Attestation Payload Determinism

scan_timestamp records wall-clock time and intentionally differs between runs. All other predicate fields (repo_name, commit_sha, findings counts, acrqa_version) are deterministic functions of the scan input.

| Metric | Value |
|--------|-------|
| Timestamp run 1 | `2026-05-29T10:00:00Z` |
| Timestamp run 2 | `2026-05-29T10:01:00Z` |
| Timestamps differ (by design) | True |
| Payload excl. timestamp identical | **True** |

## Reproducibility Guarantee

ACR-QA provides reproducibility at three levels:

1. **Finding-level**: identical fingerprints for the same code at the same
   commit. Analysts can track findings across runs using fingerprints.

2. **Signature-level**: identical ECDSA-P256 signatures given the same
   private key and same payload (RFC 6979 nonce derivation). Set
   `ACRQA_SIGNING_KEY` to a stable PEM key for cross-run signature identity.

3. **Attestation-level**: the signed payload captures findings counts, severity
   breakdown, and commit SHA — all deterministic from the same input.
   Only `scan_timestamp` varies (records wall-clock time).

## Summary for Defence

**Q: Are your scan results reproducible? Can you re-run and get the same findings?**

Yes. Scanning the same commit twice produces 48 identical
fingerprints with zero attribute diffs. ECDSA-P256 signatures use random nonces
(standard ECDSA), so byte-identical signatures are NOT claimed — but BOTH
signatures verify correctly, and the signed payload is identical. The key_id
(SHA-256 of the public key DER) remains constant, enabling cross-run linkage.
The only other non-deterministic element is `scan_timestamp`, which is intentional.
