import asyncio
import json
from typing import List, Optional

from src.core.llm import LLM
from src.core.output_parser import AbstractPlanOutputParser, PlanOutputParser
from src.core.performops.model import (
    AbstractPlan,
    PerformOpsAnalysisResult,
    PerformOpsPlan,
)
from src.core.performops.planner import PerformOpsPlanner
from src.core.user_action_store import UserActionStore
from src.deps.get_llm import get_llm

# ── Common: Tool-select stage ──────────────────────────────────────────────────
TOOL_SELECT_PROMPT = """You are a Kubernetes cluster administrator.
Select the appropriate Resource Manager API to execute the following action.

## Action
- Content: {action}
- Reason: {reason}

## Available Resource Manager APIs
{user_actions}

Select ONE most appropriate API from the list above and create the request body in JSON format.
Keep path variables like {{project-id}}, {{name}} as is.
If no appropriate API exists, return null.

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text.

{{
  "method": "PATCH",
  "path": "/resource/apps/{{project-id}}/{{name}}",
  "body": {{"memory": "1Gi", "cpu": "500m"}}
}}

Or if no matching API:

null"""

# ── Reactive: Immediate symptom mitigation ────────────────────────────────────────────
REACTIVE_PLAN_PROMPT = """Below is the performance issue analysis result.

## Analysis Result
{result}

## Resource Status
- Project Resource: {project_resource}
- App Deployment Resource: {app_deployment_resource}
- Deployment Status: {deployment_status}
- Pod Log: {pod_log}
- Traffic: {traffic}
- Latency: {latency}

You are a Kubernetes cluster administrator. Your role is to **stop the incident immediately**.

Focus on suppressing current symptoms (OOMKill, traffic surge, high latency) right now.
- Increase resources (CPU/Memory limits, replica count) generously.
- Prioritize quick stabilization over precise configuration.
- Symptom removal is the goal, not root cause analysis.

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text.

{{
  "plans": [
    {{
      "action": "Action description",
      "reason": "Why this action is needed"
    }}
  ]
}}"""

REACTIVE_PLAN_REFINEMENT_PROMPT = """Below is the performance issue analysis result.

## Analysis Result
{result}

## Resource Status
- Project Resource: {project_resource}
- App Deployment Resource: {app_deployment_resource}
- Deployment Status: {deployment_status}
- Pod Log: {pod_log}
- Traffic: {traffic}
- Latency: {latency}

You are a Kubernetes cluster administrator. Your role is to **stop the incident immediately**.

Focus on suppressing current symptoms (OOMKill, traffic surge, high latency) right now.
- Increase resources (CPU/Memory limits, replica count) generously.
- Prioritize quick stabilization over precise configuration.
- Symptom removal is the goal, not root cause analysis.

## Previous Plan Issues (Must address)
{feedback}

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text.

{{
  "plans": [
    {{
      "action": "Action description",
      "reason": "Why this action is needed"
    }}
  ]
}}"""

# ── Proactive: Root cause elimination ───────────────────────────────────────────
PROACTIVE_PLAN_PROMPT = """Below is the performance issue analysis result.

## Analysis Result
{result}

## Resource Status
- Project Resource: {project_resource}
- App Deployment Resource: {app_deployment_resource}
- Deployment Status: {deployment_status}
- Pod Log: {pod_log}
- Traffic: {traffic}
- Latency: {latency}

You are a Kubernetes cluster administrator. Your role is to **improve the system structure to prevent recurrence**.

Find and solve root causes (wrong request/limit ratio, missing HPA, untuned resource quotas).
- Prioritize configuration ratio adjustments and automation policies over simple resource increases.
- Target long-term system stability and efficiency.
- Prevention of recurrence is the goal, not immediate symptom suppression.

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text.

{{
  "plans": [
    {{
      "action": "Action description",
      "reason": "Why this action is needed"
    }}
  ]
}}"""

PROACTIVE_PLAN_REFINEMENT_PROMPT = """Below is the performance issue analysis result.

## Analysis Result
{result}

## Resource Status
- Project Resource: {project_resource}
- App Deployment Resource: {app_deployment_resource}
- Deployment Status: {deployment_status}
- Pod Log: {pod_log}
- Traffic: {traffic}
- Latency: {latency}

You are a Kubernetes cluster administrator. Your role is to **improve the system structure to prevent recurrence**.

Find and solve root causes (wrong request/limit ratio, missing HPA, untuned resource quotas).
- Prioritize configuration ratio adjustments and automation policies over simple resource increases.
- Target long-term system stability and efficiency.
- Prevention of recurrence is the goal, not immediate symptom suppression.

## Previous Plan Issues (Must address)
{feedback}

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text.

{{
  "plans": [
    {{
      "action": "Action description",
      "reason": "Why this action is needed"
    }}
  ]
}}"""


class BasePerformOpsPlanner(PerformOpsPlanner):
    """
    두 관점 Planner의 공통 로직.
    서브클래스는 PLAN_PROMPT / REFINEMENT_PROMPT 클래스 변수만 정의한다.
    """

    PLAN_PROMPT: str = ""
    REFINEMENT_PROMPT: str = ""

    def __init__(
        self,
        abstract_llm: Optional[LLM] = None,
        abstract_refinement_llm: Optional[LLM] = None,
        tool_select_llm: Optional[LLM] = None,
    ):
        self._abstract_llm = abstract_llm or get_llm(template=self.PLAN_PROMPT)
        self._abstract_refinement_llm = abstract_refinement_llm or get_llm(
            template=self.REFINEMENT_PROMPT
        )
        self._tool_select_llm = tool_select_llm or get_llm(template=TOOL_SELECT_PROMPT)
        self._abstract_parser = AbstractPlanOutputParser()
        self._plan_parser = PlanOutputParser()

    async def plan(
        self,
        analysis_result: PerformOpsAnalysisResult,
        feedback: Optional[str] = None,
    ) -> PerformOpsPlan:
        user_actions_json = self._build_user_actions_json()
        abstract_plans = await self._generate_abstract_plans(analysis_result, feedback)

        tool_responses = await asyncio.gather(
            *[
                self._tool_select_llm.chat(
                    variables=[p.action, p.reason, user_actions_json]
                )
                for p in abstract_plans
            ]
        )

        return self._plan_parser.parse_with_tools(abstract_plans, tool_responses)

    async def _generate_abstract_plans(
        self,
        analysis_result: PerformOpsAnalysisResult,
        feedback: Optional[str],
    ) -> List[AbstractPlan]:
        base_variables = [
            analysis_result.result,
            analysis_result.resource.project_resource,
            analysis_result.resource.app_deployment_resource,
            analysis_result.resource.deployment_status,
            analysis_result.resource.pod_log,
            analysis_result.resource.traffic,
            analysis_result.resource.latency,
        ]

        if feedback:
            response = await self._abstract_refinement_llm.chat(
                variables=[*base_variables, feedback],
            )
        else:
            response = await self._abstract_llm.chat(variables=base_variables)

        return self._abstract_parser.parse(response)

    @staticmethod
    def _build_user_actions_json() -> str:
        return json.dumps(
            [
                {"method": a.method, "path": a.path, "summary": a.summary}
                for a in UserActionStore.get()
            ],
            ensure_ascii=False,
            indent=2,
        )


class ReactivePlanner(BasePerformOpsPlanner):
    """
    증상 즉시 제거 관점.
    OOMKill, 트래픽 폭증, 높은 지연시간 등 현재 발생 중인 장애 신호를
    빠르게 억제하는 데 집중한다. (스케일아웃, limit 증설 위주)
    """

    PLAN_PROMPT = REACTIVE_PLAN_PROMPT
    REFINEMENT_PROMPT = REACTIVE_PLAN_REFINEMENT_PROMPT


class ProactivePlanner(BasePerformOpsPlanner):
    """
    근본 원인 제거 관점.
    request/limit 비율 재조정, HPA 튜닝 등 구조적 원인을 해결해
    동일 장애가 재발하지 않도록 한다.
    """

    PLAN_PROMPT = PROACTIVE_PLAN_PROMPT
    REFINEMENT_PROMPT = PROACTIVE_PLAN_REFINEMENT_PROMPT
