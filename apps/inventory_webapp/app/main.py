"""FastAPI entrypoint for the inventory review webapp."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origins, db_path
from app.db import migrate
from app.routers import catalogue, drawings, files, health, items, projects, summary


@asynccontextmanager
async def lifespan(_app: FastAPI):
    migrate()
    yield


app = FastAPI(
    title="Riser Inventory Review",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(drawings.router)
app.include_router(items.router)
app.include_router(summary.router)
app.include_router(catalogue.router)
app.include_router(files.router)


@app.get("/")
def root():
    return {
        "service": "riser-inventory-webapp",
        "docs": "/docs",
        "health": "/health",
        "db": str(db_path()),
    }
