# Changelog

All notable changes to the Job Application Tracker API are documented in this file.

## [2.0.0] - 2026-09-18

### Added
- Added API versioning with `/api/v1/` and `/api/v2/` prefixes.
- Added V2 application listing endpoint.
- Added `?format=summary` support for compact V2 application responses.
- Added `Deprecation: true` response header for V1 API endpoints.

### Changed
- V2 API provides the current versioned API structure while existing unversioned endpoints remain available for backward compatibility.

### Deprecated
- V1 API endpoints are marked as deprecated and should be migrated to V2.

## [1.0.0] - 2026-09-18

### Existing API
- Initial application tracking API functionality.
- Application creation, listing, updating, deletion, search, filtering and pagination.