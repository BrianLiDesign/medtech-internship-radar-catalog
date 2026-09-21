# ADR-0005: Newest-first README as a second generated view

The landing README is grouped by role family (HANDOFF Q11). Students also need a newest-first scan, but changing that landing sort would hide the role-family browse. Generate `README-Newest.md` from the same visible catalog rows as `README.md`: one flat table, Age descending, undated program-fallback hubs at the bottom. Do not parse markdown; the catalog remains the source of truth.
