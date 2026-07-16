"""API v1 router assembly."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    adverse_events,
    agents,
    budgets,
    health,
    ip,
    queries,
    reference,
    regulatory,
    reports,
    sites,
    studies,
    subjects,
    visits,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(reference.router)
api_router.include_router(studies.router)
api_router.include_router(sites.router)
api_router.include_router(subjects.router)
api_router.include_router(visits.router)
api_router.include_router(adverse_events.router)
api_router.include_router(ip.router)
api_router.include_router(regulatory.router)
api_router.include_router(queries.router)
api_router.include_router(budgets.router)
api_router.include_router(reports.router)
api_router.include_router(agents.router)
api_router.include_router(webhooks.router)
