from datetime import datetime
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

class AuditBase:
    use_tf: Mapped[str] = mapped_column(String(1), default="Y", nullable=False)
    del_tf: Mapped[str] = mapped_column(String(1), default="N", nullable=False)

    reg_adm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reg_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    up_adm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    up_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    del_adm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    del_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)