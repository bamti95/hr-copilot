from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.audit_base import AuditBase


class AdminMenu(Base, AuditBase):
    __tablename__ = "admin_menu"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("admin_menu.id"), nullable=True)

    menu_name: Mapped[str] = mapped_column(String(100), nullable=False)
    menu_key: Mapped[str] = mapped_column(String(100), nullable=False)
    menu_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)

    parent = relationship("AdminMenu", remote_side=[id])
    group_menus = relationship("AdminGroupMenu", back_populates="menu")