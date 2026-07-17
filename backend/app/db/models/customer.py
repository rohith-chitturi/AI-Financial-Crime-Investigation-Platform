from sqlalchemy import Column, String, Float, Date, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.models.base import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    country = Column(String, nullable=False, index=True)
    risk_score = Column(Float, default=0.0) # Pre-calculated baseline risk score
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("now()"))

    accounts = relationship("Account", back_populates="customer")
