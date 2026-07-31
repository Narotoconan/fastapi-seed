from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CUSTOM_DATA = REPOSITORY_ROOT / "tests" / "data" / "custom.yml"

V1_TAG = "v0.1.0"
V2_TAG = "v0.2.0"
TEMPLATE_V2_MARKER = "> stage5 template v0.2.0 marker"
USER_README_TITLE = "# Order Service (user note)"
USER_DB_HOST = "DB_HOST=db.user.internal"
USER_FILE = "app/services/user_owned.py"
USER_FILE_CONTENT = '''"""Downstream-owned business module."""\n\nUSER_OWNED = True\n'''

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


def _write_lf(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def _project_files(project: Path) -> set[str]:
    return {
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(project).parts
    }


def _assert_no_conflicts(project: Path, git: str) -> None:
    assert not list(project.rglob("*.rej"))
    assert not _git(git, project, "ls-files", "--unmerged").stdout.strip()
    _git(git, project, "diff", "--check")

    for path in project.rglob("*"):
        if not path.is_file() or ".git" in path.relative_to(project).parts:
            continue
        for line in path.read_bytes().splitlines():
            assert not line.startswith(b"<<<<<<< "), path
            assert line != b"=======", path
            assert not line.startswith(b">>>>>>> "), path


def _create_v1_template(source: Path, git: str) -> None:
    shutil.copy2(REPOSITORY_ROOT / "copier.yml", source / "copier.yml")
    shutil.copytree(REPOSITORY_ROOT / "template", source / "template")
    _git(git, source, "init", "--quiet")
    _git(git, source, "add", "-f", "--", "copier.yml", "template")
    _git(git, source, "commit", "--quiet", "-m", "template v0.1.0")
    _git(git, source, "tag", V1_TAG)


def _publish_v2_template(source: Path, git: str) -> None:
    readme = source / "template" / "README.md.jinja"
    original = readme.read_bytes()
    marker = f"\n{TEMPLATE_V2_MARKER}\n".encode()
    assert marker not in original
    readme.write_bytes(original + marker)
    _git(git, source, "add", "--", "template/README.md.jinja")
    _git(git, source, "commit", "--quiet", "-m", "template v0.2.0")
    _git(git, source, "tag", V2_TAG)


def test_update_preserves_user_evolution_and_advances_answers(tmp_path: Path) -> None:
    git = shutil.which("git")
    copier = shutil.which("copier")
    assert git is not None, "Git is required by the update gate"
    assert copier is not None, "Copier is required by the update gate"

    source = tmp_path / "template-source"
    source.mkdir()
    project = tmp_path / "generated-project"
    environment = _copier_environment()
    _create_v1_template(source, git)

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

    v1_answers = _load_yaml(project / ".copier-answers.yml")
    assert v1_answers["_commit"] == V1_TAG
    _git(git, project, "init", "--quiet")
    _git(git, project, "add", "-A")
    _git(git, project, "commit", "--quiet", "-m", "generate from v0.1.0")

    readme = project / "README.md"
    readme_content = readme.read_text(encoding="utf-8")
    assert readme_content.startswith("# Order Service\n")
    _write_lf(readme, readme_content.replace("# Order Service", USER_README_TITLE, 1))

    environment_example = project / ".env.example"
    environment_content = environment_example.read_text(encoding="utf-8")
    assert "DB_HOST=localhost" in environment_content
    _write_lf(environment_example, environment_content.replace("DB_HOST=localhost", USER_DB_HOST, 1))

    user_file = project / USER_FILE
    user_file.parent.mkdir(parents=True, exist_ok=True)
    _write_lf(user_file, USER_FILE_CONTENT)
    _git(git, project, "add", "-A")
    _git(git, project, "commit", "--quiet", "-m", "downstream user changes")
    _git(git, project, "switch", "--quiet", "-c", "chore/copier-update")
    assert not _git(git, project, "status", "--porcelain").stdout.strip()

    files_before_update = _project_files(project)
    assert len(files_before_update) == 78
    _publish_v2_template(source, git)

    update_command = [
        copier,
        "update",
        "--defaults",
        "--conflict=inline",
        f"--vcs-ref={V2_TAG}",
        str(project),
    ]
    assert "--trust" not in update_command
    _run(update_command, cwd=REPOSITORY_ROOT, env=environment)

    updated_readme = readme.read_text(encoding="utf-8")
    assert updated_readme.startswith(f"{USER_README_TITLE}\n")
    assert TEMPLATE_V2_MARKER in updated_readme
    assert USER_DB_HOST in environment_example.read_text(encoding="utf-8")
    assert user_file.read_text(encoding="utf-8") == USER_FILE_CONTENT
    assert _project_files(project) == files_before_update

    v2_answers = _load_yaml(project / ".copier-answers.yml")
    assert {key: v2_answers[key] for key in IDENTITY_KEYS} == {
        key: v1_answers[key] for key in IDENTITY_KEYS
    }
    assert v2_answers["_src_path"] == v1_answers["_src_path"]
    assert v2_answers["_commit"] == V2_TAG

    actual_files = _project_files(project)
    assert "copier.yml" not in actual_files
    assert not any(path.startswith("docs/") for path in actual_files)
    assert not any(path.startswith("tests/") for path in actual_files)
    assert not any(path.startswith(".github/workflows/") for path in actual_files)
    assert not any("alembic" in part.lower() for path in actual_files for part in Path(path).parts)
    _assert_no_conflicts(project, git)
