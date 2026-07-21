"""Load a validation script by path without making hyphenated folders packages."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def campaign_module(path: str | Path, module_name: str) -> ModuleType:
    module_path = Path(path).resolve()
    specification = importlib.util.spec_from_file_location(module_name, module_path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load campaign module: {module_path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module
