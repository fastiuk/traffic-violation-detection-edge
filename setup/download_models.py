#!/usr/bin/env python3
import json, urllib.request, sys
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent
    models_json = repo_root / "configs" / "models.json"
    models_dir = repo_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    with open(models_json) as f:
        models = json.load(f)
        
    for m in models:
        url = m.get("hef_url")
        if not url: continue
        name = m["name"]
        target = m["hailo_target"]
        out_path = models_dir / f"{name}_{target}.hef"
        if out_path.exists():
            print(f"Already exists: {out_path.name}")
            continue
        print(f"Downloading {out_path.name} from {url}...")
        try:
            urllib.request.urlretrieve(url, out_path)
            print("Done.")
        except Exception as e:
            print(f"Failed to download {url}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
