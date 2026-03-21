from src.common.config import settings
from src.core.error_tracker import ErrorTracker
from src.core.requester import Requester


class SentryErrorTracker(ErrorTracker):

    def __init__(self, requester: Requester):
        self._requester = requester
        self._base_url = "https://sentry.io/api/0"
        self._headers = {"Authorization": f"Bearer {settings.sentry_auth_token}"}

    async def get_error(
            self,
            project_id: int,
            app_deployment_name: str,
    ):
        return await self._requester.get(
            url=(
                f"{self._base_url}/projects"
                f"/{settings.sentry_organization_slug}"
                f"/{project_id}/issues/"
            ),
            params={"query": f"project_id:{project_id} app_deployment_name:{app_deployment_name}"},
            headers=self._headers,
        )
