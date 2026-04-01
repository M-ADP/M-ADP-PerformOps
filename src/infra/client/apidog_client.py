import logging
from typing import List

from src.common.config.apidog import ApidogConfig
from src.core.performops.model import UserAction
from src.infra.client.http_requester import HttpRequester

logger = logging.getLogger(__name__)

_APIDOG_BASE_URL = "https://api.apidog.com"
_PAGE_SIZE = 100
_WRITE_METHODS = {"post", "put", "patch", "delete"}
# Resource Manager API가 포함된 폴더 ID들 (6985949의 하위 폴더들)
_RESOURCE_MANAGER_FOLDER_IDS = {6985945, 6985946, 7389098, 7541379}


class ApidogClient:
    def __init__(self, requester: HttpRequester = None):
        self._requester = requester or HttpRequester()
        self._token = ApidogConfig.TOKEN
        self._project_id = ApidogConfig.PROJECT_ID

    async def fetch_user_actions(self) -> List[UserAction]:
        actions: List[UserAction] = []
        page = 1
        max_pages = 5  # 최대 5페이지만 조회 (안전장치)

        while page <= max_pages:
            logger.info(f"[ApidogClient] Fetching page {page}...")
            try:
                data = await self._requester.get(
                    url=f"{_APIDOG_BASE_URL}/api/v1/projects/{self._project_id}/http-apis",
                    headers={"X-Apidog-Api-Access-Token": self._token},
                    params={"page": page, "size": _PAGE_SIZE},
                )
                apis = data.get("data", [])
                logger.info(f"[ApidogClient] Page {page}: {len(apis)} APIs found")

                for api in apis:
                    if api.get("method", "").lower() not in _WRITE_METHODS:
                        continue
                    # Resource Manager 폴더의 API만 포함
                    if api.get("folderId") not in _RESOURCE_MANAGER_FOLDER_IDS:
                        continue
                    actions.append(
                        UserAction(
                            method=api["method"].upper(),
                            path=api["path"],
                            summary=api.get("name", ""),
                        )
                    )

                if len(apis) < _PAGE_SIZE:
                    logger.info(f"[ApidogClient] Last page reached")
                    break
                page += 1
            except Exception as e:
                logger.error(f"[ApidogClient] Error fetching page {page}: {e}")
                break

        logger.info(f"[ApidogClient] Loaded {len(actions)} user actions from apidog")
        return actions
