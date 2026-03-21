from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.core import PerformOpsCore
from src.core.performops.planner import PerformOpsPlanner
from src.core.performops.summarizer import PerformOpsSummarizer


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
    return PerformOpsAnalysisImpl()

async def get_performops_planner() -> PerformOpsPlanner:
    return PerformOpsPlannerImpl()

async def get_performops_summarizer() -> PerformOpsSummarizer:
    return PerformOpsSummarizerImpl()

