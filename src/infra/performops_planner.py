import json

from src.core.llm import LLM
from src.core.output_parser import PlanOutputParser
from src.core.performops.model import PerformOpsAnalysisResult, PerformOpsPlan
from src.core.performops.planner import PerformOpsPlanner
from src.core.user_action_store import UserActionStore
from src.deps.get_llm import get_llm

PLAN_PROMPT = """아래는 성능 이상 원인 분석 결과입니다.

## 분석 결과
{result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

## 사용 가능한 User Action
{user_actions}

위 분석 결과를 바탕으로, 사용 가능한 User Action 목록에서 적절한 액션을 선택하여 조치 계획을 수립하세요.
반드시 사용 가능한 User Action이 있는 조치만 포함하세요. 대응하는 User Action이 없는 조치는 plan에 포함하지 마세요.

아래 JSON 형식으로만 반환하세요.

{{
  "plans": [
    {{
      "plan": "조치 내용",
      "reason": "해당 조치가 필요한 이유",
      "user_action": {{
        "method": "PATCH",
        "path": "/apps/{{project-id}}/{{name}}",
        "summary": "앱 배포 수정"
      }}
    }}
  ]
}}"""


class PerformOpsPlannerImpl(PerformOpsPlanner):

    def __init__(self, llm: LLM = None):
        self._llm = llm or get_llm(template=PLAN_PROMPT)
        self._parser = PlanOutputParser()

    async def plan(
            self,
            analysis_result: PerformOpsAnalysisResult,
    ) -> PerformOpsPlan:
        user_actions = UserActionStore.get()
        user_actions_json = json.dumps(
            [{"method": a.method, "path": a.path, "summary": a.summary} for a in user_actions],
            ensure_ascii=False,
            indent=2,
        )

        response = await self._llm.chat(
            variables=[
                analysis_result.result,
                analysis_result.resource.project_resource,
                analysis_result.resource.app_deployment_resource,
                analysis_result.resource.deployment_status,
                analysis_result.resource.pod_log,
                analysis_result.resource.traffic,
                analysis_result.resource.latency,
                user_actions_json,
            ],
        )

        return self._parser.parse(response)
