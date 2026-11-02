# Reconcile duplicate active/archive identities before publication

The user authorized publication to main on 2026-11-02. Remote main at
`1dc1c63a9b5f142662d12660c0005a30c111a82a` has three IDs present in both catalogs.
The merged local hardening correctly rejects these overlaps. This is a separate
maintainer data reconciliation, not contributor scraper output or an eligibility
cleanup. No live HTTP, new discovery, force-close, or inferred opening is involved.

| ID | Company | Stored active last_seen | Stale archived closed_at | Preserved earliest first_seen |
|---|---|---|---|---|
| 57fb7a25-33a2-5ec7-8de4-e7c9fc08b534 | Boston Scientific | 2026-10-25 | 2026-09-20 | 2026-09-15 |
| a973b7c0-3d5e-50b6-9922-56654e5a224d | Boston Scientific | 2026-10-25 | 2026-10-23 | 2026-10-19 |
| ce8365a3-e267-5fbb-bddc-91969921a439 | Philips | 2026-10-24 | 2026-10-22 | 2026-09-12 |

Existing `apply_archive_rules` reconciliation gives a rediscovered active posting
precedence over its stale archived copy while restoring its original first_seen.
Apply it only to the three overlapping postings with no probe session and their
companies marked unavailable, preserving all stored miss/last_seen evidence.
Combine the reconciled records with all unaffected active rows. This is not a new
scrape observation. Assertions verify the exact first_seen-only active differences
and exact removal of three archived records before schema/disjoint validation.

Active count stays 79; archived count changes from 86 to 83. Correct only the
health archived_count; preserve the old sweep date, updated_count, and failures.
Regenerate the three README views at the stored sweep date to avoid presenting a
new sweep or changing ages merely because this maintenance runs later. The current
live availability and eligibility of these postings remain unverified.

Prepared outputs are reviewed separately from the classifier commit, then
published using the existing recoverable multi-file publication mechanism.

Independent read-only review accepted the candidate: all 79 active identities,
miss evidence, last_seen dates, URLs, and unaffected archived rows are preserved.
The three stored active observations postdate their stale archive closures.
Independent archive-rule recomputation and stable UUID checks matched the
candidate; schema validation and cross-catalog uniqueness passed. No reviewer
file changes or live probes were performed.
