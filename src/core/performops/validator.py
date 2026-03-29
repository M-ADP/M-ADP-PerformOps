from abc import ABC, abstractmethod

from src.core.performops.model import (
    PerformOpsAnalysisResult,
    PerformOpsPlan,
    ValidationResult,
)


class PerformOpsValidator(ABC):
    """
    Self-Refinement 루프의 종료 조건을 결정하는 검증 레이어.

    검증은 2단계로 구성된다:
      1. Rule-based: 빠른 deterministic 게이트 (비용 없음)
      2. LLM-as-Judge: 분석-계획 semantic 일관성 평가 (rule 통과 시에만 실행)

    두 단계 모두 통과해야 ValidationResult.approved = True.
    """

    @abstractmethod
    async def validate(
        self,
        analysis_result: PerformOpsAnalysisResult,
        plan: PerformOpsPlan,
    ) -> ValidationResult:
        raise NotImplementedError
