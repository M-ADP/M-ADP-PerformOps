from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base_entity import Base


class PerformOps(Base):
    __tablename__ = "performops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    app_deployment_name: Mapped[str] = mapped_column(String, nullable=False)

    summary: Mapped[str] = mapped_column(Text)
    influence: Mapped[str] = mapped_column(Text)
    cause: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # relationship
    actions: Mapped[list["PerformOpsAction"]] = relationship(
        "PerformOpsAction",
        back_populates="performops",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PerformOpsAction(Base):
    __tablename__ = "performops_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    performops_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("performops.id"), nullable=False
    )

    action: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # relationship
    performops: Mapped["PerformOps"] = relationship(
        "PerformOps", back_populates="actions"
    )
