# Security policy

## Security model

This is a **local-first** tool. It is designed on the assumption that:

- the server binds to `127.0.0.1` only (**never expose it to a network** — there is no auth and no TLS)
- it is used by a single person on a single machine, with no accounts
- all data stays in local files; nothing is uploaded anywhere

The following are therefore **not** vulnerabilities:

- other local programs can read `data/ledger.json` (by design: it's your file)
- the server has no authentication (it only serves your own browser over loopback)
- no encryption at rest (use an encrypted disk or a private git repo if you need that)

## What to report

Please report these **privately**, not as a public issue:

- path traversal / arbitrary file read or write (e.g. crafting an `id` that escapes the data directory)
- the server becoming reachable from the LAN or the internet unexpectedly
- XSS when rendering user data (e.g. a job link or note being executed as HTML)
- anything that can corrupt data or silently lose it

## Contact

Use GitHub's [private security advisory](../../security/advisories/new), or email the maintainer (see the commit history).

Please include:

- reproduction steps and a minimal example
- impact (read / write / delete files?)
- your environment (OS / Python / browser version)

## Data safety tips

- Keep `data/ledger.json` in your own **private** git repo and commit regularly
- Do not make that repo public — it contains your applications, referrals and interview notes
- Back up `data/ledger.json` before upgrading (there are also 50 automatic snapshots in `data/.backup/`)
