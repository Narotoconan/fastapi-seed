from __future__ import annotations

import ast
import hashlib
import os
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASELINE_ROOT = REPOSITORY_ROOT / "docs" / "baselines"
DATA_ROOT = Path(__file__).parent / "data"

IDENTITY_KEYS = frozenset(
    {
        "project_name",
        "project_title",
        "project_description",
        "project_version",
        "redis_prefix",
    }
)
ANSWER_METADATA_KEYS = frozenset({"_src_path", "_commit"})


@dataclass(frozen=True)
class GeneratedProject:
    name: str
    path: Path
    answers: dict[str, str]
    data: dict[str, str]


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, (
        f"command failed ({result.returncode}): {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    return result


def _load_yaml(path: Path) -> dict[str, str]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _relative_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def _expected_output_files() -> set[str]:
    baseline = {
        line.removeprefix("template/")
        for line in (BASELINE_ROOT / "template-files.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    }
    return baseline | {".copier-answers.yml"}


def _render_whitelist() -> set[str]:
    return {
        line.removeprefix("template/")
        for line in (BASELINE_ROOT / "template-render-whitelist.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    }


@pytest.fixture(scope="session")
def generated_projects(tmp_path_factory: pytest.TempPathFactory) -> dict[str, GeneratedProject]:
    git = shutil.which("git")
    copier = shutil.which("copier")
    assert git is not None, "Git is required by the template copy gate"
    assert copier is not None, "Copier is required by the template copy gate"

    source = tmp_path_factory.mktemp("template-source")
    shutil.copy2(REPOSITORY_ROOT / "copier.yml", source / "copier.yml")
    shutil.copytree(REPOSITORY_ROOT / "template", source / "template")

    _run([git, "init", "--quiet"], cwd=source)
    git_options = [
        git,
        "-c",
        "core.autocrlf=false",
        "-c",
        "user.name=Template Gate",
        "-c",
        "user.email=template-gate@example.invalid",
        "-c",
        "commit.gpgsign=false",
    ]
    _run([*git_options, "add", "-f", "--", "copier.yml", "template"], cwd=source)
    _run([*git_options, "commit", "--quiet", "-m", "test template snapshot"], cwd=source)

    output_root = tmp_path_factory.mktemp("generated-projects")
    copy_environment = os.environ.copy()
    copy_environment["GIT_CONFIG_COUNT"] = "1"
    copy_environment["GIT_CONFIG_KEY_0"] = "core.autocrlf"
    copy_environment["GIT_CONFIG_VALUE_0"] = "false"
    projects: dict[str, GeneratedProject] = {}
    for case_name in ("default", "custom"):
        data_path = DATA_ROOT / f"{case_name}.yml"
        destination = output_root / case_name
        command = [
            copier,
            "copy",
            "--defaults",
            "--vcs-ref=HEAD",
        ]
        if case_name == "custom":
            command.extend(["--data-file", str(data_path)])
        command.extend([str(source), str(destination)])
        assert "--trust" not in command
        _run(command, cwd=REPOSITORY_ROOT, env=copy_environment)

        answers = _load_yaml(destination / ".copier-answers.yml")
        projects[case_name] = GeneratedProject(
            name=case_name,
            path=destination,
            answers=answers,
            data=_load_yaml(data_path),
        )

    return projects


@pytest.mark.parametrize("case_name", ["default", "custom"])
def test_copy_matches_manifest_and_answers(
    generated_projects: dict[str, GeneratedProject],
    case_name: str,
) -> None:
    project = generated_projects[case_name]
    actual_files = _relative_files(project.path)

    assert actual_files == _expected_output_files()
    assert len(actual_files) == 77
    assert set(project.answers) == IDENTITY_KEYS | ANSWER_METADATA_KEYS
    assert {key: project.answers[key] for key in IDENTITY_KEYS} == project.data
    assert project.answers["_src_path"]
    assert project.answers["_commit"]

    assert not (project.path / "tests").exists()
    assert not (project.path / ".github" / "workflows").exists()
    assert not (project.path / "alembic.ini").exists()
    assert not any("alembic" in part.lower() for path in actual_files for part in Path(path).parts)
    assert "copier.yml" not in actual_files
    assert not any(path.startswith("docs/") for path in actual_files)


@pytest.mark.parametrize("case_name", ["default", "custom"])
def test_static_files_have_zero_drift(
    generated_projects: dict[str, GeneratedProject],
    case_name: str,
) -> None:
    project = generated_projects[case_name]
    hash_lines = (BASELINE_ROOT / "template-static.sha256").read_text(encoding="utf-8").splitlines()
    assert len(hash_lines) == 66

    for line in hash_lines:
        expected_hash, template_path = line.split("  ", maxsplit=1)
        output_path = project.path / template_path.removeprefix("template/")
        actual_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, template_path


@pytest.mark.parametrize("case_name", ["default", "custom"])
def test_generated_files_parse_without_jinja_residue(
    generated_projects: dict[str, GeneratedProject],
    case_name: str,
) -> None:
    project = generated_projects[case_name]
    files = [path for path in project.path.rglob("*") if path.is_file()]

    for path in files:
        assert path.suffix != ".jinja", path
        text = path.read_text(encoding="utf-8")
        assert "{{" not in text, path
        assert "{%" not in text, path

    python_files = list(project.path.rglob("*.py"))
    toml_files = list(project.path.rglob("*.toml"))
    yaml_files = [*project.path.rglob("*.yaml"), *project.path.rglob("*.yml")]
    assert (len(python_files), len(toml_files), len(yaml_files)) == (51, 2, 3)

    for path in python_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in toml_files:
        tomllib.loads(path.read_text(encoding="utf-8"))
    for path in yaml_files:
        list(yaml.safe_load_all(path.read_text(encoding="utf-8")))

    main_source = (project.path / "main.py").read_text(encoding="utf-8")
    assert "from config.settings import get_settings" in main_source
    assert "from app.api import register_router" in main_source
    assert "app = FastAPI(" in main_source
    assert (project.path / "app" / "__init__.py").is_file()
    assert (project.path / "config" / "__init__.py").is_file()


def test_custom_identity_changes_only_render_whitelist(
    generated_projects: dict[str, GeneratedProject],
) -> None:
    default = generated_projects["default"]
    custom = generated_projects["custom"]
    changed_files = {
        relative_path
        for relative_path in _expected_output_files()
        if (default.path / relative_path).read_bytes() != (custom.path / relative_path).read_bytes()
    }
    assert changed_files == _render_whitelist() | {".copier-answers.yml"}

    default_project = tomllib.loads((default.path / "pyproject.toml").read_text(encoding="utf-8"))
    custom_project = tomllib.loads((custom.path / "pyproject.toml").read_text(encoding="utf-8"))
    assert custom_project["project"]["name"] == custom.data["project_name"]
    assert custom_project["project"]["version"] == custom.data["project_version"]
    assert custom_project["project"]["description"] == custom.data["project_description"]
    assert custom_project["project"]["dependencies"] == default_project["project"]["dependencies"]
    assert custom_project["dependency-groups"] == default_project["dependency-groups"]

    compose = yaml.safe_load((custom.path / "compose.yaml").read_text(encoding="utf-8"))
    assert compose["name"] == "order-service"
    assert compose["services"]["api"]["image"] == "order-service:local"

    expected_markers = {
        "README.md": ("# Order Service", custom.data["project_description"], "order-service/", "`order`"),
        ".env.example": ('REDIS_PREFIX="order"',),
        ".env.docker.example": ('# REDIS_PREFIX="order"',),
        "config/app_config.py": ('"order-service", "0.1.0"',),
        "config/cache_config.py": ('REDIS_PREFIX: str = "order"',),
        "app/core/cache/prefixes.py": ("order:user:profile:1", "order:order:pending:O001"),
        "app/core/cache/redis.py": ('"__fastapi_order_cache__:v1:"',),
        "app/core/cache/README.md": ("`REDIS_PREFIX=order`", "order:user:1"),
    }
    for relative_path, markers in expected_markers.items():
        rendered = (custom.path / relative_path).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in rendered, (relative_path, marker)

    whitelist_text = "\n".join(
        (custom.path / relative_path).read_text(encoding="utf-8")
        for relative_path in sorted(_render_whitelist())
    )
    for default_marker in (
        "fastapi-template",
        "FastAPI Template",
        "REDIS_PREFIX=template",
        "__fastapi_template_cache__",
        "template:user:1",
    ):
        assert default_marker not in whitelist_text


def test_default_identity_preserves_fixed_identifiers(
    generated_projects: dict[str, GeneratedProject],
) -> None:
    default = generated_projects["default"]
    project_metadata = tomllib.loads((default.path / "pyproject.toml").read_text(encoding="utf-8"))
    assert project_metadata["project"]["name"] == "fastapi-template"
    assert project_metadata["project"]["version"] == "0.1.0"
    assert project_metadata["project"]["description"] == default.data["project_description"]

    compose = yaml.safe_load((default.path / "compose.yaml").read_text(encoding="utf-8"))
    assert compose["name"] == "fastapi-template"
    assert compose["services"]["api"]["image"] == "fastapi-template:local"

    expected_markers = {
        "README.md": ("# FastAPI Template", default.data["project_description"], "fastapi-template/", "`template`"),
        ".env.example": ('REDIS_PREFIX="template"',),
        ".env.docker.example": ('# REDIS_PREFIX="template"',),
        "config/app_config.py": ('"fastapi-template", "0.1.0"',),
        "config/cache_config.py": ('REDIS_PREFIX: str = "template"',),
        "app/core/cache/prefixes.py": ("template:user:profile:1",),
        "app/core/cache/redis.py": ('"__fastapi_template_cache__:v1:"',),
        "app/core/cache/README.md": ("`REDIS_PREFIX=template`", "template:user:1"),
    }
    for relative_path, markers in expected_markers.items():
        rendered = (default.path / relative_path).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in rendered, (relative_path, marker)


def test_default_lock_is_current(
    generated_projects: dict[str, GeneratedProject],
    tmp_path: Path,
) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "uv is required by the template copy gate"
    env = os.environ.copy()
    env["UV_CACHE_DIR"] = str(tmp_path / "uv-cache")
    env["UV_OFFLINE"] = "1"
    _run([uv, "lock", "--check"], cwd=generated_projects["default"].path, env=env)
