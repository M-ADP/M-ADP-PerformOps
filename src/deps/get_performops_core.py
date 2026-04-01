from src.core.performops.agents import ApplicationAgent, InfrastructureAgent, TrafficAgent
from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.core import PerformOpsCore
from src.core.performops.judge import PerformOpsJudge
from src.core.performops.planner import PerformOpsPlanner
from src.core.performops.summarizer import PerformOpsSummarizer
from src.core.performops.validator import PerformOpsValidator
from src.infra.client.http_requester import HttpRequester
from src.infra.client.prometheus_metrics_analyzer import PrometheusMetricsAnalyzer
from src.infra.client.resource_manager_workload_state_analyzer import (
    ResourceManagerWorkLoadStateAnalyzer,
)
from src.infra.performops_analysis import PerformOpsAnalysisImpl
from src.infra.performops_application_agent import ApplicationAgentImpl
from src.infra.performops_infrastructure_agent import InfrastructureAgentImpl
from src.infra.performops_judge import PerformOpsJudgeImpl
from src.infra.performops_planner import ReactivePlanner, ProactivePlanner
from src.infra.performops_summarizer import PerformOpsSummarizerImpl
from src.infra.performops_traffic_agent import TrafficAgentImpl
from src.infra.performops_validator import PerformOpsValidatorImpl


async def get_performops_core() -> PerformOpsCore:
    analysis = await get_performops_analysis()
    reactive_planner = await get_reactive_planner()
    proactive_planner = await get_proactive_planner()
    judge = await get_performops_judge()
    summarizer = await get_performops_summarizer()
    validator = await get_performops_validator()

    return PerformOpsCore(
        analysis=analysis,
        reactive_planner=reactive_planner,
        proactive_planner=proactive_planner,
        judge=judge,
        summarizer=summarizer,
        validator=validator,
    )


async def get_performops_analysis() -> PerformOpsAnalysis:
    requester = HttpRequester()
    metrics_analyzer = PrometheusMetricsAnalyzer(requester=requester)
    workload_state_analyzer = ResourceManagerWorkLoadStateAnalyzer(requester=requester)

    return PerformOpsAnalysisImpl(
        infrastructure_agent=InfrastructureAgentImpl(
            metrics_analyzer=metrics_analyzer,
            workload_state_analyzer=workload_state_analyzer,
        ),
        application_agent=ApplicationAgentImpl(
            workload_state_analyzer=workload_state_analyzer,
        ),
        traffic_agent=TrafficAgentImpl(
            metrics_analyzer=metrics_analyzer,
        ),
    )


async def get_infrastructure_agent() -> InfrastructureAgent:
    requester = HttpRequester()
    return InfrastructureAgentImpl(
        metrics_analyzer=PrometheusMetricsAnalyzer(requester=requester),
        workload_state_analyzer=ResourceManagerWorkLoadStateAnalyzer(requester=requester),
    )


async def get_application_agent() -> ApplicationAgent:
    requester = HttpRequester()
    return ApplicationAgentImpl(
        workload_state_analyzer=ResourceManagerWorkLoadStateAnalyzer(requester=requester),
    )


async def get_traffic_agent() -> TrafficAgent:
    requester = HttpRequester()
    return TrafficAgentImpl(
        metrics_analyzer=PrometheusMetricsAnalyzer(requester=requester),
    )


async def get_reactive_planner() -> PerformOpsPlanner:
    return ReactivePlanner()


async def get_proactive_planner() -> PerformOpsPlanner:
    return ProactivePlanner()


async def get_performops_judge() -> PerformOpsJudge:
    return PerformOpsJudgeImpl()


async def get_performops_summarizer() -> PerformOpsSummarizer:
    return PerformOpsSummarizerImpl()


async def get_performops_validator() -> PerformOpsValidator:
    return PerformOpsValidatorImpl()
