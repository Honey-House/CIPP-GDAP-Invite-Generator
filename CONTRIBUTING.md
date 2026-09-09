# Contributing

Thanks for considering a contribution to this project.

## Reporting bugs

Open an [issue](../../issues) with:
- What you expected to happen vs. what actually happened
- Steps to reproduce
- Wrangler/Node version, and any relevant Worker logs (redact secrets, tenant IDs, and API keys)

## Suggesting features

Open an issue describing the use case before submitting a large PR, so we can discuss the approach first.

## Submitting changes

1. Fork the repo and create a branch from `main`.
2. Keep changes focused — one topic per PR.
3. Run `wrangler dev --local` to confirm the Worker still builds and runs.
4. Never commit secrets, real `wrangler.toml` values, tenant IDs, or CIPP API credentials. Keep example values as placeholders.
5. Open a PR describing what changed and why.

## Code style

- Match the existing TypeScript style in `src/worker.ts`.
- Keep the Worker dependency-free where practical — it's meant to stay simple to read, audit, and deploy.

## Security issues

Do not open a public issue for a security vulnerability — see [SECURITY.md](SECURITY.md).
