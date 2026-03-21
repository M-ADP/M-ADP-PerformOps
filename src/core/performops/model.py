from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Performops:
    project_id: int
    deployment_id: int
    summary: str
    influence: str
    cause: str
    severity: str
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PerformOpsAnalysisResult:
    ...

@dataclass
class PerformOpsPlan:
    ...

@dataclass
class PerformOpsSummary:
    ...

@dataclass
class PerformOpsResult:
    project_id: int
    app_deployment_id: int
    analysis_result: PerformOpsAnalysisResult
    plan: PerformOpsPlan
    summary: PerformOpsSummary

