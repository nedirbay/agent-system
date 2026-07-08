"""Import every ORM model so it registers on Base.metadata.

Imported by the app factory and Alembic so migrations/create_all see
all tables. Side-effect-only module.
"""
from app.modules.auth.infrastructure.models import UserModel  # noqa: F401
from app.modules.documents.infrastructure.models import DocumentModel  # noqa: F401
from app.modules.knowledge.infrastructure.models import KnowledgeItemModel  # noqa: F401
from app.modules.knowledge.infrastructure.chunk_model import DocumentChunkModel  # noqa: F401
from app.modules.qa.infrastructure.models import QaConversationModel  # noqa: F401
from app.modules.analysis.infrastructure.models import AnalysisJobModel  # noqa: F401
from app.modules.reports.infrastructure.models import ReportModel  # noqa: F401
from app.modules.agents.infrastructure.models import AgentModel  # noqa: F401
from app.modules.workflows.infrastructure.models import WorkflowModel  # noqa: F401
from app.modules.workflows.infrastructure.instance_models import (  # noqa: F401
    WorkflowInstanceModel,
    WorkflowStepModel,
)
from app.modules.memory.infrastructure.models import (  # noqa: F401
    MemoryItemModel,
    MemoryReferenceModel,
)
from app.modules.notifications.infrastructure.models import NotificationModel  # noqa: F401
from app.modules.audit.infrastructure.models import AuditLogModel  # noqa: F401
from app.modules.execution.infrastructure.models import ExecutionRunModel  # noqa: F401
from app.modules.events.infrastructure.models import SystemEventModel  # noqa: F401
from app.modules.connectors.infrastructure.models import ConnectorConnectionModel  # noqa: F401
