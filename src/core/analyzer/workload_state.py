from abc import ABC, abstractmethod


class WorkLoadStateAnalyzer(ABC):

    @abstractmethod
    async def get_app_deployment_resource_in_project(
            self,
            project_id : int
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_app_deployment_events(
            self,
            project_id : int,
            app_deployment_name : str
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_app_deployment_logs(
            self,
            project_id: int,
            app_deployment_name: str
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_app_deployment_resource(
            self,
            project_id : int,
            app_deployment_name : str
    ):
        raise NotImplementedError
