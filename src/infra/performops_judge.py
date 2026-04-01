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

JUDGE_PROMPT = """You are a Kubernetes performance operations expert.
Two action plans from different perspectives have been created for the same incident.
Analyze the current situation and select the more appropriate plan.

## Analysis Result
{analysis_result}

## Resource Status
- Project Resource: {project_resource}
- App Deployment Resource: {app_deployment_resource}
- Deployment Status: {deployment_status}
- Pod Log: {pod_log}
- Traffic: {traffic}
- Latency: {latency}

---

## Plan A — Reactive (Immediate symptom mitigation)
{reactive_plan}

## Plan B — Proactive (Root cause structural improvement)
{proactive_plan}

---

## Selection Criteria
- **Choose Reactive when**: An active incident is in progress or service disruption risk is high. Quick stabilization takes priority over long-term optimization.
- **Choose Proactive when**: The root cause is clear and a repeating pattern is observed. Preventing recurrence is more effective than immediate action.

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text. Use English only.

{{
  "selected": "reactive",
  "reason": "Brief reason for selection"
}}

or

{{
  "selected": "proactive",
  "reason": "Brief reason for selection"
}}"""


def _format_plan(plan: PerformOpsPlan) -> str:
    lines = []
    for i, action in enumerate(plan.actions, 1):
        api_info = ""
        if action.http_method and action.http_path:
            api_info = f" → {action.http_method} {action.http_path}"
        lines.append(f"{i}. {action.action} (reason: {action.reason}){api_info}")
    return "\n".join(lines) if lines else "(no plan)"


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
                reason="Judge failed, falling back to Reactive",
            )
