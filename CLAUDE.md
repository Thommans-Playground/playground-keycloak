# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repository is currently empty aside from this file and the README — there is no application code, build tooling, or test suite yet. There are no build/lint/test commands to document until code is added; update this file as soon as a stack is chosen.

## Project intent

This is a playground for learning Keycloak (per README.md), with two intended phases of work:

1. **Local Keycloak hands-on setup** — running Keycloak (via Docker), configuring realms/clients/users, and wiring a sample app to it over OIDC (Authorization Code + PKCE), then exploring realm export/import, custom themes, and SPIs.
2. **Multi-repo distribution** — packaging the resulting realm config/theme/SPI artifacts into a dedicated `keycloak-config` repo, distributed to other company project repos via Google's `repo` multi-repository tool (a manifest repo referencing `keycloak-config` alongside each product repo, with per-project revision pinning).

When adding code, prefer structuring it around these two phases rather than a generic app layout.
