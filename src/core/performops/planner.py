from abc import ABC, abstractmethod

from src.core.performops.model import PerformOpsAnalysisResult


class PerformOpsPlanner(ABC):

    @abstractmethod
    async def plan(self, analysis_result : PerformOpsAnalysisResult):
        raise NotImplementedError
