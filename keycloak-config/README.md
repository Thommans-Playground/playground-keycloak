# keycloak-config

Realm `playground` for the Playground auth module. In phase 2 of the playground this folder becomes its own repo, pulled into product repos with `repo`.

```bash
docker compose up -d        # Keycloak at http://localhost:8080 (admin / admin)
docker compose down -v      # wipe it and re-import the realm
```

| Thing | Value |
|---|---|
| Realm | `playground`, self-registration on, email is the username |
| `playground-web` | confidential, code flow + PKCE S256, redirect `http://localhost:3000/auth/callback`, adds audience `playground-api` |
| `playground-backend` | service account with `view-users`, `query-users`, `manage-users`. Used to enable or disable people |
| `admin@example.test` / `Admin123!` | becomes the first administrator (set in `BOOTSTRAP_ADMIN_EMAILS` for the API) |
| `maya@example.test` / `Maya123!` | an ordinary person. Pending on first request until approved |
| Tokens | access 5 min. SSO session 30 min idle, 8 h max |

The secrets and passwords are dev-only. Change them for any shared environment.
Re-importing: `--import-realm` skips a realm that already exists, so use `down -v` after editing the JSON.
