import asyncio

from src.core.analyzer.workload_state import WorkLoadStateAnalyzer
from src.core.llm import LLM
from src.core.output_parser import ApplicationAgentOutputParser
from src.core.performops.agents import ApplicationAgent
from src.core.performops.model import ApplicationAgentResult
from src.deps.get_llm import get_llm

APPLICATION_AGENT_PROMPT = """Below is the application status for {app_deployment_name} (project_id: {project_id}).

## Deployment Events
{deployment_status}

## Pod Logs
{pod_log}

Analyze application health focusing on pod restarts, OOMKill, crash loops, error patterns in logs, and deployment issues.
For each metric provide: state (current condition), change (recent trend), basis (evidence used).
Provide an overall application analysis summary.

IMPORTANT: Return ONLY the JSON below. English only.

{{
  "deployment_status": {{"state": "...", "change": "...", "basis": "..."}},
  "pod_log": {{"state": "...", "change": "...", "basis": "..."}},
  "analysis": "Application root cause analysis summary"
}}"""


class ApplicationAgentImpl(ApplicationAgent):
    def __init__(
        self,
        workload_state_analyzer: WorkLoadStateAnalyzer,
        llm: LLM = None,
    ):
        self._workload_state_analyzer = workload_state_analyzer
        self._llm = llm or get_llm(template=APPLICATION_AGENT_PROMPT)
        self._parser = ApplicationAgentOutputParser()

    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> ApplicationAgentResult:
        deployment_status, pod_log = await asyncio.gather(
            self._workload_state_analyzer.get_app_deployment_events(
                project_id, app_deployment_name
            ),
            self._workload_state_analyzer.get_app_deployment_logs(
                project_id, app_deployment_name
            ),
        )

        response = await self._llm.chat(
            variables=[
                app_deployment_name,
                project_id,
                deployment_status,
                pod_log,
            ],
        )

        return self._parser.parse(response)
