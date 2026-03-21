from src.common.config.prometheus import PrometheusConfig
from src.core.analyzer.metrics import MetricsAnalyzer
from src.core.requester import Requester


class PrometheusMetricsAnalyzer(MetricsAnalyzer):

    def __init__(self, requester: Requester):
        self._requester = requester
        self._base_url = PrometheusConfig.URL

    async def _query(self, promql: str):
        return await self._requester.post(
            url=f"{self._base_url}/api/v1/query",
            body={"query": promql},
        )

    async def get_app_deployment_traffic(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        promql = (
            f'sum(rate(istio_requests_total{{'
            f'namespace="{project_id}",'
            f'x-app-deployment-id="{app_deployment_name}"'
            f'}}[5m])) by (response_code)'
        )
        return await self._query(promql)

    async def get_app_deployment_cpu(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        promql = (
            f'sum(rate(container_cpu_usage_seconds_total{{'
            f'namespace="{project_id}",'
            f'x-app-deployment-id="{app_deployment_name}"'
            f'}}[5m]))'
        )
        return await self._query(promql)

    async def get_app_deployment_memory(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        promql = (
            f'sum(container_memory_usage_bytes{{'
            f'namespace="{project_id}",'
            f'x-app-deployment-id="{app_deployment_name}"'
            f'}})'
        )
        return await self._query(promql)

    async def get_app_deployment_disk(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        promql = (
            f'sum(container_fs_usage_bytes{{'
            f'namespace="{project_id}",'
            f'x-app-deployment-id="{app_deployment_name}"'
            f'}})'
        )
        return await self._query(promql)
