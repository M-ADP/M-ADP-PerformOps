import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)

from src.core.performops.model import (
    PerformOpsAnalysisResult,
    PerformOpsAnalysisResource,
    PerformOpsPlan,
    PerformOpsSummary,
    PerformOpsSeverity,
    PlanSet,
    TrackingMetric,
    UserAction,
)

T = TypeVar("T")


class OutputParser(ABC, Generic[T]):

    @abstractmethod
    def parse(self, response: str) -> T:
        raise NotImplementedError

    def _extract_json(self, response: str) -> dict:
        cleaned = re.sub(r"^```(?:json)?\s*", "", response.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"[OutputParser] JSON parse failed. response={response!r}, error={e}")
            raise


class AnalysisResultOutputParser(OutputParser[PerformOpsAnalysisResult]):

    def parse(self, response: str) -> PerformOpsAnalysisResult:
        parsed = self._extract_json(response)
        return PerformOpsAnalysisResult(
            result=parsed["result"],
            resource=PerformOpsAnalysisResource(
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
        parsed = self._extract_json(response)
        plans = []
        for p in parsed["plans"]:
            raw_action = p.get("user_action")
            user_action = UserAction(**raw_action) if raw_action else None
            plans.append(PlanSet(
                plan=p["plan"],
                reason=p["reason"],
                user_action=user_action,
            ))
        return PerformOpsPlan(plans=plans)


class SummaryOutputParser(OutputParser[PerformOpsSummary]):

    def parse(self, response: str) -> PerformOpsSummary:
        parsed = self._extract_json(response)
        return PerformOpsSummary(
            summary=parsed["summary"],
            severity=PerformOpsSeverity(parsed["severity"]),
        )
