# URL Download and Save Example

This example demonstrates the new `--save-as` functionality that allows you to download OpenAPI specifications from URLs and save them locally for future use.

## Basic URL Download with Local Save

```bash
# Download and save Swagger Petstore API
api-agent ingest --url https://petstore.swagger.io/v2/swagger.json --save-as ./specs/petstore.json

# Download and save a different API spec
api-agent ingest --url https://api.github.com/swagger.json --save-as ./specs/github-api.json
```

## Workflow Examples

### 1. Development Workflow
```bash
# Download production API spec for local development
api-agent ingest \
  --url https://prod-api.company.com/v1/openapi.json \
  --save-as ./specs/prod-api-v1.json \
  --env production

# Later, work with the saved spec locally
api-agent ingest --file ./specs/prod-api-v1.json --env development
```

### 2. API Documentation Archive
```bash
# Create a local archive of API specifications
mkdir -p ./api-specs/

# Save multiple API versions
api-agent ingest --url https://api.example.com/v1/openapi.json --save-as ./api-specs/example-v1.json
api-agent ingest --url https://api.example.com/v2/openapi.json --save-as ./api-specs/example-v2.json
api-agent ingest --url https://api.example.com/v3/openapi.json --save-as ./api-specs/example-v3.json
```

### 3. Offline Development
```bash
# Download specs when you have internet connectivity
api-agent ingest --url https://api.service.com/openapi.json --save-as ./offline-specs/service.json

# Later, work offline with the saved spec
api-agent ingest --file ./offline-specs/service.json
api-agent list-tools
api-agent run-tests --output ./test-results.json
```

## Output Examples

### Successful Download and Save
```
Ingesting OpenAPI specification...
Loading from URL: https://petstore.swagger.io/v2/swagger.json
Saving spec to local file: ./specs/petstore.json
✓ Spec saved to ./specs/petstore.json
Successfully ingested API specification!
API Title: Swagger Petstore
API Version: 1.0.7
Environment: dev
Tools extracted: 11
```

### Warning When Using --save-as with --file
```bash
api-agent ingest --file ./local-spec.json --save-as ./copy.json
```

Output:
```
Ingesting OpenAPI specification...
Loading from file: ./local-spec.json
Warning: --save-as option ignored when using --file
Successfully ingested API specification!
...
```

## File Format

Saved files are always in JSON format with proper indentation for readability:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Example API",
    "version": "1.0.0"
  },
  "paths": {
    "/users": {
      "get": {
        "operationId": "getUsers",
        "responses": {
          "200": {
            "description": "List of users"
          }
        }
      }
    }
  }
}
```

## Error Handling

### Invalid URL
```bash
api-agent ingest --url https://invalid-url.com/api.json --save-as ./specs/invalid.json
```

The tool will show an error message and no file will be created.

### Permission Issues
If you don't have write permissions to the target directory:

```bash
api-agent ingest --url https://api.example.com/openapi.json --save-as /root/restricted.json
```

The tool will show a permission error and the file won't be saved.

### Network Issues
If the URL is unreachable or returns an error:

```bash
api-agent ingest --url https://down-api.example.com/openapi.json --save-as ./specs/down.json
```

The tool will show the network error and no file will be created.

## Integration with Other Commands

After saving a spec locally, you can use it with all other commands:

```bash
# Save the spec
api-agent ingest --url https://api.example.com/openapi.json --save-as ./my-api.json

# Work with the saved spec
api-agent ingest --file ./my-api.json
api-agent list-tools
api-agent call --tool get_users --data '{}'
api-agent run-tests --tool create_user
api-agent serve --port 8000
```

This workflow is particularly useful for:
- Offline development
- Version control of API specifications
- Backup and archival purposes
- Working with multiple API versions
- Sharing API specs with team members
