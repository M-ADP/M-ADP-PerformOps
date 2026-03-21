from src.core.error_tracker import ErrorTracker


class SentryErrorTacker(ErrorTracker):

    async def get_error(self, project_id: int, app_deployment_name: str):
        pass