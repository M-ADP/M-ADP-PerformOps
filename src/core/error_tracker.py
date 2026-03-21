from abc import ABC, abstractmethod


class ErrorTracker(ABC):

    @abstractmethod
    async def get_error(
            self,
            project_id : int,
            app_deployment_id : int
    ):
        raise NotImplementedError

