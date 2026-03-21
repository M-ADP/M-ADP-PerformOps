
class PerformOps(Base):
    __tablename__ = "performops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project.id"),
        nullable=False
    )

    deployment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("deployment.id"),
        nullable=False
    )

    summary: Mapped[str] = mapped_column(String(255))
    influence: Mapped[str] = mapped_column(String(255))
    cause: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )