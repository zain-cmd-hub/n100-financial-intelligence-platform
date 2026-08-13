import os
import shutil
from pathlib import Path

def copy_if_exists(src, dst):
    if os.path.exists(src):
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        print(f"Copied {src} to {dst}")
    else:
        print(f"Warning: {src} does not exist.")

def archive():
    dest_dir = Path("output/final_deliverables")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    deliverables = [
        "output/cluster_labels.csv",
        "reports/elbow_plot.png",
        "reports/correlation_heatmap.png",
        "output/outlier_report.csv",
        "output/portfolio_stats.csv",
        "src/api",
        "docs/openapi.json",
        "reports/pytest_report.html",
        "docs/analyst_guide.pdf",
        "docs/acceptance_checklist.pdf",
        "output/final_deliverables/acceptance_results.md"
    ]
    
    for item in deliverables:
        item_path = Path(item)
        if item_path.name == "acceptance_results.md":
            continue
        copy_if_exists(str(item_path), str(dest_dir / item_path.name))

if __name__ == "__main__":
    archive()
