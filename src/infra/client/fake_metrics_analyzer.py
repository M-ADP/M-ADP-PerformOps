from src.core.analyzer.metrics import MetricsAnalyzer


class FakeMetricsAnalyzer(MetricsAnalyzer):

    async def get_app_deployment_traffic(self, project_id: int, app_deployment_name: str):
        return {"value": "120 req/s"}

    async def get_app_deployment_cpu(self, project_id: int, app_deployment_name: str):
        return {"value": "0.85 cores"}

    async def get_app_deployment_memory(self, project_id: int, app_deployment_name: str):
        return {"value": "3.2 GiB"}

    async def get_app_deployment_disk(self, project_id: int, app_deployment_name: str):
        return {"value": "8.0 GiB"}

    async def get_app_deployment_latency(self, project_id: int, app_deployment_name: str):
        return {"value": "850ms (P95)"}
