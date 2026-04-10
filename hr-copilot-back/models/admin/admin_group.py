from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.audit_base import AuditBase


class AdminGroup(Base, AuditBase):
    __tablename__ = "admin_group"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(100), nullable=False)
    group_desc: Mapped[str | None] = mapped_column(String(500), nullable=True)

    admins = relationship("Admin", back_populates="group")
    group_menus = relationship("AdminGroupMenu", back_populates="group")