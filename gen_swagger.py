import json
from fastapi.openapi.utils import get_openapi
from taglyatelle.exposition.taglyatelle_api import app 

openapi_schema = get_openapi(
    title=app.title,
    version=app.version,
    routes=app.routes,
)

with open("docker/swagger.json", "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=4)