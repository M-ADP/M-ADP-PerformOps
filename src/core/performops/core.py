from abc import ABC, abstractmethod

from fastapi import Depends

from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.model import PerformOpsSummary, PerformOpsResult
from src.core.performops.planner import PerformOpsPlanner
from src.core.performops.summarizer import PerformOpsSummarizer


class PerformOpsCore:

    def __init__(
            self,
            analysis : PerformOpsAnalysis,
            planner : PerformOpsPlanner,
            summarizer : PerformOpsSummarizer
    ):
        self._analysis = analysis
        self._planner = planner
        self._summarizer = summarizer

    async def start(
            self,
            project_id : int,
            app_deployment_id : int,
    ) -> PerformOpsResult:
        # 원인 분석
        analysis_result = await self._analysis.analyze(
            project_id=project_id,
            app_deployment_id=app_deployment_id,
        )

        # 계획 수립
        plan = await self._planner.plan(analysis_result=analysis_result)

        # 요약 + 심각성 도출
        summary = await self._summarizer.summarize(
            analysis_result=analysis_result,
            plan=plan
        )

        return PerformOpsResult(
            project_id=project_id,
            app_deployment_id=app_deployment_id,
            analysis_result=analysis_result,
            plan=plan,
            summary=summary
        )


