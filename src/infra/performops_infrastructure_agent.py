import asyncio

from src.core.analyzer.metrics import MetricsAnalyzer
from src.core.analyzer.workload_state import WorkLoadStateAnalyzer
from src.core.llm import LLM
from src.core.output_parser import InfrastructureAgentOutputParser
from src.core.performops.agents import InfrastructureAgent
from src.core.performops.model import InfrastructureAgentResult
from src.deps.get_llm import get_llm

INFRASTRUCTURE_AGENT_PROMPT = """Below is the infrastructure status for {app_deployment_name} (project_id: {project_id}).

## Project Resource (Node/Namespace capacity)
{project_resource}

## App Deployment Resource (CPU/Memory allocation & limits)
CPU usage: {cpu}
Memory usage: {memory}
Resource config: {app_deployment_resource}

Analyze infrastructure health focusing on CPU saturation, memory pressure, node capacity, and resource contention.
For each metric provide: state (current condition), change (recent trend), basis (evidence used).
Provide an overall infrastructure analysis summary.

IMPORTANT: Return ONLY the JSON below. English only.

{{
  "project_resource": {{"state": "...", "change": "...", "basis": "..."}},
  "app_deployment_resource": {{"state": "...", "change": "...", "basis": "..."}},
  "analysis": "Infrastructure root cause analysis summary"
}}"""


class InfrastructureAgentImpl(InfrastructureAgent):
    def __init__(
        self,
        metrics_analyzer: MetricsAnalyzer,
        workload_state_analyzer: WorkLoadStateAnalyzer,
        llm: LLM = None,
    ):
        self._metrics_analyzer = metrics_analyzer
        self._workload_state_analyzer = workload_state_analyzer
        self._llm = llm or get_llm(template=INFRASTRUCTURE_AGENT_PROMPT)
        self._parser = InfrastructureAgentOutputParser()

    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> InfrastructureAgentResult:
        project_resource, app_deployment_resource, cpu, memory = await asyncio.gather(
            self._workload_state_analyzer.get_project_resource(project_id),
            self._workload_state_analyzer.get_app_deployment_resource(
                project_id, app_deployment_name
            ),
            self._metrics_analyzer.get_app_deployment_cpu(
                project_id, app_deployment_name
            ),
            self._metrics_analyzer.get_app_deployment_memory(
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
            ],
        )

        return self._parser.parse(response)
