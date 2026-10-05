"""Publish the regenerated research artifacts into the static interface."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
shutil.copytree(root / "research/artifacts", root / "dist/artifacts", dirs_exist_ok=True)
shutil.copy2(root / "research/inference.mjs", root / "dist/inference.mjs")
print("Copied model, metrics, scenario and inference from the research pipeline.")
