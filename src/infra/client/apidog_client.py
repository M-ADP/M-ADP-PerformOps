import logging
from typing import List

from src.common.config.apidog import ApidogConfig
from src.core.performops.model import UserAction
from src.infra.client.http_requester import HttpRequester

logger = logging.getLogger(__name__)

_APIDOG_BASE_URL = "https://api.apidog.com"
_PAGE_SIZE = 100
_WRITE_METHODS = {"post", "put", "patch", "delete"}


class ApidogClient:

    def __init__(self, requester: HttpRequester = None):
        self._requester = requester or HttpRequester()
        self._token = ApidogConfig.TOKEN
        self._project_id = ApidogConfig.PROJECT_ID

    async def fetch_user_actions(self) -> List[UserAction]:
        actions: List[UserAction] = []
        page = 1

        while True:
            data = await self._requester.get(
                url=f"{_APIDOG_BASE_URL}/api/v1/projects/{self._project_id}/http-apis",
                headers={"X-Apidog-Api-Access-Token": self._token},
                params={"page": page, "size": _PAGE_SIZE},
            )
            apis = data.get("data", [])

            for api in apis:
                if api.get("method", "").lower() not in _WRITE_METHODS:
                    continue
                actions.append(UserAction(
                    method=api["method"].upper(),
                    path=api["path"],
                    summary=api.get("name", ""),
                ))

            if len(apis) < _PAGE_SIZE:
                break
            page += 1

        logger.info(f"[ApidogClient] Loaded {len(actions)} user actions from apidog")
        return actions
