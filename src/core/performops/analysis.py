from abc import ABC, abstractmethod

from src.core.analyzer.metrics import MetricsAnalyzer
from src.core.analyzer.workload_state import WorkLoadStateAnalyzer
from src.core.performops.model import PerformOpsAnalysisResult


class PerformOpsAnalysis(ABC):
    def __init__(
        self,
        metrics_analyzer: MetricsAnalyzer,
        workload_state_analyzer: WorkLoadStateAnalyzer,
    ):
        self._metrics_analyzer = metrics_analyzer
        self._workload_state_analyzer = workload_state_analyzer

    @abstractmethod
    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> PerformOpsAnalysisResult:
        raise NotImplementedError
