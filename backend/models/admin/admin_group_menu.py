from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.audit_base import AuditBase


class AdminGroupMenu(Base, AuditBase):
    __tablename__ = "admin_group_menu"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("admin_group.id"), nullable=False)
    menu_id: Mapped[int] = mapped_column(ForeignKey("admin_menu.id"), nullable=False)

    read_tf: Mapped[str] = mapped_column(String(1), nullable=False, default="Y")
    write_tf: Mapped[str] = mapped_column(String(1), nullable=False, default="N")
    delete_tf: Mapped[str] = mapped_column(String(1), nullable=False, default="N")

    group = relationship("AdminGroup", back_populates="group_menus")
    menu = relationship("AdminMenu", back_populates="group_menus")