from sqlalchemy import (
    Column, Integer, String, DateTime, func, UniqueConstraint
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ProcessedFileLog(Base):
    """
    SQLAlchemy model to log files that have been processed.
    This provides a persistent store for our deduplication gateway.
    """
    __tablename__ = 'processed_file_logs'

    id = Column(Integer, primary_key=True)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    content_hash = Column(String, nullable=False, index=True)
    source_filename = Column(String, nullable=False)
    processed_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('file_hash', name='uq_file_hash'),
        UniqueConstraint('content_hash', name='uq_content_hash'),
    )

    def __repr__(self):
        # ✅ FIXED: Crash-proof __repr__ method - never fails on UTF-8 issues
        try:
            # Safe filename conversion
            safe_filename = str(self.source_filename or "Unknown")
            safe_filename = safe_filename.encode('utf-8', errors='replace').decode('utf-8')
            
            # Safe hash conversion
            safe_hash = str(self.file_hash or "None")[:10]
            
            return f"<ProcessedFileLog(filename='{safe_filename}', file_hash='{safe_hash}...')>"
        except Exception:
            # Ultimate fallback - never fails
            return f"<ProcessedFileLog(id={getattr(self, 'id', 'Unknown')})>" 