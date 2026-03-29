import logging
from typing import Optional

from src.core.llm import LLM
from src.core.output_parser import JudgeOutputParser
from src.core.performops.judge import PerformOpsJudge
from src.core.performops.model import (
    JudgeResult,
    PerformOpsAnalysisResult,
    PerformOpsPlan,
    PlannerType,
)
from src.deps.get_llm import get_llm

logger = logging.getLogger(__name__)

JUDGE_PROMPT = """당신은 Kubernetes 성능 운영 전문가입니다.
동일한 장애 상황에 대해 두 가지 관점의 조치 계획이 수립되었습니다.
현재 상황을 분석하여 더 적합한 계획을 선택하세요.

## 원인 분석 결과
{analysis_result}

## 리소스 상태
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

---

## Plan A — Reactive (즉각 증상 제거)
{reactive_plan}

## Plan B — Proactive (근본 원인 구조 개선)
{proactive_plan}

---

## 선택 기준
- **Reactive를 선택해야 하는 경우**: 현재 장애가 진행 중이거나 서비스 중단 위험이 높을 때.
  빠른 안정화가 장기 최적화보다 우선한다.
- **Proactive를 선택해야 하는 경우**: 근본 원인이 명확하고 반복 패턴이 보일 때.
  즉각 조치보다 재발 방지가 더 효과적인 상황이다.

두 계획 중 현재 상황에 더 적합한 것을 선택하고, 아래 JSON 형식으로만 반환하세요.

{{
  "selected": "reactive",
  "reason": "선택 이유를 한두 문장으로 설명"
}}

또는

{{
  "selected": "proactive",
  "reason": "선택 이유를 한두 문장으로 설명"
}}"""


def _format_plan(plan: PerformOpsPlan) -> str:
    lines = []
    for i, action in enumerate(plan.actions, 1):
        api_info = ""
        if action.http_method and action.http_path:
            api_info = f" → {action.http_method} {action.http_path}"
        lines.append(f"{i}. {action.action} (이유: {action.reason}){api_info}")
    return "\n".join(lines) if lines else "(계획 없음)"


class PerformOpsJudgeImpl(PerformOpsJudge):
    def __init__(self, llm: Optional[LLM] = None):
        self._llm = llm or get_llm(template=JUDGE_PROMPT)
        self._parser = JudgeOutputParser()

    async def judge(
        self,
        analysis_result: PerformOpsAnalysisResult,
        reactive_plan: PerformOpsPlan,
        proactive_plan: PerformOpsPlan,
    ) -> JudgeResult:
        resource = analysis_result.resource

        try:
            response = await self._llm.chat(
                variables=[
                    analysis_result.result,
                    resource.project_resource,
                    resource.app_deployment_resource,
                    resource.deployment_status,
                    resource.pod_log,
                    resource.traffic,
                    resource.latency,
                    _format_plan(reactive_plan),
                    _format_plan(proactive_plan),
                ],
            )
            result = self._parser.parse(response)
            logger.info(f"[Judge] selected={result.selected} reason={result.reason!r}")
            return result
        except Exception as e:
            # Judge 실패 시 Reactive로 폴백 (장애 상황에서는 빠른 안정화 우선)
            logger.warning(f"[Judge] LLM 호출 실패, Reactive로 폴백. error={e}")
            return JudgeResult(
                selected=PlannerType.REACTIVE,
                reason="Judge 실패로 인한 Reactive 폴백",
            )
