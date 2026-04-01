from abc import ABC, abstractmethod

from src.core.performops.model import PerformOpsAnalysisResult


class PerformOpsAnalysis(ABC):
    @abstractmethod
    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> PerformOpsAnalysisResult:
        raise NotImplementedError
