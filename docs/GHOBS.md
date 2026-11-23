# Good Heart Open Build Standard

This repository declares GHOBS v1 with checker 0.1.12. The adoption change is documentation, tooling, and offline tests only; it does not alter Worker routes, its authentication boundary, Microsoft permissions, or its deployment configuration.

## Scope

This is the publicly distributed Honey House source; deployed instances are for explicitly authorized staff. Public distribution does not make any installation public. This is a browser-only Cloudflare Worker. The two same-origin JSON routes are UI transport, not a supported integration API (see [API policy](PUBLIC_API.md)). Do not add public Swagger, OpenAPI, or MCP routes. Continue protecting the entire deployment with Cloudflare Access. Do not test a live invitation action as part of a documentation rollout.

Public source distribution is not a public discovery website. Omit the optional `website: public` profile and do not publish sitemap, robots, or llms discovery files for protected installations. Revisit website discovery and accessibility only if an approved public site is established; ordinary browser-tool accessibility still matters.

## Validate and update

1. In a clean checkout, run `python .ghobs/ghobs.py check` and `node --test tests/browser-policy.test.mjs` with Node 22.18+ or Node 24. The test renders the local browser shell with fake config, checks that integration documentation and MCP paths remain absent, and guards against outgoing fetches.
2. This repository does not gain an Actions workflow. The manifest records local check and manual upstream sync exceptions. A maintainer can vendor a pinned upstream release from an authorized standard checkout using `python .ghobs/ghobs.py sync --standard-dir /path/to/standard`; do not stage any new `.github/workflows/ghobs-*.yml` produced by the generic sync.
3. Review the Worker authentication, authorization, client-side logging, accessibility, and operational deployment independently before a runtime release. The structural checker and offline tests do not certify production controls.

## Handoff

[GitHub Issues](https://github.com/Honey-House/CIPP-GDAP-Invite-Generator/issues) is canonical; issue numbers are the stable IDs. The tracker audit found no open or closed human issues to move or migrate. There was no live issue to sample for field-level verification. Check a real item when one exists, and do not create a placeholder item solely to pass the manual review.

Use the active issue as the task record. Include owner/availability, starting and current commit, completed changes, verification results, open items, and the next concrete step. Never include tokens, real tenant data, or customer payloads. Verify a deployment separately in the Cloudflare dashboard against the expected revision and use an approved non-mutating verification path.

Initial baseline: `main` at `65be931936ae8701aa7b6633dc73f6318a202f1d`. Rollout acceptance: managed files and manifest are present, strict structural check passes (with the two Actions exceptions), offline tests pass, and runtime/deployment files are unchanged. No live validation was performed in this rollout.
