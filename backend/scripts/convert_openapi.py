"""Day 20 helper: Convert the existing Swagger 2.0 document (/swagger.json)
into an OpenAPI 3.0.3 document (openapi.json) for the React/frontend team.

Why: The existing Swagger implementation in app.py is hand-written Swagger 2.0.
We do NOT rewrite that documentation system - we fetch the served document and
normalize it into OpenAPI 3.x, which is the standard most frontend tooling
(openapi-generator, Swagger UI 3.x+, Postman) expects.

Conversion rules applied:
  host + basePath               -> servers[]
  securityDefinitions           -> components.securitySchemes
  definitions                   -> components.schemas
  parameters[] with in: body    -> requestBody
  responses[<code>].schema      -> responses[<code>].content[application/json]
  schema type: file             -> application/octet-stream binary
"""

import json
import urllib.request

SWAGGER_URL = "http://127.0.0.1:5000/swagger.json"
OUTPUT_FILE = "openapi.json"

# Endpoints that exist in the backend (api/health.py, api/jobs.py, api/admin.py)
# but are NOT documented in the hand-written Swagger 2.0 document.
# We document them here so the frozen openapi.json is complete.
JWT_BEARER = [{"BearerAuth": []}]
EXTRA_PATHS = {
    "/api/health": {
        "get": {
            "tags": ["Health"],
            "summary": "Health check",
            "description": "Returns health of the Flask app, PostgreSQL database and Redis cache. No authentication required.",
            "responses": {
                "200": {
                    "description": "Service health status",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "healthy"},
                                    "database": {"type": "string", "example": "healthy"},
                                    "redis": {"type": "string", "example": "healthy"},
                                },
                            }
                        }
                    },
                },
                "500": {"description": "A component is unhealthy"},
            },
        }
    },
    "/api/analytics": {
        "get": {
            "tags": ["Statistics"],
            "summary": "Advanced analytics",
            "description": "Aggregated analytics for the authenticated user (Redis cached 300s). Requires JWT.",
            "security": JWT_BEARER,
            "responses": {
                "200": {"description": "Analytics data", "content": {"application/json": {"schema": {"type": "object"}}}},
                "401": {"description": "Unauthorized - JWT token missing or invalid"},
                "500": {"description": "Internal error"},
            },
        }
    },
    "/api/admin/users": {
        "get": {
            "tags": ["Admin"],
            "summary": "List all users (admin only)",
            "description": "Returns all users with id, name, email, role and is_current_user flag. Requires admin JWT.",
            "security": JWT_BEARER,
            "responses": {
                "200": {
                    "description": "User list",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "count": {"type": "integer"},
                                    "users": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "email": {"type": "string"},
                                                "role": {"type": "string"},
                                                "is_current_user": {"type": "boolean"},
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden - not an admin"},
            },
        }
    },
    "/api/admin/users/{user_id}/impersonate": {
        "post": {
            "tags": ["Admin"],
            "summary": "Impersonate a user (admin only)",
            "description": "Creates an access token for the target user (audited). Admin cannot impersonate themselves.",
            "security": JWT_BEARER,
            "parameters": [
                {"name": "user_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Target user id"}
            ],
            "responses": {
                "200": {
                    "description": "Impersonation token created",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "impersonated_user": {"type": "object"},
                                    "access_token": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "400": {"description": "Admin cannot impersonate themselves"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden - not an admin"},
                "404": {"description": "User not found"},
            },
        }
    },
    "/api/admin/users/{user_id}": {
        "delete": {
            "tags": ["Admin"],
            "summary": "Delete a user (admin only)",
            "description": "Deletes the target user and creates an audit log entry. Admin cannot delete themselves.",
            "security": JWT_BEARER,
            "parameters": [
                {"name": "user_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Target user id"}
            ],
            "responses": {
                "200": {"description": "User deleted successfully"},
                "400": {"description": "Admin cannot delete themselves"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden - not an admin"},
                "404": {"description": "User not found"},
            },
        }
    },
}


def schema_to_oas3(schema):
    """Normalize a Swagger 2.0 schema object into an OpenAPI 3.0 schema."""
    if schema is None:
        return {}
    out = {}
    for key, value in schema.items():
        if key == "$ref":
            # swagger 2.0 ref: "#/definitions/Foo" stays valid in OAS3
            # because we copy definitions into components/schemas with the
            # same names; only the prefix changes.
            out[key] = value.replace("#/definitions/", "#/components/schemas/")
        elif key == "type" and value == "file":
            out["type"] = "string"
            out["format"] = "binary"
        elif key == "items":
            out["items"] = schema_to_oas3(value)
        elif key in ("properties",):
            out[key] = {name: schema_to_oas3(sub) for name, sub in value.items()}
        else:
            out[key] = value
    return out


def convert(swagger):
    doc = {
        "openapi": "3.0.3",
        "info": swagger.get("info", {"title": "Job Application Tracker API", "version": "1.0.0"}),
        "servers": [
            {"url": f"http://{swagger.get('host', '127.0.0.1:5000')}{swagger.get('basePath', '/')}".rstrip("/")}
        ],
        "tags": swagger.get("tags", []),
        "paths": {},
    }

    # ---- paths / operations ----
    for path, methods in swagger.get("paths", {}).items():
        doc["paths"][path] = {}
        for method, op in methods.items():
            if method == "parameters":
                # path-level parameters are kept as-is (non-body)
                doc["paths"][path] = {"parameters": [schema_to_oas3_fix_param(p) for p in op]}
                continue
            new_op = {
                k: op[k] for k in ("tags", "summary", "description", "operationId", "deprecated") if k in op
            }
            params, request_body = [], None
            for param in op.get("parameters", []):
                if param.get("in") == "body":
                    request_body = {
                        "required": param.get("required", False),
                        "content": {
                            "application/json": {"schema": schema_to_oas3(param.get("schema", {}))}
                        },
                    }
                    if param.get("description"):
                        request_body["description"] = param["description"]
                elif param.get("in") == "formData":
                    # formData -> multipart request body (import/file endpoints)
                    content_key = (
                        "application/octet-stream"
                        if param.get("type") == "file"
                        else "application/x-www-form-urlencoded"
                    )
                    prop = {
                        "in": "formData",
                        "name": param.get("name"),
                        "description": param.get("description", ""),
                        "required": param.get("required", False),
                    }
                    if param.get("type") == "file":
                        prop["schema"] = {"type": "string", "format": "binary"}
                    elif param.get("type"):
                        prop["schema"] = {"type": param["type"]}
                    else:
                        prop["schema"] = {}
                    request_body = request_body or {
                        "required": False,
                        "content": {content_key: {"schema": {"type": "object", "properties": {}}}},
                    }
                    body_schema = next(iter(request_body["content"].values()))["schema"]
                    body_schema.setdefault("properties", {})[param.get("name", "")] = prop["schema"]
                    if prop["required"]:
                        body_schema.setdefault("required", []).append(prop["name"])
                        request_body["required"] = True
                else:
                    params.append(schema_to_oas3_fix_param(param))
            if params:
                new_op["parameters"] = params
            if request_body:
                new_op["requestBody"] = request_body

            # responses
            responses = {}
            for code, resp in op.get("responses", {}).items():
                new_resp = {"description": resp.get("description", "")}
                if "schema" in resp:
                    entry = schema_to_oas3(resp["schema"])
                    if entry.get("format") == "binary" or entry.get("type") == "string" and entry.get("format") == "binary":
                        new_resp["content"] = {"application/octet-stream": {"schema": entry}}
                    else:
                        new_resp["content"] = {"application/json": {"schema": entry}}
                if "headers" in resp:
                    new_resp["headers"] = resp["headers"]
                responses[code] = new_resp
            new_op["responses"] = responses or {"200": {"description": "OK"}}

            if "security" in op:
                new_op["security"] = op["security"]
            doc["paths"][path][method] = new_op

    # ---- security schemes ----
    sec_defs = swagger.get("securityDefinitions", {})
    if sec_defs:
        doc["components"] = {"securitySchemes": sec_defs}

    # ---- reusable definitions ----
    definitions = swagger.get("definitions", {})
    if definitions:
        doc.setdefault("components", {})
        doc["components"]["schemas"] = {
            name: schema_to_oas3(s) for name, s in definitions.items()
        }

    if "security" in swagger:
        doc["security"] = swagger["security"]

    # ---- add endpoints missing from the Swagger 2.0 document ----
    for path, methods in EXTRA_PATHS.items():
        if path not in doc["paths"]:
            doc["paths"][path] = methods

    return doc


def schema_to_oas3_fix_param(param):
    """Fix non-body parameters: type stays, 'schema' (rare in swagger2 params) normalized."""
    out = dict(param)
    if "schema" in out and isinstance(out["schema"], dict):
        out["schema"] = schema_to_oas3(out["schema"])
    return out


def main():
    with urllib.request.urlopen(SWAGGER_URL, timeout=15) as response:
        swagger = json.loads(response.read().decode("utf-8"))

    openapi_doc = convert(swagger)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(openapi_doc, fh, indent=2)

    n_paths = len(openapi_doc["paths"])
    n_ops = sum(len(v) for v in openapi_doc["paths"].values())
    print(f"openapi.json written: {n_paths} paths, {n_ops} operations")
    print(f"OpenAPI version: {openapi_doc['openapi']}")


if __name__ == "__main__":
    main()
