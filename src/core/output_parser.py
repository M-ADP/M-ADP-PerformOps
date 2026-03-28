import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

logger = logging.getLogger(__name__)

from src.core.performops.model import (
    AbstractPlan,
    PerformOpsAnalysisResult,
    PerformOpsAnalysisResource,
    PerformOpsPlan,
    PerformOpsSummary,
    PerformOpsSeverity,
    PlanAction,
    TrackingMetric,
    UserAction,
)

T = TypeVar("T")


class OutputParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, response: str) -> T:
        raise NotImplementedError

    def _extract_json(self, response: str):
        cleaned = re.sub(r"^```(?:json)?\s*", "", response.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(
                f"[OutputParser] JSON parse failed. response={response!r}, error={e}"
            )
            raise


class AnalysisResultOutputParser(OutputParser[PerformOpsAnalysisResult]):
    def parse(self, response: str) -> PerformOpsAnalysisResult:
        parsed = self._extract_json(response)
        return PerformOpsAnalysisResult(
            result=parsed["result"],
            resource=PerformOpsAnalysisResource(
                project_resource=TrackingMetric(**parsed["project_resource"]),
                app_deployment_resource=TrackingMetric(
                    **parsed["app_deployment_resource"]
                ),
                deployment_status=TrackingMetric(**parsed["deployment_status"]),
                pod_log=TrackingMetric(**parsed["pod_log"]),
                traffic=TrackingMetric(**parsed["traffic"]),
                latency=TrackingMetric(**parsed["latency"]),
            ),
        )


class AbstractPlanOutputParser(OutputParser[List[AbstractPlan]]):
    """1단계: 자연어 조치 목록 파싱"""

    def parse(self, response: str) -> List[AbstractPlan]:
        parsed = self._extract_json(response)
        return [
            AbstractPlan(action=p["action"], reason=p["reason"])
            for p in parsed["plans"]
        ]


class PlanOutputParser(OutputParser[PerformOpsPlan]):
    """2단계: AbstractPlan 목록 + tool_select 응답들을 합쳐 최종 PerformOpsPlan 생성"""

    def parse(self, response: str) -> PerformOpsPlan:
        # 단독 호출용 (하위 호환)
        parsed = self._extract_json(response)
        actions = []
        for a in parsed["actions"]:
            raw_ua = a.get("user_action")
            user_action = UserAction(**raw_ua) if raw_ua else None
            actions.append(
                PlanAction(
                    action=a["action"],
                    reason=a["reason"],
                    http_method=a.get("http_method", ""),
                    http_path=a.get("http_path", ""),
                    http_body=a.get("http_body", ""),
                    user_action=user_action,
                )
            )
        return PerformOpsPlan(actions=actions)

    def parse_with_tools(
        self,
        abstract_plans: List[AbstractPlan],
        tool_responses: List[str],
    ) -> PerformOpsPlan:
        """1단계 추상 플랜 + 2단계 tool select 응답을 결합"""
        actions = []
        for plan, tool_resp in zip(abstract_plans, tool_responses):
            tool = self._parse_tool_response(tool_resp)
            if tool is None:
                # 대응 API 없음 → action만 기록, http 정보 비움
                actions.append(
                    PlanAction(
                        action=plan.action,
                        reason=plan.reason,
                        http_method="",
                        http_path="",
                        http_body="",
                    )
                )
            else:
                actions.append(
                    PlanAction(
                        action=plan.action,
                        reason=plan.reason,
                        http_method=tool["method"],
                        http_path=tool["path"],
                        http_body=json.dumps(
                            tool.get("body") or {}, ensure_ascii=False
                        ),
                        user_action=UserAction(
                            method=tool["method"],
                            path=tool["path"],
                            summary=plan.action,
                        ),
                    )
                )
        return PerformOpsPlan(actions=actions)

    def _parse_tool_response(self, response: str) -> dict | None:
        cleaned = re.sub(r"^```(?:json)?\s*", "", response.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        if cleaned.lower() == "null":
            return None
        try:
            parsed = json.loads(cleaned)
            return parsed if parsed else None
        except json.JSONDecodeError:
            logger.warning(
                f"[PlanOutputParser] tool select 파싱 실패, 건너뜀. response={response!r}"
            )
            return None


class SummaryOutputParser(OutputParser[PerformOpsSummary]):
    def parse(self, response: str) -> PerformOpsSummary:
        parsed = self._extract_json(response)
        return PerformOpsSummary(
            summary=parsed["summary"],
            severity=PerformOpsSeverity(parsed["severity"]),
        )
