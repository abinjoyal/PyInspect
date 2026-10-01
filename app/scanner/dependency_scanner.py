"""Dependency parser for requirements.txt and pyproject.toml."""

import sys
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from app.core.logger import get_logger

logger = get_logger("dependency_scanner")


@dataclass
class DependencyInfo:
    name: str
    specifier: str = ""
    source: str = ""  # requirements.txt, pyproject.toml


class DependencyScanner:
    """Parses project dependency declarations."""

    @staticmethod
    def scan_dependencies(project_dir: Path) -> List[DependencyInfo]:
        dependencies: List[DependencyInfo] = []

        # Check requirements.txt
        req_file = project_dir / "requirements.txt"
        if req_file.is_file():
            dependencies.extend(DependencyScanner.parse_requirements_txt(req_file))

        # Check pyproject.toml
        toml_file = project_dir / "pyproject.toml"
        if toml_file.is_file():
            dependencies.extend(DependencyScanner.parse_pyproject_toml(toml_file))

        return dependencies

    @staticmethod
    def parse_requirements_txt(req_path: Path) -> List[DependencyInfo]:
        results = []
        try:
            with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    # Match name and version specifier
                    match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", line)
                    if match:
                        name, spec = match.groups()
                        results.append(
                            DependencyInfo(
                                name=name.strip(),
                                specifier=spec.strip(),
                                source="requirements.txt"
                            )
                        )
        except Exception as e:
            logger.warning(f"Error reading requirements.txt: {e}")
        return results

    @staticmethod
    def parse_pyproject_toml(toml_path: Path) -> List[DependencyInfo]:
        results = []
        try:
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)

            project_deps = data.get("project", {}).get("dependencies", [])
            for dep in project_deps:
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", dep)
                if match:
                    name, spec = match.groups()
                    results.append(
                        DependencyInfo(
                            name=name.strip(),
                            specifier=spec.strip(),
                            source="pyproject.toml"
                        )
                    )
        except Exception as e:
            logger.warning(f"Error reading pyproject.toml: {e}")
        return results
