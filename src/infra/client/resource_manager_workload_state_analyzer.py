from src.common.config import settings
from src.core.analyzer.workload_state import WorkLoadStateAnalyzer
from src.core.requester import Requester


class ResourceManagerWorkLoadStateAnalyzer(WorkLoadStateAnalyzer):

    def __init__(self, requester: Requester):
        self._requester = requester
        self._base_url = settings.resource_manager_url

    async def get_app_deployment_resource_in_project(
            self,
            project_id: int,
    ):
        return await self._requester.get(
            url=f"{self._base_url}/apps/{project_id}/resource",
        )

    async def get_app_deployment_events(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        return await self._requester.get(
            url=f"{self._base_url}/apps/{project_id}/{app_deployment_name}/events",
        )

    async def get_app_deployment_logs(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        return await self._requester.get(
            url=f"{self._base_url}/apps/{project_id}/{app_deployment_name}/logs",
        )

    async def get_app_deployment_resource(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        response = await self._requester.get(
            url=f"{self._base_url}/apps/{project_id}/resource",
            params={"names": app_deployment_name},
        )
        return response["data"][0]
