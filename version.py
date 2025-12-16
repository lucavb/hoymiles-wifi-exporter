import importlib.metadata
import tomllib
from pathlib import Path


def get_version() -> str:
    try:
        # Works when package is installed (production/container)
        return importlib.metadata.version("hoymiles-wifi-exporter")
    except importlib.metadata.PackageNotFoundError:
        # Fallback for development (running from source)
        try:
            pyproject_path = Path(__file__).parent / "pyproject.toml"
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
            version = pyproject.get("project", {}).get("version", "unknown")
            return f"{version}-dev"
        except Exception:
            return "unknown"
