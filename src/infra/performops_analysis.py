import asyncio

from src.core.analyzer.metrics import MetricsAnalyzer
from src.core.analyzer.workload_state import WorkLoadStateAnalyzer
from src.core.llm import LLM
from src.core.output_parser import AnalysisResultOutputParser
from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.model import PerformOpsAnalysisResult
from src.deps.get_llm import get_llm

ANALYSIS_PROMPT = """Below is the current status data for {app_deployment_name} (project_id: {project_id}).

## Project Resource
{project_resource}

## App Deployment Resource (CPU/Memory)
CPU: {cpu}
Memory: {memory}
Allocation: {app_deployment_resource}

## Deployment Events
{deployment_status}

## Pod Logs
{pod_log}

## Traffic
{traffic}

## Latency (P95 latency)
{latency}

Analyze each item for current state, change, and basis.
Provide overall root cause analysis summary (result).

IMPORTANT: Return ONLY the JSON format below. No explanations, no additional text. Use English only.

{{
  "result": "Overall root cause analysis summary",
  "project_resource": {{"state": "...", "change": "...", "basis": "..."}},
  "app_deployment_resource": {{"state": "...", "change": "...", "basis": "..."}},
  "deployment_status": {{"state": "...", "change": "...", "basis": "..."}},
  "pod_log": {{"state": "...", "change": "...", "basis": "..."}},
  "traffic": {{"state": "...", "change": "...", "basis": "..."}},
  "latency": {{"state": "...", "change": "...", "basis": "..."}}
}}"""


class PerformOpsAnalysisImpl(PerformOpsAnalysis):
    def __init__(
        self,
        metrics_analyzer: MetricsAnalyzer,
        workload_state_analyzer: WorkLoadStateAnalyzer,
        llm: LLM = None,
    ):
        super().__init__(
            metrics_analyzer=metrics_analyzer,
            workload_state_analyzer=workload_state_analyzer,
        )
        self._llm = llm or get_llm(template=ANALYSIS_PROMPT)
        self._parser = AnalysisResultOutputParser()

    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> PerformOpsAnalysisResult:
        (
            project_resource,
            app_deployment_resource,
            deployment_status,
            pod_log,
            traffic,
            cpu,
            memory,
            latency,
        ) = await asyncio.gather(
            self._workload_state_analyzer.get_project_resource(project_id),
            self._workload_state_analyzer.get_app_deployment_resource(
                project_id, app_deployment_name
            ),
            self._workload_state_analyzer.get_app_deployment_events(
                project_id, app_deployment_name
            ),
            self._workload_state_analyzer.get_app_deployment_logs(
                project_id, app_deployment_name
            ),
            self._metrics_analyzer.get_app_deployment_traffic(
                project_id, app_deployment_name
            ),
            self._metrics_analyzer.get_app_deployment_cpu(
                project_id, app_deployment_name
            ),
            self._metrics_analyzer.get_app_deployment_memory(
                project_id, app_deployment_name
            ),
            self._metrics_analyzer.get_app_deployment_latency(
                project_id, app_deployment_name
            ),
        )

        response = await self._llm.chat(
            variables=[
                app_deployment_name,
                project_id,
                project_resource,
                cpu,
                memory,
                app_deployment_resource,
                deployment_status,
                pod_log,
                traffic,
                latency,
            ],
        )

        return self._parser.parse(response)
