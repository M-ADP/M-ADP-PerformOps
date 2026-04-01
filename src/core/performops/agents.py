from abc import ABC, abstractmethod

from src.core.performops.model import (
    ApplicationAgentResult,
    InfrastructureAgentResult,
    TrafficAgentResult,
)


class InfrastructureAgent(ABC):
    @abstractmethod
    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> InfrastructureAgentResult:
        raise NotImplementedError


class ApplicationAgent(ABC):
    @abstractmethod
    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> ApplicationAgentResult:
        raise NotImplementedError


class TrafficAgent(ABC):
    @abstractmethod
    async def analyze(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> TrafficAgentResult:
        raise NotImplementedError
