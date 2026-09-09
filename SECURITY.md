# Security Policy

## Supported versions

This project is deployed as a single Cloudflare Worker without version branches. Only the code on `main` is supported.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities — this tool has access to your CIPP API and can generate GDAP invitations, so reports may involve sensitive deployment details.

Instead, use GitHub's [private vulnerability reporting](../../security/advisories/new) for this repository, if enabled, or open a draft security advisory. If that isn't available, contact the repository maintainer directly through GitHub.

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce (proof of concept if possible)
- Any suggested fix, if you have one

We'll acknowledge reports as quickly as we can and work with you on a fix and disclosure timeline.

## Notes on this project's threat model

This application **must** be protected with Cloudflare Zero Trust before deployment — see the [Security Warning](README.md#-security-warning) in the README. It has access to your CIPP API and can generate GDAP invitations to your tenants. Reports about the app being reachable without Zero Trust configured by a deployer are a deployment/configuration concern, not a vulnerability in the code itself, but we're still interested in ways the app could better guide safe deployment.
