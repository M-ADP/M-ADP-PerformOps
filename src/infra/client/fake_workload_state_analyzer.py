from src.core.analyzer.workload_state import WorkLoadStateAnalyzer


class FakeWorkLoadStateAnalyzer(WorkLoadStateAnalyzer):

    async def get_project_resource(self, project_id: int):
        return {
            "cpu": {"limit": "8.0", "used": "6.8", "percentage": 85.0, "unit": "cores"},
            "memory": {"limit": "16.0", "used": "13.0", "percentage": 81.25, "unit": "GiB"},
        }

    async def get_app_deployment_resource(self, project_id: int, app_deployment_name: str):
        return {
            "cpu": {"limit": "2.0", "used": "1.7", "percentage": 85.0, "unit": "cores"},
            "memory": {"limit": "4.0", "used": "3.2", "percentage": 80.0, "unit": "GiB"},
            "instance": {"limit": 3, "used": 3, "percentage": 100.0},
        }

    async def get_app_deployment_events(self, project_id: int, app_deployment_name: str):
        return {
            "events": [
                {
                    "type": "Warning",
                    "reason": "OOMKilled",
                    "message": "Container killed due to OOM",
                    "count": 3,
                }
            ]
        }

    async def get_app_deployment_logs(self, project_id: int, app_deployment_name: str):
        return {
            "pod_logs": [
                {
                    "pod_name": f"{app_deployment_name}-xxxxx",
                    "logs": "ERROR OutOfMemoryError: Java heap space\nWARN High memory usage detected",
                }
            ]
        }
