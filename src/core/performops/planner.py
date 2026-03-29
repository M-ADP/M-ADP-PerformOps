from abc import ABC, abstractmethod
from typing import Optional

from src.core.performops.model import PerformOpsAnalysisResult, PerformOpsPlan


class PerformOpsPlanner(ABC):
    @abstractmethod
    async def plan(
        self,
        analysis_result: PerformOpsAnalysisResult,
        feedback: Optional[str] = None,
    ) -> PerformOpsPlan:
        """
        분석 결과를 바탕으로 조치 계획을 수립한다.

        Args:
            analysis_result: 원인 분석 결과
            feedback: Validator가 거절한 경우 제공하는 개선 요구사항.
                      None이면 최초 계획, 값이 있으면 Self-Refinement 재시도.
        """
        raise NotImplementedError
