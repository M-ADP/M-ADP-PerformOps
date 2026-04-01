from src.core.llm import LLM
from src.core.output_parser import SummaryOutputParser
from src.core.performops.model import (
    PerformOpsAnalysisResult,
    PerformOpsPlan,
    PerformOpsSummary,
)
from src.core.performops.summarizer import PerformOpsSummarizer
from src.deps.get_llm import get_llm

SUMMARY_PROMPT = """Below is the performance issue analysis result and action plan.

## Analysis Result
{result}

## Resource Status
- Project Resource: {project_resource}
- App Deployment Resource: {app_deployment_resource}
- Deployment Status: {deployment_status}
- Pod Log: {pod_log}
- Traffic: {traffic}
- Latency: {latency}

## Action Plan
{plans}

Based on the above, provide an overall summary and severity level.

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text. Use English only.
Severity must be one of: "low", "medium", "high".
Summary must include the current situation and the actions the user should take (including user actions).

{{
  "summary": "Overall situation summary and user action guidance",
  "severity": "low | medium | high"
}}"""


class PerformOpsSummarizerImpl(PerformOpsSummarizer):
    def __init__(self, llm: LLM = None):
        self._llm = llm or get_llm(template=SUMMARY_PROMPT)
        self._parser = SummaryOutputParser()

    async def summarize(
        self,
        analysis_result: PerformOpsAnalysisResult,
        plan: PerformOpsPlan,
    ) -> PerformOpsSummary:
        def format_plan(p):
            if p.user_action:
                return f"- {p.action} (이유: {p.reason}) → {p.user_action.summary}"
            return f"- {p.action} (이유: {p.reason})"

        plans_text = "\n".join(format_plan(p) for p in plan.actions)

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

        return self._parser.parse(response)
