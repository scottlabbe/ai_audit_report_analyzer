from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from database import Base

class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    version = Column(Integer, default=1)
    content = Column(JSON, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'file_name': self.file_name,
            'upload_date': self.upload_date.isoformat(),
            'version': self.version,
            'content': self.content
        }
