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
        return (
            f"<ProcessedFileLog(filename='{self.source_filename}', "
            f"file_hash='{self.file_hash[:10]}...')>"
        ) 