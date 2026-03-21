from abc import ABC, abstractmethod

from src.core.performops.model import PerformOpsAnalysisResult, PerformOpsPlan


class PerformOpsPlanner(ABC):

    @abstractmethod
    async def plan(
            self,
            analysis_result : PerformOpsAnalysisResult
    ) -> PerformOpsPlan:
        raise NotImplementedError
