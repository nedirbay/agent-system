"""Aggregate API router — mounts every module under the v1 prefix."""
from fastapi import APIRouter

from app.modules.auth.presentation.router import router as auth_router
from app.modules.documents.presentation.router import router as documents_router
from app.modules.knowledge.presentation.router import router as knowledge_router
from app.modules.qa.presentation.router import router as qa_router
from app.modules.analysis.presentation.router import router as analysis_router
from app.modules.reports.presentation.router import router as reports_router
from app.modules.agents.presentation.router import router as agents_router
from app.modules.workflows.presentation.router import router as workflows_router
from app.modules.memory.presentation.router import router as memory_router
from app.modules.notifications.presentation.router import router as notifications_router
from app.modules.audit.presentation.router import router as audit_router
from app.modules.execution.presentation.router import router as execution_router
from app.modules.events.presentation.router import router as events_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(knowledge_router)
api_router.include_router(qa_router)
api_router.include_router(analysis_router)
api_router.include_router(reports_router)
api_router.include_router(agents_router)
api_router.include_router(workflows_router)
api_router.include_router(memory_router)
api_router.include_router(notifications_router)
api_router.include_router(audit_router)
api_router.include_router(execution_router)
api_router.include_router(events_router)
