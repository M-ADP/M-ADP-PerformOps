from abc import ABC, abstractmethod

from src.core.performops.model import (
    JudgeResult,
    PerformOpsAnalysisResult,
    PerformOpsPlan,
)


class PerformOpsJudge(ABC):
    """
    Reactive / Proactive 두 plan 후보 중 현재 상황에 더 적합한 것을 선택한다.
    상대 비교 평가이므로 절대 판단보다 정확하다.
    """

    @abstractmethod
    async def judge(
        self,
        analysis_result: PerformOpsAnalysisResult,
        reactive_plan: PerformOpsPlan,
        proactive_plan: PerformOpsPlan,
    ) -> JudgeResult:
        raise NotImplementedError
