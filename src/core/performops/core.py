from abc import ABC, abstractmethod

from fastapi import Depends

from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.planner import PerformOpsPlanner


class PerformOpsCore(ABC):

    def __init__(
            self,
            analysis : PerformOpsAnalysis = Depends(get_performops_analysis),
            planner : PerformOpsPlanner = Depends(get_performops_planner),
    ):
        self.analysis = analysis
        self.planner = planner

    @abstractmethod
    async def start(
            self,
            project_id : int,
            app_deployment_name : str,
    ):
        raise NotImplementedError
