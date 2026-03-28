from dataclasses import field
from pydantic.dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


@dataclass
class PerformOpsAction:
    action: str
    state: str
    performops_id: int | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Performops:
    project_id: int
    app_deployment_name: str
    summary: str
    influence: str
    cause: str
    severity: str
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    actions: List[PerformOpsAction] = field(default_factory=list)


@dataclass
class TrackingMetric:
    state: str  # 현재 상태
    change: str  # n분간 변화
    basis: str  # 판단 근거


@dataclass
class PerformOpsAnalysisResource:
    project_resource: TrackingMetric
    app_deployment_resource: TrackingMetric
    deployment_status: TrackingMetric
    pod_log: TrackingMetric
    traffic: TrackingMetric
    latency: TrackingMetric


@dataclass
class PerformOpsAnalysisResult:
    result: str
    resource: PerformOpsAnalysisResource


@dataclass
class UserAction:
    method: str
    path: str
    summary: str


@dataclass
class PlanAction:
    action: str
    reason: str
    user_action: Optional[UserAction] = None


@dataclass
class PerformOpsPlan:
    actions: List[PlanAction]


class PerformOpsSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PerformOpsSummary:
    summary: str
    severity: PerformOpsSeverity


@dataclass
class PerformOpsResult:
    project_id: int
    app_deployment_name: str
    analysis_result: PerformOpsAnalysisResult
    plan: PerformOpsPlan
    summary: PerformOpsSummary

    @property
    def summary_text(self) -> str:
        return self.summary.summary

    @property
    def severity(self) -> PerformOpsSeverity:
        return self.summary.severity
