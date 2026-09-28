# Migration Guide: API V1 to V2

## Overview

The Job Application Tracker API supports both V1 and V2 so existing clients can continue using the API while migrating to the newer version.

V1 endpoints are deprecated and include the following response header:

`Deprecation: true`

New integrations should use the V2 API.

---

## 1. Change the Base URL

### V1

`/api/v1/`

### V2

`/api/v2/`

Example:

V1:
`GET /api/v1/applications`

V2:
`GET /api/v2/applications`

---

## 2. Application Listing

The application listing endpoint is available in both versions.

### V1

```text
GET /api/v1/applications