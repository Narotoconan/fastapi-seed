from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CUSTOM_DATA = REPOSITORY_ROOT / "tests" / "data" / "custom.yml"

V1_TAG = "v0.1.0"
V2_TAG = "v0.2.0"
V2_ONLY_MARKER = "> stage5 recopy must not select v0.2.0"
DRIFT_MARKER = "stage5-recopy-managed-file-drift"

IDENTITY_KEYS = frozenset(
    {
        "project_name",
        "project_title",
        "project_description",
        "project_version",
        "redis_prefix",
    }
)


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


def _git(git: str, repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            git,
            "-c",
            "core.autocrlf=false",
            "-c",
            "user.name=Template Gate",
            "-c",
            "user.email=template-gate@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *arguments,
        ],
        cwd=repository,
    )


def _copier_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_CONFIG_COUNT"] = "1"
    environment["GIT_CONFIG_KEY_0"] = "core.autocrlf"
    environment["GIT_CONFIG_VALUE_0"] = "false"
    return environment


def _load_yaml(path: Path) -> dict[str, str]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _tree_snapshot(project: Path) -> dict[str, str]:
    return {
        path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in project.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(project).parts
    }


def _assert_no_conflicts(project: Path) -> None:
    assert not list(project.rglob("*.rej"))
    for path in project.rglob("*"):
        if not path.is_file() or ".git" in path.relative_to(project).parts:
            continue
        for line in path.read_bytes().splitlines():
            assert not line.startswith(b"<<<<<<< "), path
            assert line != b"=======", path
            assert not line.startswith(b">>>>>>> "), path


def _create_versioned_template(source: Path, git: str) -> None:
    shutil.copy2(REPOSITORY_ROOT / "copier.yml", source / "copier.yml")
    shutil.copytree(REPOSITORY_ROOT / "template", source / "template")
    _git(git, source, "init", "--quiet")
    _git(git, source, "add", "-f", "--", "copier.yml", "template")
    _git(git, source, "commit", "--quiet", "-m", "template v0.1.0")
    _git(git, source, "tag", V1_TAG)

    readme = source / "template" / "README.md.jinja"
    readme.write_bytes(readme.read_bytes() + f"\n{V2_ONLY_MARKER}\n".encode())
    _git(git, source, "add", "--", "template/README.md.jinja")
    _git(git, source, "commit", "--quiet", "-m", "template v0.2.0")
    _git(git, source, "tag", V2_TAG)


def test_same_version_recopy_is_idempotent_and_restores_managed_files(tmp_path: Path) -> None:
    git = shutil.which("git")
    copier = shutil.which("copier")
    assert git is not None, "Git is required by the recopy gate"
    assert copier is not None, "Copier is required by the recopy gate"

    documentation = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    assert "copier recopy --vcs-ref=:current:" in documentation
    assert "可能覆盖模板管理文件中的用户改动" in documentation
    assert "日常升级应优先使用 `copier update`" in documentation

    source = tmp_path / "template-source"
    source.mkdir()
    project = tmp_path / "generated-project"
    environment = _copier_environment()
    _create_versioned_template(source, git)

    copy_command = [
        copier,
        "copy",
        "--defaults",
        "--data-file",
        str(CUSTOM_DATA),
        f"--vcs-ref={V1_TAG}",
        str(source.resolve()),
        str(project),
    ]
    assert "--trust" not in copy_command
    _run(copy_command, cwd=REPOSITORY_ROOT, env=environment)
    _git(git, project, "init", "--quiet")
    _git(git, project, "add", "-A")
    _git(git, project, "commit", "--quiet", "-m", "generate from v0.1.0")

    answers_path = project / ".copier-answers.yml"
    answers_before = answers_path.read_bytes()
    answers_data = _load_yaml(answers_path)
    assert answers_data["_commit"] == V1_TAG
    baseline = _tree_snapshot(project)
    assert V2_ONLY_MARKER not in (project / "README.md").read_text(encoding="utf-8")
    assert not _git(git, project, "status", "--porcelain").stdout.strip()

    recopy_command = [
        copier,
        "recopy",
        "--vcs-ref=:current:",
        "--skip-answered",
        "--overwrite",
    ]
    assert "--trust" not in recopy_command
    _run(recopy_command, cwd=project, env=environment)

    assert _tree_snapshot(project) == baseline
    assert answers_path.read_bytes() == answers_before
    assert _load_yaml(answers_path) == answers_data
    assert {key: _load_yaml(answers_path)[key] for key in IDENTITY_KEYS} == {
        key: answers_data[key] for key in IDENTITY_KEYS
    }
    assert _load_yaml(answers_path)["_commit"] == V1_TAG
    assert V2_ONLY_MARKER not in (project / "README.md").read_text(encoding="utf-8")
    assert not _git(git, project, "status", "--porcelain").stdout.strip()

    readme = project / "README.md"
    original_readme = readme.read_bytes()
    readme.write_bytes(original_readme + f"\n{DRIFT_MARKER}\n".encode())
    assert DRIFT_MARKER in readme.read_text(encoding="utf-8")
    assert _tree_snapshot(project) != baseline
    assert _git(git, project, "status", "--porcelain").stdout.strip() == "M README.md"

    _run(recopy_command, cwd=project, env=environment)
    assert readme.read_bytes() == original_readme
    assert _tree_snapshot(project) == baseline
    assert answers_path.read_bytes() == answers_before
    assert _load_yaml(answers_path) == answers_data
    assert not _git(git, project, "status", "--porcelain").stdout.strip()
    assert not _git(git, project, "ls-files", "--unmerged").stdout.strip()
    _git(git, project, "diff", "--check")
    _assert_no_conflicts(project)
