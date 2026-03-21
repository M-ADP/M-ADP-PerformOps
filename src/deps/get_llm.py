from src.core.llm import LLM
from src.infra.llm.openrouter import OpenRouterLLM


def get_llm(
        template: str = None,
) -> LLM:
    return OpenRouterLLM(template=template)
