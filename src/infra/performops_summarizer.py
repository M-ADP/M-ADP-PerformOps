import json

from src.core.llm import LLM
from src.core.performops.model import (
    PerformOpsAnalysisResult,
    PerformOpsPlan,
    PerformOpsSummary,
    PerfromOpsSeverity,
)
from src.core.performops.summarizer import PerformOpsSummarizer
from src.deps.get_llm import get_llm

SUMMARY_PROMPT = """아래는 성능 이상 분석 결과와 조치 계획입니다.

## 원인 분석
{result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

## 조치 계획
{plans}

위 내용을 바탕으로 전체 요약과 심각도를 아래 JSON 형식으로만 반환하세요.
심각도는 "low", "medium", "high" 중 하나입니다.

{{
  "summary": "전체 상황 요약",
  "severity": "low | medium | high"
}}"""


class PerformOpsSummarizerImpl(PerformOpsSummarizer):

    def __init__(self, llm: LLM = None):
        self._llm = llm or get_llm(template=SUMMARY_PROMPT)

    async def summarize(
            self,
            analysis_result: PerformOpsAnalysisResult,
            plan: PerformOpsPlan,
    ) -> PerformOpsSummary:
        plans_text = "\n".join(
            f"- {p.plan} (이유: {p.reason})" for p in plan.plans
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
                plans_text,
            ],
        )

        parsed = json.loads(response)

        return PerformOpsSummary(
            summary=parsed["summary"],
            severity=PerfromOpsSeverity(parsed["severity"]),
        )
