import asyncio

from src.core.analyzer.metrics import MetricsAnalyzer
from src.core.llm import LLM
from src.core.output_parser import TrafficAgentOutputParser
from src.core.performops.agents import TrafficAgent
from src.core.performops.model import TrafficAgentResult
from src.deps.get_llm import get_llm

TRAFFIC_AGENT_PROMPT = """Below is the traffic and latency data for {app_deployment_name} (project_id: {project_id}).

## Traffic (Istio metrics — RPS, error rates)
{traffic}

## Latency (P95)
{latency}

Analyze traffic patterns focusing on request rate anomalies, error rate spikes, P95 latency trends, and Istio-level issues.
For each metric provide: state (current condition), change (recent trend), basis (evidence used).
Provide an overall traffic analysis summary.

IMPORTANT: Return ONLY the JSON below. English only.

{{
  "traffic": {{"state": "...", "change": "...", "basis": "..."}},
  "latency": {{"state": "...", "change": "...", "basis": "..."}},
  "analysis": "Traffic root cause analysis summary"
}}"""


class TrafficAgentImpl(TrafficAgent):
    def __init__(
        self,
        metrics_analyzer: MetricsAnalyzer,
        llm: LLM = None,
    ):
        self._metrics_analyzer = metrics_analyzer
        self._llm = llm or get_llm(template=TRAFFIC_AGENT_PROMPT)
        self._parser = TrafficAgentOutputParser()

    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> TrafficAgentResult:
        traffic, latency = await asyncio.gather(
            self._metrics_analyzer.get_app_deployment_traffic(
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
                traffic,
                latency,
            ],
        )

        return self._parser.parse(response)
