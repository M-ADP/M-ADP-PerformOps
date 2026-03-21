from src.core.error_tracker import ErrorTracker
from src.infra.sentry_error_tracker import SentryErrorTacker


async def get_error_tracker() -> ErrorTracker:
    return SentryErrorTacker()
