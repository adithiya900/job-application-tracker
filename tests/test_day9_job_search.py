"""
Day 9 Tests: Job Search (External Adzuna API Integration)
All external API calls are mocked — no real Adzuna requests are made.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from schemas.job_suggestion_schema import (
    JobSuggestion,
    strip_html_tags,
    format_salary_range
)
from services.job_search_service import (
    JobSearchService,
    MissingCredentialsError,
    ExternalAPIError
)


# ==========================================
# Fixtures
# ==========================================

SAMPLE_ADZUNA_ITEM = {
    "title": "<b>Python Developer</b>",
    "company": {"display_name": "Acme Corp"},
    "location": {"display_name": "Chennai, Tamil Nadu"},
    "salary_min": 500000.0,
    "salary_max": 800000.0,
    "description": "<p>We need a <b>Python</b> developer.</p>",
    "redirect_url": "https://www.adzuna.in/jobs/123",
    "created": "2024-01-15T10:00:00Z"
}

SAMPLE_ADZUNA_RESPONSE = {
    "results": [SAMPLE_ADZUNA_ITEM]
}


# ==========================================
# Unit Tests: JobSuggestion DTO
# ==========================================

class TestJobSuggestionDTO:

    def test_from_adzuna_maps_fields_correctly(self):
        """Test DTO maps Adzuna fields correctly."""

        suggestion = JobSuggestion.from_adzuna(SAMPLE_ADZUNA_ITEM)

        assert suggestion.title == "Python Developer"
        assert suggestion.company == "Acme Corp"
        assert suggestion.location == "Chennai, Tamil Nadu"
        assert suggestion.salary_min == 500000.0
        assert suggestion.salary_max == 800000.0
        assert "5,00,000" in suggestion.salary_range or "500,000" in suggestion.salary_range
        assert "We need a" in suggestion.description
        assert "Python" in suggestion.description
        assert suggestion.redirect_url == "https://www.adzuna.in/jobs/123"
        assert suggestion.created == "2024-01-15T10:00:00Z"

    def test_html_tags_stripped_from_title(self):
        """HTML tags are stripped from title."""

        suggestion = JobSuggestion.from_adzuna(SAMPLE_ADZUNA_ITEM)
        assert "<b>" not in suggestion.title
        assert "</b>" not in suggestion.title

    def test_html_tags_stripped_from_description(self):
        """HTML tags are stripped from description."""

        suggestion = JobSuggestion.from_adzuna(SAMPLE_ADZUNA_ITEM)
        assert "<p>" not in suggestion.description
        assert "<b>" not in suggestion.description

    def test_to_dict_contains_all_keys(self):
        """to_dict() returns all expected keys."""

        suggestion = JobSuggestion.from_adzuna(SAMPLE_ADZUNA_ITEM)
        d = suggestion.to_dict()

        expected_keys = [
            "title", "company", "location",
            "salary_min", "salary_max", "salary_range",
            "description", "redirect_url", "created"
        ]

        for key in expected_keys:
            assert key in d

    def test_missing_company_defaults_to_unknown(self):
        """Missing company defaults to 'Unknown Company'."""

        item = dict(SAMPLE_ADZUNA_ITEM)
        item["company"] = {}

        suggestion = JobSuggestion.from_adzuna(item)
        assert suggestion.company == "Unknown Company"

    def test_missing_location_defaults_to_unknown(self):
        """Missing location defaults to 'Unknown Location'."""

        item = dict(SAMPLE_ADZUNA_ITEM)
        item["location"] = {}

        suggestion = JobSuggestion.from_adzuna(item)
        assert suggestion.location == "Unknown Location"


# ==========================================
# Unit Tests: Salary Formatting
# ==========================================

class TestSalaryFormatting:

    def test_both_min_max_provided(self):
        result = format_salary_range(500000, 800000)
        assert "500,000" in result or "5,00,000" in result
        assert "-" in result or "–" in result or "-" in result

    def test_only_min_provided(self):
        result = format_salary_range(500000, None)
        assert "From" in result

    def test_only_max_provided(self):
        result = format_salary_range(None, 800000)
        assert "Up to" in result

    def test_neither_provided(self):
        result = format_salary_range(None, None)
        assert result == "Not disclosed"


# ==========================================
# Unit Tests: strip_html_tags
# ==========================================

class TestStripHtmlTags:

    def test_strips_bold_tags(self):
        assert strip_html_tags("<b>Python</b>") == "Python"

    def test_strips_paragraph_tags(self):
        assert strip_html_tags("<p>Hello</p>") == "Hello"

    def test_empty_string(self):
        assert strip_html_tags("") == ""

    def test_none_input(self):
        assert strip_html_tags(None) == ""

    def test_no_tags(self):
        assert strip_html_tags("plain text") == "plain text"


# ==========================================
# Integration Tests: API Endpoints
# ==========================================

class TestJobSearchEndpoint:

    def _get_token(self, client, test_user):
        """Helper: get JWT token via login."""
        from flask_jwt_extended import create_access_token
        from app import app
        with app.app_context():
            return create_access_token(identity=str(test_user.id))

    def test_missing_q_returns_400(self, client, auth_headers):
        """Missing q param → 400."""

        response = client.get(
            "/api/jobs/search",
            headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "q" in data["error"].lower() or "required" in data["error"].lower()

    def test_blank_q_returns_400(self, client, auth_headers):
        """Blank q param → 400."""

        response = client.get(
            "/api/jobs/search?q=   ",
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_unauthenticated_request_returns_401(self, client):
        """No JWT → 401."""

        response = client.get("/api/jobs/search?q=python")
        assert response.status_code == 401

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_successful_job_search(
        self, mock_get, client, auth_headers, test_app
    ):
        """Successful job search returns 200 with jobs array."""

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_ADZUNA_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get(
            "/api/jobs/search?q=python&location=chennai",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "jobs" in data
        assert "count" in data
        assert "query" in data
        assert "cached" in data
        assert "source" in data
        assert data["query"] == "python"
        assert data["location"] == "chennai"

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_successful_search_jobs_array_structure(
        self, mock_get, client, auth_headers, test_app
    ):
        """Jobs array contains expected fields."""

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_ADZUNA_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get(
            "/api/jobs/search?q=python",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["jobs"]) == 1

        job = data["jobs"][0]
        assert "title" in job
        assert "company" in job
        assert "location" in job
        assert "salary_range" in job
        assert "description" in job
        assert "redirect_url" in job

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_empty_api_results_returns_empty_jobs_array(
        self, mock_get, client, auth_headers, test_app
    ):
        """Empty Adzuna results → empty jobs array."""

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get(
            "/api/jobs/search?q=xyzabcnotexist",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 0
        assert data["jobs"] == []

    def test_missing_credentials_returns_503(
        self, client, auth_headers, test_app
    ):
        """Missing Adzuna credentials → 503."""

        with patch.dict("os.environ", {
            "ADZUNA_APP_ID": "",
            "ADZUNA_APP_KEY": ""
        }):
            response = client.get(
                "/api/jobs/search?q=python",
                headers=auth_headers
            )
            assert response.status_code == 503
            data = response.get_json()
            assert "error" in data

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_external_api_http_error_returns_502(
        self, mock_get, client, auth_headers, test_app
    ):
        """Adzuna HTTP error → 502."""

        import requests as req_lib
        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = req_lib.exceptions.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        response = client.get(
            "/api/jobs/search?q=python",
            headers=auth_headers
        )
        assert response.status_code == 502
        data = response.get_json()
        assert "error" in data

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_external_api_timeout_returns_502(
        self, mock_get, client, auth_headers, test_app
    ):
        """Adzuna timeout → 502."""

        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout()

        response = client.get(
            "/api/jobs/search?q=python",
            headers=auth_headers
        )
        assert response.status_code == 502
        data = response.get_json()
        assert "error" in data

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_api_called_only_once_for_identical_requests(
        self, mock_get, client, auth_headers, test_app
    ):
        """Cache miss on first call, cache hit on second — API called only once."""

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_ADZUNA_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # First request — cache miss, API called
        response1 = client.get(
            "/api/jobs/search?q=uniquecachetest123",
            headers=auth_headers
        )
        assert response1.status_code == 200
        assert response1.get_json()["source"] == "api"
        assert response1.get_json()["cached"] is False

        # Second request — cache hit, API NOT called again
        response2 = client.get(
            "/api/jobs/search?q=uniquecachetest123",
            headers=auth_headers
        )
        assert response2.status_code == 200
        assert response2.get_json()["source"] == "cache"
        assert response2.get_json()["cached"] is True

        # API was called exactly once
        assert mock_get.call_count == 1

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_different_queries_make_separate_api_calls(
        self, mock_get, client, auth_headers, test_app
    ):
        """Different queries create different cache keys → separate API calls."""

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_ADZUNA_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client.get(
            "/api/jobs/search?q=queryA_unique_xkcd",
            headers=auth_headers
        )
        client.get(
            "/api/jobs/search?q=queryB_unique_xkcd",
            headers=auth_headers
        )

        assert mock_get.call_count == 2

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_cache_hit_logged(
        self, mock_get, client, auth_headers, test_app
    ):
        """CACHE HIT is logged on second identical request."""

        import logging

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_ADZUNA_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Populate cache
        client.get(
            "/api/jobs/search?q=cachehittest_unique",
            headers=auth_headers
        )

        with patch(
            "services.job_search_service.logger"
        ) as mock_logger:

            response = client.get(
                "/api/jobs/search?q=cachehittest_unique",
                headers=auth_headers
            )
            assert response.status_code == 200

            log_calls = [
                str(call) for call in mock_logger.info.call_args_list
            ]
            cache_hit_logged = any(
                "CACHE HIT" in call or "cache" in call.lower()
                for call in log_calls
            )
            assert cache_hit_logged, (
                "Expected CACHE HIT log message not found"
            )

    @patch.dict("os.environ", {
        "ADZUNA_APP_ID": "test_id",
        "ADZUNA_APP_KEY": "test_key",
        "ADZUNA_COUNTRY": "in"
    })
    @patch("services.job_search_service.requests.get")
    def test_also_supports_jobs_search_route(
        self, mock_get, client, auth_headers, test_app
    ):
        """GET /jobs/search also works (non-api prefix route)."""

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_ADZUNA_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get(
            "/jobs/search?q=python",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "jobs" in data
