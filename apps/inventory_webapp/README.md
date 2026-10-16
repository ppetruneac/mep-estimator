# Inventory review webapp (GR-6)

FastAPI + React app for reviewing Hubby (and future) take-offs stored in `$DATA_DIR/getriser.sqlite`.

## Quick start (Make)

From the **repo root**:

```bash
export DATA_DIR=/Users/pico/workspace/data/getriser
make seed-hubby      # if DB empty
make check-ports
make up              # UI :8870  API :8871
```

Or host-native:

```bash
make migrate
make dev-api         # :8871
make dev-ui          # :5173 (proxies /api)
```

## Stack

| Layer | Choice |
|---|---|
| API | FastAPI on `getriser.sqlite` (review columns migrated on boot) |
| UI | React + Vite; Docker serves via nginx with `/api` proxy |
| Data | `$DATA_DIR/getriser.sqlite` — same DB as `riser-inventory` |

## Ports

Defaults **8870** (UI) / **8871** (API). Override with `RISER_UI_PORT` / `RISER_API_PORT` if busy (do not commit remaps).
