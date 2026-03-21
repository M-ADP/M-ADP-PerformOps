import json
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.core.performops.model import (
    PerformOpsAnalysisResult,
    PerformOpsanalysisResource,
    PerformOpsPlan,
    PerformOpsSummary,
    PerfromOpsSeverity,
    PlanSet,
    TrackingMetric,
)

T = TypeVar("T")


class OutputParser(ABC, Generic[T]):

    @abstractmethod
    def parse(self, response: str) -> T:
        raise NotImplementedError


class AnalysisResultOutputParser(OutputParser[PerformOpsAnalysisResult]):

    def parse(self, response: str) -> PerformOpsAnalysisResult:
        parsed = json.loads(response)
        return PerformOpsAnalysisResult(
            result=parsed["result"],
            resource=PerformOpsanalysisResource(
                project_resource=TrackingMetric(**parsed["project_resource"]),
                app_deployment_resource=TrackingMetric(**parsed["app_deployment_resource"]),
                deployment_status=TrackingMetric(**parsed["deployment_status"]),
                pod_log=TrackingMetric(**parsed["pod_log"]),
                traffic=TrackingMetric(**parsed["traffic"]),
                latency=TrackingMetric(**parsed["latency"]),
            ),
        )


class PlanOutputParser(OutputParser[PerformOpsPlan]):

    def parse(self, response: str) -> PerformOpsPlan:
        parsed = json.loads(response)
        return PerformOpsPlan(
            plans=[PlanSet(**p) for p in parsed["plans"]],
        )


class SummaryOutputParser(OutputParser[PerformOpsSummary]):

    def parse(self, response: str) -> PerformOpsSummary:
        parsed = json.loads(response)
        return PerformOpsSummary(
            summary=parsed["summary"],
            severity=PerfromOpsSeverity(parsed["severity"]),
        )
