"""Inventory review webapp (Streamlit).

Run:
  cd apps/inventory_webapp
  streamlit run app.py

Or from repo root after seeding:
  uv run --with streamlit streamlit run apps/inventory_webapp/app.py
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "inventory.db"


def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        st.error(f"Database not found at {DB_PATH}. Run seed.py first.")
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def load_projects(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM projects", conn)


def load_drawings(conn: sqlite3.Connection, project_id: int) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM drawings WHERE project_id = ? ORDER BY floor_tab_name",
        conn,
        params=(project_id,),
    )


def load_items(conn: sqlite3.Connection, drawing_id: int) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM inventory_items WHERE drawing_id = ? ORDER BY line",
        conn,
        params=(drawing_id,),
    )


def update_item_status(conn: sqlite3.Connection, item_id: int, status: str, amended_count=None, amended_notes=None) -> None:
    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE inventory_items
           SET status = ?, amended_count = ?, amended_notes = ?, reviewed_at = ?
           WHERE id = ?""",
        (status, amended_count, amended_notes, now, item_id),
    )
    conn.commit()


def main() -> None:
    st.set_page_config(page_title="MEP Inventory Review", layout="wide")
    st.title("MEP Inventory Review")
    st.caption("Approve / exclude / amend take-off items. No costs or labour.")

    conn = get_conn()

    projects = load_projects(conn)
    if projects.empty:
        st.warning("No projects. Run seed.py.")
        return

    project_name = st.sidebar.selectbox(
        "Project",
        projects["name"].tolist(),
        index=0,
    )
    project_id = int(projects.loc[projects["name"] == project_name, "id"].iloc[0])

    drawings = load_drawings(conn, project_id)
    if drawings.empty:
        st.info("No drawings for this project.")
        return

    drawing_label = drawings["floor_tab_name"].tolist()
    selected_label = st.sidebar.selectbox("Drawing / Floor", drawing_label)
    drawing_row = drawings[drawings["floor_tab_name"] == selected_label].iloc[0]
    drawing_id = int(drawing_row["id"])

    st.sidebar.markdown("---")
    view = st.sidebar.radio("View", ["Inventory", "Summary by floor", "Summary by category"])

    if view == "Inventory":
        st.subheader(f"{drawing_row['floor_tab_name']}  ·  {drawing_row.get('drawing_number', '')}")
        if drawing_row.get("source_pdf"):
            st.markdown(f"[Open PDF]({drawing_row['source_pdf']})")
        else:
            st.info("PDF path not set. Overlays will appear here when the extractor writes them.")

        items = load_items(conn, drawing_id)
        if items.empty:
            st.write("No items.")
            return

        # Editable table via data_editor
        edited = st.data_editor(
            items,
            column_config={
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["pending", "approved", "excluded", "amended"],
                    required=True,
                ),
                "amended_count": st.column_config.NumberColumn("Amended count"),
                "amended_notes": st.column_config.TextColumn("Amended notes"),
                "measurement_type": st.column_config.TextColumn("Measurement"),
                "scope": st.column_config.TextColumn("Scope"),
            },
            disabled=["id", "drawing_id"],
            hide_index=True,
            use_container_width=True,
            key=f"editor_{drawing_id}",
        )

        if st.button("Save changes"):
            for _, row in edited.iterrows():
                update_item_status(
                    conn,
                    int(row["id"]),
                    row["status"],
                    row.get("amended_count"),
                    row.get("amended_notes"),
                )
            st.success("Saved.")
            st.rerun()

        # Quick actions
        cols = st.columns(3)
        if cols[0].button("Approve all pending"):
            conn.execute(
                "UPDATE inventory_items SET status = 'approved', reviewed_at = ? WHERE drawing_id = ? AND status = 'pending'",
                (datetime.utcnow().isoformat(), drawing_id),
            )
            conn.commit()
            st.rerun()
        if cols[1].button("Exclude all pending"):
            conn.execute(
                "UPDATE inventory_items SET status = 'excluded', reviewed_at = ? WHERE drawing_id = ? AND status = 'pending'",
                (datetime.utcnow().isoformat(), drawing_id),
            )
            conn.commit()
            st.rerun()

    elif view == "Summary by floor":
        st.subheader("Summary by floor")
        q = """
        SELECT d.floor_tab_name,
               COUNT(*) as items,
               SUM(CASE WHEN i.status = 'approved' THEN COALESCE(i.amended_count, i.tender_estimate, i.count) ELSE 0 END) as approved_qty,
               SUM(CASE WHEN i.status = 'excluded' THEN 1 ELSE 0 END) as excluded
        FROM inventory_items i
        JOIN drawings d ON i.drawing_id = d.id
        WHERE d.project_id = ?
        GROUP BY d.floor_tab_name
        ORDER BY d.floor_tab_name
        """
        df = pd.read_sql(q, conn, params=(project_id,))
        st.dataframe(df, use_container_width=True)

    elif view == "Summary by category":
        st.subheader("Summary by category (across project)")
        q = """
        SELECT COALESCE(i.category, 'Uncategorised') as category,
               COUNT(*) as items,
               SUM(CASE WHEN i.status = 'approved' THEN COALESCE(i.amended_count, i.tender_estimate, i.count) ELSE 0 END) as approved_qty
        FROM inventory_items i
        JOIN drawings d ON i.drawing_id = d.id
        WHERE d.project_id = ?
        GROUP BY category
        ORDER BY category
        """
        df = pd.read_sql(q, conn, params=(project_id,))
        st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
