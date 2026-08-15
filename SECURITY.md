# Security Policy

## Supported versions

Security fixes apply to the current `main` branch of this catalog repository.

## Reporting a vulnerability

Once this repository is on GitHub, report vulnerabilities through GitHub
**private vulnerability reporting** (Security Advisories) for this repo.
Do not open a public issue for:

- Credentials or secrets exposed in the repository
- Exploitable scraper behavior (SSRF, code injection via parsed HTML)
- GitHub Actions workflow permission escalation
- Supply-chain risks in dependencies

Include:

1. Affected file, workflow, or component
2. Steps to reproduce
3. Expected impact
4. Suggested mitigation (if known)

The maintainer will acknowledge the report and coordinate remediation and disclosure.

Until the GitHub remote exists, contact the maintainer privately by the same
channel you already use for this project — still do not file a public issue.

## Response expectations

- Acknowledgment: within 7 days
- Status update: within 30 days
- Fix or documented mitigation for confirmed issues affecting `main`

## Scope

| In scope | Out of scope |
|----------|--------------|
| This repository's code, workflows, and published catalog files | Third-party company career sites being scraped |
| Data integrity of `data/active/` and `data/archived/` | Social engineering of employer pages |
| Dependency vulnerabilities in `requirements.txt` | A future website that *consumes* this catalog |

## What not to report here

- Stale or incorrect listings (use the Add internship issue, or a blank issue for corrections)
- Scrapers failing because a company changed their page layout
- Rate limiting or blocking by target websites during normal scraping

## Secure development practices

- Never commit secrets, session cookies, or API keys
- Treat scraped HTML as untrusted input
- Keep GitHub Actions permissions at the minimum required level
- Review automation-generated PRs before merging

## Related

- [NOTICE](NOTICE) — licensing
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to suggest listings
