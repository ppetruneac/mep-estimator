from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import data_dir, resolve_pdf_path
from app.db import connect
from app.services import resolve_drawing

router = APIRouter(prefix="/api", tags=["files"])


def _overlay_candidates(drawing_number: str, source_pdf: str | None) -> list[Path]:
    cands: list[Path] = []
    dd = data_dir()
    for folder in (
        dd / "exports" / "overlays",
        dd / "exports" / "HubbyPremierInnLondon" / "overlays",
        Path("evals/evidence/gr2/overlays"),
        Path("out/overlays"),
    ):
        cands.append(folder / f"{drawing_number}.pdf")
    if source_pdf:
        p = Path(source_pdf)
        cands.append(p.with_name(p.stem + "-overlay.pdf"))
    return cands


def _pdf_response(d) -> FileResponse:
    path = resolve_pdf_path(d["source_pdf"])
    if not path or not path.exists():
        raise HTTPException(404, f"PDF not found: {d['source_pdf']}")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{d['drawing_number']}.pdf",
        content_disposition_type="inline",
        headers={"Cache-Control": "private, max-age=60"},
    )


def _overlay_response(d) -> FileResponse:
    for cand in _overlay_candidates(d["drawing_number"], d["source_pdf"]):
        if cand.exists():
            return FileResponse(
                cand,
                media_type="application/pdf",
                filename=f"{d['drawing_number']}-overlay.pdf",
                content_disposition_type="inline",
                headers={"Cache-Control": "private, max-age=60"},
            )
    raise HTTPException(404, "overlay not found")


@router.get("/projects/{project_uuid}/drawings/{drawing_key}/pdf")
def get_pdf_by_key(project_uuid: str, drawing_key: str):
    conn = connect(readonly=True)
    try:
        d = resolve_drawing(conn, project_uuid, drawing_key)
        if not d:
            raise HTTPException(404, "drawing not found")
        return _pdf_response(d)
    finally:
        conn.close()


@router.get("/projects/{project_uuid}/drawings/{drawing_key}/overlay")
def get_overlay_by_key(project_uuid: str, drawing_key: str):
    conn = connect(readonly=True)
    try:
        d = resolve_drawing(conn, project_uuid, drawing_key)
        if not d:
            raise HTTPException(404, "drawing not found")
        return _overlay_response(d)
    finally:
        conn.close()


@router.get("/drawings/{drawing_id}/pdf")
def get_pdf(drawing_id: int):
    conn = connect(readonly=True)
    try:
        d = conn.execute(
            "SELECT drawing_number, source_pdf FROM documents WHERE id = ?",
            (drawing_id,),
        ).fetchone()
        if not d:
            raise HTTPException(404, "drawing not found")
        return _pdf_response(d)
    finally:
        conn.close()


@router.get("/drawings/{drawing_id}/overlay")
def get_overlay(drawing_id: int):
    conn = connect(readonly=True)
    try:
        d = conn.execute(
            "SELECT drawing_number, source_pdf FROM documents WHERE id = ?",
            (drawing_id,),
        ).fetchone()
        if not d:
            raise HTTPException(404, "drawing not found")
        return _overlay_response(d)
    finally:
        conn.close()
