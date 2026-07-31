from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined, meta


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASELINE_ROOT = REPOSITORY_ROOT / "docs" / "baselines"

IDENTITY_KEYS = frozenset(
    {
        "project_name",
        "project_title",
        "project_description",
        "project_version",
        "redis_prefix",
    }
)
MESSAGE_KEYS = (
    "_message_before_copy",
    "_message_after_copy",
    "_message_before_update",
    "_message_after_update",
)
FORBIDDEN_CONFIG_KEYS = frozenset(
    {
        "_tasks",
        "_migrations",
        "_jinja_extensions",
        "_external_data",
    }
)

ALLOWED_TEMPLATE_VARIABLES = {
    ".env.docker.example": {"redis_prefix"},
    ".env.example": {"redis_prefix"},
    "app/core/cache/prefixes.py": {"redis_prefix"},
    "app/core/cache/README.md": {"redis_prefix"},
    "app/core/cache/redis.py": {"redis_prefix"},
    "compose.yaml": {"project_name"},
    "config/app_config.py": {"project_name", "project_version"},
    "config/cache_config.py": {"redis_prefix"},
    "pyproject.toml": {"project_description", "project_name", "project_version"},
    "README.md": {"project_description", "project_name", "project_title", "redis_prefix"},
}


def _load_yaml(path: Path) -> dict[str, object]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _jinja_environment() -> Environment:
    environment = Environment(undefined=StrictUndefined)
    environment.filters["to_json"] = lambda value, **_: value
    environment.filters["to_nice_yaml"] = lambda value, **_: value
    return environment


def test_render_whitelist_and_allowed_variables_are_exact() -> None:
    whitelist = {
        line.removeprefix("template/")
        for line in (BASELINE_ROOT / "template-render-whitelist.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    }
    assert whitelist == set(ALLOWED_TEMPLATE_VARIABLES)
    assert len(whitelist) == 10

    expected_templates = {f"{path}.jinja" for path in whitelist}
    answers_template = "{{ _copier_conf.answers_file }}.jinja"
    actual_templates = {
        path.relative_to(REPOSITORY_ROOT / "template").as_posix()
        for path in (REPOSITORY_ROOT / "template").rglob("*.jinja")
    }
    assert actual_templates == expected_templates | {answers_template}

    environment = _jinja_environment()
    used_variables: set[str] = set()
    for output_path, allowed_variables in ALLOWED_TEMPLATE_VARIABLES.items():
        template_path = REPOSITORY_ROOT / "template" / f"{output_path}.jinja"
        source = template_path.read_text(encoding="utf-8")
        parsed = environment.parse(source)
        actual_variables = meta.find_undeclared_variables(parsed)
        assert actual_variables == allowed_variables, output_path
        used_variables.update(actual_variables)

        if output_path.endswith(".py"):
            assert "{%" not in source, output_path

    assert used_variables == IDENTITY_KEYS

    answers_source = (REPOSITORY_ROOT / "template" / answers_template).read_text(encoding="utf-8")
    answers_variables = meta.find_undeclared_variables(environment.parse(answers_source))
    assert answers_variables == {"_copier_answers"}


def test_copier_control_plane_stays_safe_and_minimal() -> None:
    configuration = _load_yaml(REPOSITORY_ROOT / "copier.yml")
    public_questions = {key for key in configuration if not key.startswith("_")}

    assert public_questions == IDENTITY_KEYS
    assert configuration["_subdirectory"] == "template"
    assert configuration["_templates_suffix"] == ".jinja"
    assert configuration["_answers_file"] == ".copier-answers.yml"
    assert not (FORBIDDEN_CONFIG_KEYS & set(configuration))

    for question in IDENTITY_KEYS:
        definition = configuration[question]
        assert isinstance(definition, dict)
        assert "secret" not in definition


def test_lifecycle_messages_render_with_strict_undefined_without_secrets() -> None:
    configuration = _load_yaml(REPOSITORY_ROOT / "copier.yml")
    defaults = {
        key: configuration[key]["default"]
        for key in IDENTITY_KEYS
    }
    sentinel_secret = "stage4-do-not-leak-sentinel"
    context = {
        **defaults,
        "_copier_conf": {"dst_path": "generated-project"},
        "_copier_answers": {**defaults, "runtime_secret": sentinel_secret},
    }
    environment = _jinja_environment()

    assert all(key in configuration for key in MESSAGE_KEYS)
    for message_key in MESSAGE_KEYS:
        message = configuration[message_key]
        assert isinstance(message, str)
        rendered = environment.from_string(message).render(context)
        assert rendered.strip()
        assert sentinel_secret not in rendered
