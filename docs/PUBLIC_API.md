# Public API policy

This is a **browser tool**, not an integrator API. It is a single Cloudflare Worker (`src/worker.ts`)
that serves one HTML page and two JSON routes the page calls. Last reviewed 2026-10-12.

## OpenAPI exception

The [Honey House / WOSP OpenAPI standard](https://github.com/Honey-House/Honey-House-Company-Documentation/blob/main/docs/decided/openapi-api-standard.md)
asks every JSON HTTP API for `/api/openapi.json` and `/api/docs`. This project records an exception:

- There is **no supported API for third-party automation**, so no OpenAPI document and no Swagger UI is
  served. Do not add `/api/docs` or `/api/openapi.json` to this Worker.
- The two routes below exist only to serve the page. They can change without notice and are not a contract.
- If a real integrator API is ever wanted, build it in a FastAPI container that follows the standard and
  have this Worker call it, rather than growing the Worker. A Worker would otherwise need a code-first
  OpenAPI generator (for example Hono with Zod OpenAPI) and the standard paths.
- No sunset date applies: there are no legacy paths.

## What the Worker serves

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | The HTML page |
| GET | `/api/templates` | Lists CIPP GDAP role templates (calls CIPP `ExecGDAPRoleTemplate`) |
| POST | `/api/generate-invite` | Creates a GDAP invite from `{ "roleMappings": [...] }` (calls CIPP `ExecGDAPInvite`) |

## Authentication and access

The Worker has **no authentication of its own**. It holds a CIPP API credential (`CIPP_API_SECRET` as a
Worker secret) and uses it for every request, so **whoever can reach the hostname can list role templates
and create GDAP invites**.

- **Required:** put the hostname behind Cloudflare Zero Trust (Cloudflare Access) before deploying. The
  README says the same. Treat an unprotected deployment as a security incident.
- Never expose the Worker on `workers.dev` or an open public hostname.
- Not implemented, worth adding: verify the Cloudflare Access JWT (`Cf-Access-Jwt-Assertion`) inside the
  Worker, so a misrouted or unprotected hostname fails closed instead of serving the page.
- Not implemented: rate limiting or Turnstile. Put a Cloudflare rate-limit rule on `/api/*` until it is.

## Engineering

Internal OpenAPI artifacts, if any are ever produced, belong under `openapi/` in this repo for agents and
release export, never on the public hostname.
