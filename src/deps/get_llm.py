from typing import Optional

from src.core.llm import LLM
from src.infra.llm.openrouter import OpenRouterLLM


def get_llm(
    template: Optional[str] = None,
) -> LLM:
    return OpenRouterLLM(template=template)
