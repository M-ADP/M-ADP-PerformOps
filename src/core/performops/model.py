from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


@dataclass
class Performops:
    project_id: int
    app_deployment_name: int
    summary: str
    influence: str
    cause: str
    severity: str
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TrackingMetric:
      state: str    # 현재 상태
      change: str   # n분간 변화
      basis: str    # 판단 근거

@dataclass
class PerformOpsAnalysisResult:
    project_resource: TrackingMetric
    project_resource: TrackingMetric
    app_deployment_resource: TrackingMetric
    deployment_status: TrackingMetric
    pod_log: TrackingMetric
    traffic: TrackingMetric

@dataclass
class PlanSet:
    plan : str
    reason : str

@dataclass
class PerformOpsPlan:
    plans : List[PlanSet]

@dataclass
class PerfromOpsSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class PerformOpsSummary:
    summary : str
    severity : PerfromOpsSeverity

@dataclass
class PerformOpsResult:
    project_id: int
    app_deployment_name: int
    analysis_result: PerformOpsAnalysisResult
    plan: PerformOpsPlan
    summary: PerformOpsSummary

    @property
    def summary_text(self) -> str:
        return self.summary.summary

    @property
    def severity(self) -> PerfromOpsSeverity:
        return self.summary.severity

