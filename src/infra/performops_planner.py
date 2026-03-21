import json

from src.core.llm import LLM
from src.core.performops.model import PerformOpsAnalysisResult, PerformOpsPlan, PlanSet
from src.core.performops.planner import PerformOpsPlanner
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

위 분석 결과를 바탕으로 조치 계획을 아래 JSON 형식으로만 반환하세요.

{{
  "plans": [
    {{"plan": "조치 내용", "reason": "해당 조치가 필요한 이유"}},
    ...
  ]
}}"""


class PerformOpsPlannerImpl(PerformOpsPlanner):

    def __init__(self, llm: LLM = None):
        self._llm = llm or get_llm(template=PLAN_PROMPT)

    async def plan(
            self,
            analysis_result: PerformOpsAnalysisResult,
    ) -> PerformOpsPlan:
        response = await self._llm.chat(
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
        parsed = json.loads(response)

        return PerformOpsPlan(
            plans=[PlanSet(**p) for p in parsed["plans"]],
        )
