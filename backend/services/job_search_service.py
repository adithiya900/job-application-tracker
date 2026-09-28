import logging
import os

import requests

from extensions import cache
from schemas.job_suggestion_schema import JobSuggestion


# =========================
# Logger Setup
# =========================
logger = logging.getLogger(__name__)


class JobSearchService:

    # =========================
    # Search Jobs (with caching)
    # =========================
    @staticmethod
    def search_jobs(q, location="", page=1, per_page=5):

        # =========================
        # Validate API Credentials
        # =========================

        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")
        country = os.getenv("ADZUNA_COUNTRY", "in")

        if not app_id or not app_key:

            logger.error(
                "Adzuna API credentials are not configured"
            )

            raise MissingCredentialsError(
                "Adzuna API credentials are not configured. "
                "Set ADZUNA_APP_ID and ADZUNA_APP_KEY "
                "in your environment."
            )

        # =========================
        # Build Cache Key
        # =========================

        cache_key = (
            f"job_search:{q.lower().strip()}"
            f":{location.lower().strip()}"
            f":{page}:{per_page}"
        )

        # =========================
        # Check Cache
        # =========================

        try:

            cached_data = cache.get(cache_key)

            if cached_data is not None:

                logger.info(
                    "CACHE HIT: Retrieved %d job suggestions "
                    "from cache for query '%s' in '%s'",
                    len(cached_data),
                    q,
                    location
                )

                return {
                    "query": q,
                    "location": location,
                    "count": len(cached_data),
                    "cached": True,
                    "source": "cache",
                    "jobs": cached_data
                }

        except Exception as e:

            logger.warning(
                "Cache read failed, continuing with "
                "live API fetch: %s",
                str(e)
            )

        # =========================
        # Cache Miss: Fetch from Adzuna API
        # =========================

        logger.info(
            "CACHE MISS: Fetching live job search results "
            "from Adzuna API for query '%s' in '%s'",
            q,
            location
        )

        url = (
            f"https://api.adzuna.com/v1/api/jobs"
            f"/{country}/search/{page}"
        )

        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": q,
            "results_per_page": per_page,
            "content-type": "application/json"
        }

        if location:
            params["where"] = location

        try:

            response = requests.get(
                url,
                params=params,
                timeout=10
            )

            response.raise_for_status()

        except requests.exceptions.Timeout:

            logger.error(
                "Adzuna API request timed out"
            )

            raise ExternalAPIError(
                "Job search request timed out. "
                "Please try again later."
            )

        except requests.exceptions.HTTPError as e:

            logger.error(
                "Adzuna API returned HTTP error: %s",
                str(e)
            )

            raise ExternalAPIError(
                f"Job search provider returned an error: "
                f"{response.status_code}"
            )

        except requests.exceptions.RequestException as e:

            logger.error(
                "Adzuna API request failed: %s",
                str(e)
            )

            raise ExternalAPIError(
                "Failed to connect to job search provider."
            )

        # =========================
        # Parse Response
        # =========================

        data = response.json()

        raw_results = data.get("results", [])

        # =========================
        # Map to JobSuggestion DTO
        # =========================

        job_suggestions = [

            JobSuggestion.from_adzuna(item).to_dict()

            for item in raw_results

        ]

        # =========================
        # Store in Cache (30 minutes)
        # =========================

        try:

            cache.set(
                cache_key,
                job_suggestions,
                timeout=1800
            )

            logger.info(
                "CACHE STORE: Cached %d job suggestions "
                "for 30 minutes (key: %s)",
                len(job_suggestions),
                cache_key
            )

        except Exception as e:

            logger.warning(
                "Cache write failed: %s",
                str(e)
            )

        return {
            "query": q,
            "location": location,
            "count": len(job_suggestions),
            "cached": False,
            "source": "api",
            "jobs": job_suggestions
        }


# =========================
# Custom Exceptions
# =========================

class MissingCredentialsError(Exception):
    """Raised when API credentials are not configured."""
    pass


class ExternalAPIError(Exception):
    """Raised when external API returns an error."""
    pass
