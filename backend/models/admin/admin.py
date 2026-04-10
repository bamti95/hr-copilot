from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.audit_base import AuditBase


class Admin(Base, AuditBase):
    __tablename__ = "admin"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("admin_group.id"), nullable=False)

    login_id: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    group = relationship("AdminGroup", back_populates="admins")
    access_logs = relationship("AdminAccessLog", back_populates="admin")
    refresh_tokens = relationship("AdminRefreshToken", back_populates="admin")