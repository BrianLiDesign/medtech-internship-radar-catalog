# Slice — jobs2web search adapters (Teleflex, Olympus, Arthrex)

**Status:** Implemented with mocked tests. Live intern-keyword search on 2026-08-15 returned no intern-titled reqs (hits were Internal/International titles or intern mentioned in descriptions). Production catalog is unchanged until daily refresh.

**Locked constraints:** Public jobs2web `GET /search/?q=intern` listing HTML only (and the public RSS sibling). Do not reverse-engineer Workday CXS/search. Do not use login-walled SuccessFactors `career_ns` HTML. Treat listing HTML as untrusted (title/location/href only). Mock HTTP in CI.

## Scope

| Company | Origin |
|---------|--------|
| Teleflex | `https://careers.teleflex.com/search/` |
| Olympus | `https://careers.olympusamerica.com/search/` |
| Arthrex | `https://careers.arthrex.com/search/` |

Shared adapter: `scripts/jobs2web_adapter.py`.

## Behaviors to test

1. Framework registers `Teleflex`, `Olympus`, and `Arthrex` (not the shared base class).
2. Fixture US STEM intern is a `posting`; HR, sales, Internal Communications, and non-US intern titles drop.
3. Empty listing HTML keeps the program-fallback hub.
4. 403 / blocked HTTP soft-fail.

## Done when

Lint + pytest + validate green. `--fixture` remains Boston Scientific-only.
