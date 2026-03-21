from src.common.config.resource_manager import ResourceManagerConfig
from src.core.analyzer.workload_state import WorkLoadStateAnalyzer
from src.core.requester import Requester


class ResourceManagerWorkLoadStateAnalyzer(WorkLoadStateAnalyzer):

    def __init__(self, requester: Requester):
        self._requester = requester
        self._base_url = ResourceManagerConfig.URL

    async def get_project_resource(
            self,
            project_id: int,
    ):
        response = await self._requester.get(
            url=f"{self._base_url}/projects/{project_id}/resource",
        )
        return response["data"]

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
