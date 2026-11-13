import json
from app.main import app

openapi = app.openapi()
print(f"=== {openapi['info']['title']} v{openapi['info']['version']} ===")
print(f"Total endpoints registered: {len(openapi['paths'])}\n")

for path, methods in sorted(openapi["paths"].items()):
    for method, details in sorted(methods.items()):
        summary = details.get("summary", "")
        tags = ",".join(details.get("tags", []))
        print(f"{method.upper():<7} {path:<38} [{tags}] {summary}")
