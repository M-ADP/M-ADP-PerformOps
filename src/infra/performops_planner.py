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

# ── 공통: 2단계 Tool-select ──────────────────────────────────────────────────
TOOL_SELECT_PROMPT = """당신은 Kubernetes 클러스터 관리자입니다.
아래 조치를 실행하기 위해 사용할 Resource Manager API와 요청 body를 결정하세요.

## 조치
- 내용: {action}
- 이유: {reason}

## 사용 가능한 Resource Manager API
{user_actions}

위 API 중 이 조치를 실행하는 데 가장 적합한 API 하나를 선택하고,
실제 호출에 필요한 request body를 JSON으로 작성하세요.
path의 {{project-id}}, {{name}} 등 경로 변수는 그대로 두세요.
대응하는 API가 없으면 null을 반환하세요.

아래 JSON 형식으로만 반환하세요.

{{
  "method": "PATCH",
  "path": "/resource/apps/{{project-id}}/{{name}}",
  "body": {{"memory": "1Gi", "cpu": "500m"}}
}}

또는 대응 API 없음:

null"""

# ── Reactive: 증상 즉시 제거 관점 ────────────────────────────────────────────
REACTIVE_PLAN_PROMPT = """아래는 성능 이상 원인 분석 결과입니다.

## 분석 결과
{result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

당신은 Kubernetes 클러스터 관리자입니다. 당신의 역할은 **지금 당장 장애를 멈추는 것**입니다.

현재 발생 중인 증상(OOMKill, 트래픽 폭증, 높은 지연시간 등)을 즉시 억제하는 데 집중하세요.
- 리소스(CPU/Memory limit, replica 수)를 여유 있게 늘리는 방향으로 판단하세요.
- 설정의 정교함보다 빠른 안정화를 우선합니다.
- 근본 원인 분석보다 증상 제거가 목표입니다.

아래 JSON 형식으로만 반환하세요.

{{
  "plans": [
    {{
      "action": "조치 내용",
      "reason": "해당 조치가 필요한 이유"
    }}
  ]
}}"""

REACTIVE_PLAN_REFINEMENT_PROMPT = """아래는 성능 이상 원인 분석 결과입니다.

## 분석 결과
{result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

당신은 Kubernetes 클러스터 관리자입니다. 당신의 역할은 **지금 당장 장애를 멈추는 것**입니다.

현재 발생 중인 증상(OOMKill, 트래픽 폭증, 높은 지연시간 등)을 즉시 억제하는 데 집중하세요.
- 리소스(CPU/Memory limit, replica 수)를 여유 있게 늘리는 방향으로 판단하세요.
- 설정의 정교함보다 빠른 안정화를 우선합니다.
- 근본 원인 분석보다 증상 제거가 목표입니다.

## 이전 계획의 문제점 (반드시 반영할 것)
{feedback}

아래 JSON 형식으로만 반환하세요.

{{
  "plans": [
    {{
      "action": "조치 내용",
      "reason": "해당 조치가 필요한 이유"
    }}
  ]
}}"""

# ── Proactive: 근본 원인 제거 관점 ───────────────────────────────────────────
PROACTIVE_PLAN_PROMPT = """아래는 성능 이상 원인 분석 결과입니다.

## 분석 결과
{result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

당신은 Kubernetes 클러스터 관리자입니다. 당신의 역할은 **같은 문제가 반복되지 않도록 구조를 개선하는 것**입니다.

현재 증상의 근본 원인(잘못된 request/limit 비율, HPA 설정 부재, 리소스 쿼터 미조정 등)을 찾아 해결하세요.
- 단순 리소스 증설보다 설정 비율 재조정, 자동화 정책 도입을 우선하세요.
- 장기적인 시스템 안정성과 효율성을 목표로 합니다.
- 즉각적인 증상 억제보다 재발 방지가 목표입니다.

아래 JSON 형식으로만 반환하세요.

{{
  "plans": [
    {{
      "action": "조치 내용",
      "reason": "해당 조치가 필요한 이유"
    }}
  ]
}}"""

PROACTIVE_PLAN_REFINEMENT_PROMPT = """아래는 성능 이상 원인 분석 결과입니다.

## 분석 결과
{result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

당신은 Kubernetes 클러스터 관리자입니다. 당신의 역할은 **같은 문제가 반복되지 않도록 구조를 개선하는 것**입니다.

현재 증상의 근본 원인(잘못된 request/limit 비율, HPA 설정 부재, 리소스 쿼터 미조정 등)을 찾아 해결하세요.
- 단순 리소스 증설보다 설정 비율 재조정, 자동화 정책 도입을 우선하세요.
- 장기적인 시스템 안정성과 효율성을 목표로 합니다.
- 즉각적인 증상 억제보다 재발 방지가 목표입니다.

## 이전 계획의 문제점 (반드시 반영할 것)
{feedback}

아래 JSON 형식으로만 반환하세요.

{{
  "plans": [
    {{
      "action": "조치 내용",
      "reason": "해당 조치가 필요한 이유"
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
