"""관리자 refresh token 해시를 저장하는 모델이다."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base


class ManagerRefreshToken(Base, AuditBase):
    __tablename__ = "manager_refresh_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("manager.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_tf: Mapped[str] = mapped_column(String(1), nullable=False, default="N")
    user_agent: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)

    manager = relationship("Manager", back_populates="refresh_tokens")

