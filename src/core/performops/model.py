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
    http_method: str | None = None
    http_path: str | None = None
    http_body: str | None = None
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
class InfrastructureAgentResult:
    project_resource: TrackingMetric
    app_deployment_resource: TrackingMetric
    analysis: str


@dataclass
class ApplicationAgentResult:
    deployment_status: TrackingMetric
    pod_log: TrackingMetric
    analysis: str


@dataclass
class TrafficAgentResult:
    traffic: TrackingMetric
    latency: TrackingMetric
    analysis: str


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
class AbstractPlan:
    """1단계: 자연어 조치 목록"""

    action: str  # 조치 내용
    reason: str  # 조치가 필요한 이유


@dataclass
class PlanAction:
    """2단계: 실행 가능한 API 정보까지 포함된 최종 액션"""

    action: str
    reason: str
    http_method: str
    http_path: str
    http_body: str
    user_action: Optional[UserAction] = None


@dataclass
class PerformOpsPlan:
    actions: List[PlanAction]


class ActionState(str, Enum):
    PENDING = "pending"  # 실행 안됨
    FAILED = "failed"  # 실패함
    EXECUTED = "executed"  # 실행됨


class PerformOpsSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PlannerType(str, Enum):
    REACTIVE = "reactive"
    PROACTIVE = "proactive"


@dataclass
class JudgeResult:
    """Judge가 두 plan 중 하나를 선택한 결과"""

    selected: PlannerType  # 선택된 planner 관점
    reason: str  # 선택 이유


@dataclass
class RuleCheckResult:
    """Rule-based 검증 개별 항목 결과"""

    name: str  # 검증 항목명
    passed: bool  # 통과 여부
    score: float  # 0.0 ~ 1.0
    detail: str  # 상세 설명


@dataclass
class ValidationResult:
    """Validator 최종 판정"""

    approved: bool  # 최종 통과 여부
    feedback: str  # 재계획 시 프롬프트에 주입할 피드백
    rule_results: List[RuleCheckResult]  # Rule-based 개별 결과
    llm_approved: Optional[bool] = None  # LLM-as-Judge 판정 (None = rule 단계에서 차단)


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
