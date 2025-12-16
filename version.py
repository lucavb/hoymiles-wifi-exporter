import importlib.metadata


def get_version() -> str:
    try:
        # setuptools-scm reads version from git tags and makes it available via importlib.metadata
        return importlib.metadata.version("hoymiles-wifi-exporter")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"
