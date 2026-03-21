from abc import ABC, abstractmethod

# Timeseries data 받기
class MetricsAnalyzer(ABC):

    @abstractmethod
    async def get_app_deployment_traffic(
            self,
            project_id : int,
            app_deployment_name : str,
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_app_deployment_cpu(
            self,
            project_id : int,
            app_deployment_name : str,
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_app_deployment_memory(
            self,
            project_id : int,
            app_deployment_name : str,
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_app_deployment_disk(
            self,
            project_id : int,
            app_deployment_name : str,
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_app_deployment_latency(
            self,
            project_id : int,
            app_deployment_name : str,
    ):
        raise NotImplementedError

