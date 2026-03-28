import json
from typing import List

from typing import Optional

from src.core.llm import LLM
from src.core.output_parser import AbstractPlanOutputParser, PlanOutputParser
from src.core.performops.model import (
    AbstractPlan,
    PerformOpsAnalysisResult,
    PerformOpsPlan,
    UserAction,
)
from src.core.performops.planner import PerformOpsPlanner
from src.core.user_action_store import UserActionStore
from src.deps.get_llm import get_llm

# ── 1단계: 분석 결과 → 자연어 조치 목록 ──────────────────────────────────────
ABSTRACT_PLAN_PROMPT = """아래는 성능 이상 원인 분석 결과입니다.

## 분석 결과
{result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

당신은 Kubernetes 클러스터 관리자입니다.
위 분석 결과를 바탕으로 시스템 안정화를 위해 필요한 조치 목록을 수립하세요.
각 조치는 구체적이고 실행 가능한 내용이어야 합니다 (예: "app-backend의 메모리 limit을 512Mi에서 1Gi로 증설").

아래 JSON 형식으로만 반환하세요.

{{
  "plans": [
    {{
      "action": "조치 내용",
      "reason": "해당 조치가 필요한 이유"
    }}
  ]
}}"""

# ── 2단계: 각 조치 → Resource Manager API + 실행 파라미터 결정 ────────────────
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


class PerformOpsPlannerImpl(PerformOpsPlanner):
    def __init__(
        self, abstract_llm: Optional[LLM] = None, tool_select_llm: Optional[LLM] = None
    ):
        self._abstract_llm = abstract_llm or get_llm(template=ABSTRACT_PLAN_PROMPT)
        self._tool_select_llm = tool_select_llm or get_llm(template=TOOL_SELECT_PROMPT)
        self._abstract_parser = AbstractPlanOutputParser()
        self._plan_parser = PlanOutputParser()

    async def plan(
        self,
        analysis_result: PerformOpsAnalysisResult,
    ) -> PerformOpsPlan:
        user_actions = UserActionStore.get()
        user_actions_json = json.dumps(
            [
                {"method": a.method, "path": a.path, "summary": a.summary}
                for a in user_actions
            ],
            ensure_ascii=False,
            indent=2,
        )

        # ── 1단계: 자연어 조치 목록 생성 ──
        abstract_response = await self._abstract_llm.chat(
            variables=[
                analysis_result.result,
                analysis_result.resource.project_resource,
                analysis_result.resource.app_deployment_resource,
                analysis_result.resource.deployment_status,
                analysis_result.resource.pod_log,
                analysis_result.resource.traffic,
                analysis_result.resource.latency,
            ],
        )
        abstract_plans: List[AbstractPlan] = self._abstract_parser.parse(
            abstract_response
        )

        # ── 2단계: 각 조치에 대해 API + 파라미터 결정 (병렬) ──
        import asyncio

        tool_responses = await asyncio.gather(
            *[
                self._tool_select_llm.chat(
                    variables=[p.action, p.reason, user_actions_json]
                )
                for p in abstract_plans
            ]
        )

        return self._plan_parser.parse_with_tools(abstract_plans, tool_responses)
