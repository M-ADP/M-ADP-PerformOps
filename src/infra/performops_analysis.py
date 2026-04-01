import asyncio
import logging

from src.core.llm import LLM
from src.core.output_parser import SynthesisOutputParser
from src.core.performops.agents import (
    ApplicationAgent,
    InfrastructureAgent,
    TrafficAgent,
)
from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.model import (
    PerformOpsAnalysisResource,
    PerformOpsAnalysisResult,
)
from src.deps.get_llm import get_llm

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = """You are a synthesis agent. Below are analysis results from three specialized agents for {app_deployment_name} (project_id: {project_id}).

## Infrastructure Agent
{infrastructure_analysis}

## Application Agent
{application_analysis}

## Traffic Agent
{traffic_analysis}

Correlate findings across all three domains and produce a unified root cause analysis.
Identify cross-domain causal chains (e.g. traffic spike → CPU saturation → pod crash).

IMPORTANT: Return ONLY the JSON below. English only.

{{
  "result": "Unified root cause analysis integrating infrastructure, application, and traffic findings"
}}"""


class PerformOpsAnalysisImpl(PerformOpsAnalysis):
    def __init__(
        self,
        infrastructure_agent: InfrastructureAgent,
        application_agent: ApplicationAgent,
        traffic_agent: TrafficAgent,
        llm: LLM = None,
    ):
        self._infrastructure_agent = infrastructure_agent
        self._application_agent = application_agent
        self._traffic_agent = traffic_agent
        self._llm = llm or get_llm(template=SYNTHESIS_PROMPT)
        self._parser = SynthesisOutputParser()

    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> PerformOpsAnalysisResult:
        logger.info(
            f"[PerformOpsAnalysis] Starting multi-agent analysis for "
            f"{app_deployment_name} (project_id={project_id})"
        )

        infra_result, app_result, traffic_result = await asyncio.gather(
            self._infrastructure_agent.analyze(project_id, app_deployment_name),
            self._application_agent.analyze(project_id, app_deployment_name),
            self._traffic_agent.analyze(project_id, app_deployment_name),
        )

        logger.info(
            f"[PerformOpsAnalysis] Agents done — "
            f"infra={infra_result.analysis!r:.80} "
            f"app={app_result.analysis!r:.80} "
            f"traffic={traffic_result.analysis!r:.80}"
        )

        response = await self._llm.chat(
            variables=[
                app_deployment_name,
                project_id,
                infra_result.analysis,
                app_result.analysis,
                traffic_result.analysis,
            ],
        )

        result_text = self._parser.parse(response)

        return PerformOpsAnalysisResult(
            result=result_text,
            resource=PerformOpsAnalysisResource(
                project_resource=infra_result.project_resource,
                app_deployment_resource=infra_result.app_deployment_resource,
                deployment_status=app_result.deployment_status,
                pod_log=app_result.pod_log,
                traffic=traffic_result.traffic,
                latency=traffic_result.latency,
            ),
        )
