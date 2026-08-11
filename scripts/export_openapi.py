import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api.main import app

def export_openapi():
    openapi_schema = app.openapi()
    docs_dir = Path(__file__).resolve().parents[1] / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    with open(docs_dir / "openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
        
    print(f"OpenAPI spec successfully exported to {docs_dir / 'openapi.json'}")

if __name__ == "__main__":
    export_openapi()
