from abc import ABC, abstractmethod
from src.core.performops.model import PerformOpsAnalysisResult, PerformOpsPlan, PerformOpsSummary


class PerformOpsSummarizer(ABC):

    @abstractmethod
    async def summarize(
            self,
            analysis_result : PerformOpsAnalysisResult,
            plan : PerformOpsPlan,
    ) -> PerformOpsSummary:
        raise NotImplementedError