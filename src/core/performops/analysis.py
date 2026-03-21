from abc import ABC, abstractmethod

from fastapi import Depends

from src.core.error_tracker import ErrorTracker
from src.core.performops.model import PerformOpsAnalysisResult
from src.deps.get_error_tracker import get_error_tracker


class PerformOpsAnalysis(ABC):

    @abstractmethod
    async def analyze(
            self,
            error_tracker : ErrorTracker = Depends(get_error_tracker),
    ) -> PerformOpsAnalysisResult:
        raise NotImplementedError
