# Inventory Review Webapp

Local Streamlit app for reviewing MEP take-off inventory.

See [PLAN.md](PLAN.md) for the full design (Linear GR-6).

## Quick start

```bash
# from repo root
uv pip install -r apps/inventory_webapp/requirements.txt
python apps/inventory_webapp/seed.py          # creates inventory.db
streamlit run apps/inventory_webapp/app.py
```

The seeder prefers the Hubby Excel if present under `/workspace/attachments/`; otherwise it falls back to `evals/datasets/hubby-premier-inn-london/expected/floors.json`.

## Features

- Project and drawing selection from SQLite
- Inventory table with approve / exclude / amend
- Summary by floor and by category
- PDF path placeholder (ready for overlays)

No costs or labour.
