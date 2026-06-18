"""SQLAlchemy models — import all so Alembic autogenerate sees them."""
from app.models.admin_user import AdminUser
from app.models.audio_recording import AudioRecording
from app.models.audit_log import AuditLog
from app.models.booking import Booking
from app.models.call import Call
from app.models.callback_task import CallbackTask
from app.models.customer import Customer
from app.models.knowledge import KnowledgeChunk
from app.models.knowledge_item import KnowledgeItem
from app.models.telephony_call import TelephonyCall
from app.models.telephony_stream import TelephonyStream
from app.models.transcript import Transcript

__all__ = [
    "AdminUser",
    "AudioRecording",
    "AuditLog",
    "Booking",
    "Call",
    "CallbackTask",
    "Customer",
    "KnowledgeChunk",
    "KnowledgeItem",
    "TelephonyCall",
    "TelephonyStream",
    "Transcript",
]
