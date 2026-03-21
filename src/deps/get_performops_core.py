from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.core import PerformOpsCore
from src.core.performops.planner import PerformOpsPlanner
from src.core.performops.summarizer import PerformOpsSummarizer
from src.infra.client.fake_metrics_analyzer import FakeMetricsAnalyzer
from src.infra.client.fake_workload_state_analyzer import FakeWorkLoadStateAnalyzer
from src.infra.performops_analysis import PerformOpsAnalysisImpl
from src.infra.performops_planner import PerformOpsPlannerImpl
from src.infra.performops_summarizer import PerformOpsSummarizerImpl


async def get_performops_core() -> PerformOpsCore:
    analysis = await get_performops_analysis()
    planner = await get_performops_planner()
    summarizer = await get_performops_summarizer()

    return PerformOpsCore(
        analysis=analysis,
        planner=planner,
        summarizer=summarizer,
    )

async def get_performops_analysis() -> PerformOpsAnalysis:
    return PerformOpsAnalysisImpl(
        metrics_analyzer=FakeMetricsAnalyzer(),
        workload_state_analyzer=FakeWorkLoadStateAnalyzer(),
    )

async def get_performops_planner() -> PerformOpsPlanner:
    return PerformOpsPlannerImpl()

async def get_performops_summarizer() -> PerformOpsSummarizer:
    return PerformOpsSummarizerImpl()
