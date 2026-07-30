# FastAPI 项目 Copier 模板化设计与分阶段改造方案

> 状态：Copier 范围修订版  
> 日期：2026-07-30  
> 输入目录：`template/`  
> 目标：在不改变现有应用代码逻辑和目录结构的前提下，将当前项目改造成可复制、可追踪、可更新的 Copier 项目脚手架

## 1. 方案结论

当前 `template/` 是已经确认过的 FastAPI 项目源代码。本方案不再审查或重构它的应用架构，而是把它视为一份固定、可信的模板输入。

Copier 改造只完成以下工作：

1. 在仓库根目录建立 Copier 控制面；
2. 为项目名称、描述、初始版本和项目命名空间等标识增加模板变量；
3. 只对包含这些固定标识的文件进行 Jinja 渲染；
4. 生成并保存 `.copier-answers.yml`；
5. 建立不进入生成项目的模板验证；
6. 建立 Git tag、`copier update` 和 `copier recopy` 的版本更新流程；
7. 提供清晰的生成后操作说明。

首版生成结果：

- 保持当前 `main.py`、`app/`、`config/` 等目录结构；
- 保持现有模块划分、导入路径、配置加载和运行逻辑；
- 不迁移到 `src/` layout；
- 不增加或删除数据库、Redis、JWT、限流等现有能力；
- 不生成 `tests/`；
- 不生成 CI workflow；
- 不生成 Alembic；
- 不通过 Copier task 安装依赖、初始化 Git、启动容器或执行其他命令。

## 2. 范围边界

### 2.1 允许改动

允许的改动仅限于 Copier 模板化：

- 根目录新增 `copier.yml`；
- 根目录新增模板维护说明、变更日志和本地验证配置；
- `template/` 内新增动态 answers 文件模板；
- 对明确列入白名单的文件添加 `.jinja` 后缀；
- 将白名单文件中的固定项目标识替换为 Jinja 变量；
- 修正 README 中与生成方式、项目名称或实际交付内容有关的说明；
- 为模板生成、更新和回放建立外置验证。

### 2.2 禁止改动

以下内容不属于本轮范围：

- 调整 `main.py` 启动方式；
- 重排 `app/`、`config/` 或其他目录；
- 修改 Router、Service、Repository、Schema、Model 的设计；
- 修改数据库会话、Redis、JWT、中间件、异常、日志或生命周期实现；
- 修改现有业务行为和接口契约；
- 因代码审查意见引入任何架构重构；
- 为了模板选项而拆除或重写现有功能；
- 引入 tests、CI、Alembic 或其他下游团队自行决定的工程设施。

如果某个 Copier 变量必须依赖上述改动才能实现，则该变量不进入首版。

### 2.3 “保持不变”的判定

Copier 改造完成后，默认答案生成的项目应满足：

- 除 `.copier-answers.yml` 和项目标识替换外，文件集合与当前 `template/` 一致；
- 非 `.jinja` 文件与源文件逐字节一致；
- `.jinja` 文件只允许预先登记的标识字符串发生变化；
- Python 包仍为 `app`，配置包仍为 `config`，入口仍为 `main:app`；
- 现有依赖集合不因 Copier 选项改变；
- 默认生成项目的现有质量检查结果不因模板化而退化。

## 3. 当前 Copier 化基线

### 3.1 已确认且不再审查的输入

以下内容作为固定输入直接保留：

- `main.py` 应用入口；
- `app/` 全部运行代码和目录划分；
- `config/` 配置体系；
- Dockerfile 和 Compose 的现有运行逻辑；
- `pyproject.toml` 中现有依赖与工具配置；
- `uv.lock` 中现有依赖解析结果；
- `.agents/`、`.codex/`、`.github/copilot-instructions.md` 等协作说明；
- 当前项目已经确认过的代码风格和功能实现。

模板化验证的目标不是重新判断这些代码是否正确，而是证明 Copier 渲染没有破坏它们。

### 3.2 Copier 改造建设清单

当前仓库只有已经确认过的 `template/` 源代码，这是开始 Copier 改造前的正常基线，不代表项目存在缺陷。下表只是列出在现有源码外围需要新增的 Copier 能力，不对原项目作问题诊断。

| 建设项 | 当前基线 | 本次改造动作 |
| --- | --- | --- |
| Copier 控制入口 | 当前只提供 `template/` 源代码 | 在根目录新增唯一的 `copier.yml` |
| 模板源声明 | `template/` 已是明确的源码目录 | 配置 `_subdirectory: template` |
| Answers 契约 | 尚未进入模板生成阶段 | 新增 answers 文件模板并在生成项目中保存 `.copier-answers.yml` |
| 项目标识变量化 | 原始源码使用 `fastapi-template`、`FastAPI Template`、`template` 等固定名称 | 将所有固定项目标识替换为对应 Copier 变量 |
| 渲染范围 | 当前文件都是普通源文件 | 仅对白名单文件增加 `.jinja`，其余文件静态复制 |
| 问题契约 | 当前不需要 Copier questions | 为首版身份变量定义稳定 key、类型、默认值和校验规则 |
| 使用说明 | README 当前描述固定项目 | 补充 copy、update、recopy 和生成后操作说明 |
| 模板版本 | 当前尚未发布 Copier 版本 | 初始化模板 Git 历史并使用不可变版本 tag |
| Update 验证 | 当前尚未形成可更新的模板版本 | 建立真实的 `copier update` 和三方合并验证 |
| Recopy 验证 | 当前尚未形成 answers 契约 | 建立同版本、同答案的回放和幂等验证 |
| 安全基线 | 当前没有 Copier 执行配置 | 首版不使用 tasks、extensions、migrations，默认无需 `--trust` |
| 生成验证 | 当前尚未执行模板渲染 | 在模板根目录验证渲染残留、路径清单和静态文件一致性 |
| 锁文件策略 | `uv.lock` 作为当前项目的静态文件 | 保持静态复制；发布前明确依赖索引受众，不对 lock 做 Jinja 改写 |

## 4. 脚手架产品定义

### 4.1 输入与输出

输入：

- 当前模板 Git 地址或本地路径；
- 一组只描述项目身份的 Copier answers；
- 用户选择的目标目录。

输出：

- 一份与当前 `template/` 逻辑和结构一致的 FastAPI 项目；
- 已替换的项目名称、描述、版本和 Redis 命名空间；
- 可被后续 `copier update` 识别的 `.copier-answers.yml`；
- 不包含模板维护文件。

### 4.2 首版定位

首版是“固定工程基线的可命名复制器”，不是“任意功能组合生成器”。

该定位有三个好处：

1. 不需要为了条件组合改写现有代码；
2. 默认生成结果与已确认的源项目行为一致；
3. 先把 copy/update/recopy 协议做好，再评估后续是否需要功能选项。

### 4.3 首版非目标

- 不提供数据库类型选择；
- 不提供是否启用 Redis、JWT、限流或 Docker 的开关；
- 不提供 Python package 路径选择；
- 不提供 `src` layout 选择；
- 不提供测试、CI、Alembic 选项；
- 不收集数据库密码、JWT secret 等运行期敏感信息；
- 不在生成期间执行安装、建库、容器或 Git 命令。

## 5. 目标仓库结构

```text
fastapi-seed/
├── copier.yml
├── README.md                          # 模板仓库使用说明
├── CHANGELOG.md                       # 模板版本变更
├── pyproject.toml                     # 仅模板维护依赖
├── uv.lock                            # 仅模板维护环境
├── docs/
│   ├── fastapi-copier-scaffold-design.md
│   ├── copier-contract.md
│   └── release-checklist.md
├── tests/                             # 不进入生成结果
│   ├── test_copy.py
│   ├── test_render_contract.py
│   ├── test_update.py
│   ├── test_recopy.py
│   └── data/
│       ├── default.yml
│       └── custom.yml
└── template/
    ├── {{ _copier_conf.answers_file }}.jinja
    ├── README.md.jinja
    ├── pyproject.toml.jinja
    ├── compose.yaml.jinja
    ├── .env.example.jinja
    ├── .env.docker.example.jinja
    ├── main.py
    ├── app/
    ├── config/
    └── ...                            # 其余现有文件保持原路径
```

说明：

- `template/` 仍是唯一生成源；
- 根目录文件不会进入生成结果；
- 根目录 `tests/` 只验证模板，不代表生成项目自带测试；
- 生成项目不再套一层 `{{ project_name }}/`，目标目录本身就是项目根；
- 不在 `template/` 内放模板维护脚本、模板发布配置或嵌套 `.git`。

## 6. 生成项目结构

默认生成结果沿用当前结构：

```text
target-project/
├── .copier-answers.yml
├── .agents/
├── .codex/
├── .github/
│   └── copilot-instructions.md
├── app/
├── config/
├── .env.example
├── .env.docker.example
├── AGENTS.md
├── compose.yaml
├── Dockerfile
├── main.py
├── pyproject.toml
├── README.md
└── uv.lock
```

明确不生成：

- `tests/`；
- `.github/workflows/`；
- `alembic/`；
- 模板仓库根目录的维护文档和验证代码。

## 7. Copier 问题模型

### 7.1 首版问题

首版只询问项目身份信息：

| Key | 类型 | 默认值 | 用途 |
| --- | --- | --- | --- |
| `project_name` | `str` | `fastapi-template` | Python distribution 名、Compose 项目名、镜像名和机器可读标识 |
| `project_title` | `str` | `FastAPI Template` | README 标题和人类可读项目名称 |
| `project_description` | `str` | 当前项目说明 | `pyproject.toml` 和 README 简介 |
| `project_version` | `str` | `0.1.0` | 生成项目初始版本 |
| `redis_prefix` | `str` | `template` | Redis key 与缓存序列化命名空间 |

### 7.2 命名约束

`project_name`：

- 只允许小写字母、数字和单个连字符；
- 必须以字母或数字开头、结尾；
- 不能包含空格、下划线、路径分隔符或 Jinja 标记；
- 作为长期 answers 保存，后续 update 不自动重新计算。

`project_title`：

- 去除首尾空白后不能为空；
- 只用于展示，不参与文件路径和 Python import。

`project_version`：

- 使用合法的 PEP 440 版本；
- 只表示生成项目的初始版本，不等于模板版本；
- 模板升级不得自动覆盖用户后来维护的应用版本，相关冲突交由 Copier 三方合并处理。

`redis_prefix`：

- 不能为空；
- 不包含空白、控制字符和冒号；
- 用户必须确认并持久化，避免后续模板算法变化导致已有 Redis key 命名空间漂移。

### 7.3 不设置 `package_name`

当前 Python 包固定为 `app`。增加 `package_name` 会要求移动目录、重写 import 和修改大量文档，违反“不调整原有代码结构”的边界，因此首版不设置该问题。

### 7.4 不设置功能开关

首版不设置：

- `use_postgresql`；
- `use_redis`；
- `use_jwt`；
- `use_rate_limit`；
- `include_docker`；
- `include_tests`；
- `ci`；
- `use_alembic`。

这些开关都会改变文件集合、依赖或运行路径，需要重新验证业务逻辑，超出当前 Copier 改造范围。

### 7.5 变量使用映射

每个问题都必须有明确用途，禁止收集生成结果中没有使用的答案。

| Copier 变量 | 生成位置 | 说明 |
| --- | --- | --- |
| `project_name` | `pyproject.toml` 的 project name、Compose project name、镜像名、应用名称 fallback | 统一替换所有 `fastapi-template` 机器标识 |
| `project_title` | README 标题和项目展示名称 | 统一替换 `FastAPI Template` |
| `project_description` | `pyproject.toml` description、README 简介 | 只描述生成项目，不参与路径 |
| `project_version` | `pyproject.toml` version、应用版本 fallback | 只表示生成项目初始版本 |
| `redis_prefix` | 环境变量示例、缓存配置默认值、Redis key 示例、序列化命名空间 | 统一替换作为项目命名空间使用的 `template` |

不额外询问可由这些答案直接得到的值：

- Compose project name 和 image name 直接使用 `project_name`；
- Python import package 固定为现有 `app`，不产生 `package_name`；
- 缓存序列化标识由 `redis_prefix` 渲染；
- 目标目录使用 Copier 调用方传入的 destination，不再询问目录名。

模板内部可以使用 Copier 内置上下文，但不把它们设计成用户问题：

| 内置变量 | 用途 |
| --- | --- |
| `_copier_conf.answers_file` | 动态生成 answers 文件名 |
| `_copier_conf.dst_path` | 在生成完成消息中展示目标目录 |
| `_copier_answers` | 完整、规范地写入 Copier 所需元数据和用户答案 |

变量验收必须覆盖默认值、自定义值、中文描述、引号和特殊字符，保证 Python、TOML、YAML 与 Markdown 渲染结果有效。

## 8. 文件模板化白名单

### 8.1 白名单原则

只有确实包含项目固定标识的文件才增加 `.jinja` 后缀。其余文件保持静态复制。

禁止：

- 批量把所有文件改成 `.jinja`；
- 设置 `_templates_suffix: ""`；
- 在大型 Python 文件中加入功能条件；
- 通过注释/取消注释控制代码；
- 在不同答案下删除当前运行模块；
- 对 `uv.lock` 做字符串替换。

### 8.2 首版白名单

| 源文件 | 模板文件 | 允许替换 |
| --- | --- | --- |
| `README.md` | `README.md.jinja` | 标题、目录名、描述、Redis 示例前缀 |
| `pyproject.toml` | `pyproject.toml.jinja` | name、version、description |
| `compose.yaml` | `compose.yaml.jinja` | Compose project name、镜像名 |
| `.env.example` | `.env.example.jinja` | `REDIS_PREFIX` 示例值 |
| `.env.docker.example` | `.env.docker.example.jinja` | Redis prefix 示例值 |
| `config/app_config.py` | `config/app_config.py.jinja` | 固定 fallback name/version 字符串 |
| `config/cache_config.py` | `config/cache_config.py.jinja` | 默认 Redis prefix 字符串 |
| `app/core/cache/prefixes.py` | `app/core/cache/prefixes.py.jinja` | 注释和示例中的 Redis prefix |
| `app/core/cache/redis.py` | `app/core/cache/redis.py.jinja` | 缓存序列化命名空间字符串 |
| `app/core/cache/README.md` | `app/core/cache/README.md.jinja` | Redis prefix 文档和示例 |

此外新增：

```text
template/{{ _copier_conf.answers_file }}.jinja
```

如果实施时发现新的固定项目标识，必须先更新白名单和替换契约，再修改文件；不得临时扩大 Jinja 范围。

### 8.3 Python 文件模板化约束

对白名单中的 Python 文件：

- 只能替换字符串字面量、注释或 docstring 中的项目标识；
- 不增加 `{% if %}`、`{% for %}` 等控制逻辑；
- 不修改函数、类、import、条件分支或调用顺序；
- 渲染后必须能通过 Python 语法解析；
- 默认答案渲染结果应与改造前文件语义等价。

## 9. `copier.yml` 设计

推荐基础配置：

```yaml
_min_copier_version: "9.17.0"
_subdirectory: template
_templates_suffix: .jinja
_answers_file: .copier-answers.yml

_envops:
  keep_trailing_newline: true
  undefined: jinja2.StrictUndefined

_preserve_symlinks: false

_message_before_copy: |
  即将生成 "{{ project_title }}"（{{ project_name }}）。
  本模板只渲染项目文件，不会自动安装依赖、初始化 Git 或启动容器。

_message_after_copy: |
  项目已生成。
  1. 进入目标目录：{{ _copier_conf.dst_path }}
  2. 复制并填写环境变量示例文件。
  3. 运行 uv sync --locked。
  4. 按实际项目需要自行接入 tests、CI 和数据库迁移方案。
  5. 将 uv.lock 与 .copier-answers.yml 一并提交到 Git。

_message_before_update: |
  即将更新 "{{ project_title }}"。
  请确认目标项目已纳入 Git、当前工作区干净，并在独立分支执行更新。

_message_after_update: |
  模板已更新。
  请先检查 Git diff 和冲突标记，再运行项目原有质量检查。
```

### 9.1 安全消息钩子

首版使用四个只输出提示、不执行命令的生命周期消息：

| 设置 | 作用 | 是否修改目标项目 |
| --- | --- | --- |
| `_message_before_copy` | 告知即将生成的项目和“仅渲染、不执行命令”的边界 | 否 |
| `_message_after_copy` | 给出依赖同步、环境变量和 Git 提交等后续步骤 | 否 |
| `_message_before_update` | 提醒使用干净工作区和独立分支 | 否 |
| `_message_after_update` | 提醒检查 diff、冲突标记和项目质量检查 | 否 |

消息允许使用已确认的项目变量和 Copier 内置目标路径，但不得包含 secret。

### 9.2 可执行 hooks 策略

Copier 没有必要为了本项目首版执行任意生成后命令。以下可执行机制全部不启用：

- `_tasks`：不自动执行 `uv sync`、`git init`、Docker、文件删除或格式化命令；
- `_migrations`：首版尚无旧模板协议需要迁移；
- `_jinja_extensions` / context hook：当前变量可直接由 questions 和内置 Jinja 完成，不引入 Python 扩展；
- 外部 shell hook：不引入跨平台差异和命令注入面。

这样 `copy`、`update` 和 `recopy` 默认都不要求 `--trust`。未来只有出现无法通过普通渲染或 Copier 三方合并解决的明确需求时，才单独设计可执行 hook，并要求它满足最小权限、跨平台、幂等、可跳过和可测试。

首版不配置：

- `_tasks`；
- `_migrations`；
- `_jinja_extensions`；
- `_skip_if_exists`；
- `_secret_questions`；
- 平台特定 shell 命令。

结果是 `copier copy` 默认无需 `--trust`，生成过程只在目标目录渲染文件。

## 10. Answers 文件设计

模板文件：

```yaml
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
{{ _copier_answers | to_nice_yaml -}}
```

原则：

- 文件名使用 `{{ _copier_conf.answers_file }}`，不把实际 answers 文件名写死在源路径；
- 使用 Copier 内置 `_copier_answers`，由 Copier 统一保存 `_src_path`、`_commit` 和全部可序列化问题答案；
- answers 文件必须进入生成项目 Git；
- 不记录数据库密码、Redis 密码、JWT secret 或 Token；
- 问题 key 一旦发布即视为公共 API；
- 已发布 key 不随意改名或复用为其他含义；
- `_src_path` 使用稳定模板远端地址；
- `_commit` 指向生成时使用的不可变模板版本。

## 11. Secrets 与运行期配置

Copier 只收集项目身份，不收集运行期配置。

以下内容继续由现有环境变量示例管理：

- PostgreSQL 地址、账号和密码；
- Redis 地址和密码；
- JWT secret；
- CORS；
- 日志级别；
- 连接池、超时和 worker 参数。

理由：

- 这些值因开发、测试和生产环境而异；
- 写入 answers 会形成长期明文记录；
- `secret: true` 只是不把答案写入 answers，并不等于加密；
- 它们不应该在模板 update 时被重新计算或覆盖。

## 12. `uv.lock` 分发策略

首版依赖集合不做条件化，因此 `uv.lock` 保持静态复制，不增加 Jinja。

但当前 lock 绑定清华 PyPI 镜像，发布前必须明确模板受众：

- 如果脚手架明确面向国内开发环境，可以保留并在 README 说明；
- 如果脚手架面向通用或国际环境，应在发布模板 tag 前使用目标公共索引重新生成 lock；
- 不通过 Copier 问题动态选择 index；
- 不手工替换 lock 内 URL；
- 不维护多份条件化 lock。

每个发布 tag 都要验证：

```bash
uv lock --check
uv sync --locked
```

项目身份变量变化不应改变依赖集合；若 `pyproject.toml` 的模板化导致 lock 校验变化，应在发布流程中重新生成静态 lock，而不是在 Copier task 中联网解析。

## 13. Git 与版本更新协议

### 13.1 模板版本

- 模板仓库必须初始化 Git；
- 正式版本使用不可变 tag，例如 `v0.1.0`、`v0.2.0`、`v1.0.0`；
- 模板 tag 和生成项目的 `project_version` 是两套独立版本；
- 已发布 tag 不移动、不覆盖；
- 每个 tag 对应 CHANGELOG 条目。

### 13.2 Copy

正式使用方式：

```bash
copier copy --vcs-ref=v0.1.0 <template-git-url> <target-directory>
```

验证：

- answers 被正确保存；
- 目标目录没有模板维护文件；
- 静态文件未被改变；
- 白名单变量全部完成替换；
- 没有残留 Jinja 语法。

### 13.3 Update

生成项目使用：

```bash
copier update --vcs-ref=v0.2.0
```

前提：

- 生成项目已提交 `.copier-answers.yml`；
- 工作区干净；
- 模板源 tag 可访问；
- update 在独立分支执行；
- 用户先查看 diff，再运行项目自身的验证命令。

### 13.4 Recopy

`copier recopy` 仅作为同版本重放、恢复模板管理文件或诊断漂移的工具。

必须验证：

- 同一 tag、相同 answers 的 recopy 不产生无意义 diff；
- recopy 不丢失 answers；
- 文档明确说明 recopy 可能覆盖模板管理文件中的用户改动；
- 日常升级优先使用 update。

### 13.5 Copier migrations

首版不使用 `_migrations`。

Copier migration 只用于模板答案或文件所有权协议升级，与 Alembic 数据库迁移无关。只有未来确实发生以下情况时才考虑：

- 已发布问题 key 改名；
- answers schema 需要转换；
- 普通三方合并无法处理的路径所有权迁移。

## 14. 模板外置验证

根目录测试不进入生成项目，只用于证明 Copier 改造没有破坏固定源代码。

### 14.1 Default copy

使用默认 answers 生成临时项目，验证：

- 生成成功；
- `.copier-answers.yml` 存在且不包含 secret；
- 生成文件清单符合契约；
- 不存在 `tests/`、CI workflow 或 Alembic；
- TOML、YAML 和 Python 文件可解析；
- 没有 `.jinja`、`{{`、`{%` 残留；
- 原项目入口和 import 路径保持不变；
- 四个生命周期消息均能正常渲染，且不包含 secret；
- 模板没有 tasks、migrations 或自定义 context hook；
- `uv lock --check` 通过。

### 14.2 Custom identity copy

至少使用一组自定义 answers：

```yaml
project_name: order-service
project_title: Order Service
project_description: Async order API
project_version: 0.1.0
redis_prefix: order
```

验证所有白名单位置完成替换，同时确保：

- Python 包路径仍为 `app`；
- `main:app` 不变；
- 依赖集合不变；
- 非白名单文件 hash 不变；
- 不残留 `fastapi-template`、`FastAPI Template` 或默认 Redis prefix。

### 14.3 静态文件完整性

建立生成清单和 hash 校验：

1. 枚举 `template/` 中所有非 `.jinja` 文件；
2. 在默认生成结果中找到对应路径；
3. 比较 SHA-256；
4. 任一静态文件发生变化立即失败。

这项验证是“不动原有代码逻辑和结构”的核心技术保障。

### 14.4 渲染白名单

对白名单文件保存允许变化的字段清单。测试必须证明：

- 只出现已声明变量；
- Python 模板没有控制语句；
- 默认值渲染与原固定标识一致；
- 自定义值不会破坏 TOML、YAML、Python 或 Markdown；
- Jinja 自动转义和引号处理不会产生语法错误。

### 14.5 Update 验证

使用临时 Git 仓库模拟：

1. 发布模板 `v0.1.0`；
2. 生成项目并提交；
3. 模拟用户修改 README、配置值并新增业务文件；
4. 模板发布 `v0.2.0`；
5. 执行 `copier update`；
6. 验证模板改动进入、用户新增文件保留、answers 更新；
7. 验证不存在未处理的 `<<<<<<<`、`=======`、`>>>>>>>` 或 `.rej`。

### 14.6 本地门禁

首版不要求 CI，但模板发布前必须有单一的本地验证入口，例如：

```bash
uv run pytest
```

该命令负责运行 copy、custom identity、hash、update 和 recopy 验证。是否增加模板仓库 CI 可在以后决定，不影响生成结果。

## 15. 分阶段改造计划

### 阶段 0：冻结范围与建立基线

目标：确保 Copier 改造不会演变为应用重构。

工作：

- 将当前 `template/` 作为已确认基线；
- 初始化模板仓库 Git；
- 提交改造前完整基线；
- 记录“不修改应用逻辑和目录结构”的 ADR；
- 生成当前文件清单和静态文件 hash 基线；
- 记录 tests、CI、Alembic 不进入生成结果。

验收：

- 可通过 Git 找回改造前版本；
- 白名单之外的文件有可验证 hash；
- 范围文档得到确认；
- 此阶段不修改 `template/` 内容。

### 阶段 1：建立最小 Copier 控制面

目标：先让固定项目可以被 Copier 原样生成。

工作：

- 根目录新增 `copier.yml`；
- 配置 `_subdirectory: template`；
- 配置 `.jinja` 后缀和 StrictUndefined；
- 新增动态 answers 文件模板；
- 配置 before/after copy、before/after update 四个安全消息钩子；
- 首版不添加 tasks、migrations、extensions、skip；
- 根目录新增模板维护依赖。

验收：

- 默认 copy 不需要 `--trust`；
- 生成结果保留当前目录结构；
- 根目录维护文件不会进入生成结果；
- answers 文件能记录模板来源和版本。

### 阶段 2：项目身份参数化

目标：只替换固定项目标识，不改变代码行为。

工作：

- 增加 `project_name`、`project_title`、`project_description`、`project_version`、`redis_prefix`；
- 将白名单文件改名为 `.jinja`；
- 逐个替换硬编码标识；
- 不增加任何功能条件；
- 不调整 Python 文件路径或 import。

验收：

- 默认 answers 生成结果与原项目等价；
- 自定义 answers 在全部白名单位置一致生效；
- 非白名单文件 hash 完全一致；
- Python、TOML 和 YAML 均能解析。

### 阶段 3：完善生成体验与文档

目标：让使用者清楚如何生成、启动和继续维护项目。

工作：

- 根 README 增加 Copier 安装、copy、update、recopy 说明；
- 生成项目 README 使用项目变量；
- 完善四个生命周期消息钩子的用户提示；
- 明确生成项目不包含 tests、CI、Alembic；
- 明确运行期 secret 不由 Copier 收集；
- 说明 `uv.lock` 索引策略。

验收：

- 新用户可仅按文档完成生成；
- 文档不承诺未交付能力；
- 命令、路径和文件名与真实输出一致。

### 阶段 4：建立模板外置验证

目标：用自动化证明模板化没有破坏固定源代码。

工作：

- 新增 default/custom copy 测试；
- 新增文件清单与静态 hash 测试；
- 新增白名单变量渲染测试；
- 新增 Jinja 残留和语法解析检查；
- 新增 `uv lock --check`；
- 建立单一本地发布门禁。

验收：

- 默认和自定义生成均通过；
- 静态文件零漂移；
- 模板变量无遗漏；
- 生成结果无模板维护文件。

### 阶段 5：验证 update 与 recopy

目标：证明脚手架可以长期升级，而不只是首次 copy。

工作：

- 在临时 Git 模板仓库创建两个版本 tag；
- 模拟生成项目的用户修改和新增业务文件；
- 执行 update；
- 执行同版本 recopy；
- 检查 answers、冲突标记和无意义 diff。

验收：

- update 保留非冲突用户修改；
- 用户新增文件不丢失；
- answers `_commit` 正确更新；
- recopy 行为符合文档；
- 不存在未解释冲突。

### 阶段 6：发布首个模板版本

目标：形成可复用、可升级的正式模板。

工作：

- 完成 release checklist；
- 确认模板远端 URL；
- 确认 `uv.lock` 索引受众；
- 运行完整本地门禁；
- 编写 CHANGELOG；
- 发布不可变 `v0.1.0`；
- 用正式远端 tag 完成一次全新 copy。

验收：

- 正式 tag 可复制；
- answers 记录正式远端和 tag；
- 默认及自定义项目均可生成；
- update 基线已建立；
- 发布 tag 与源提交一一对应。

### 阶段 7：首版稳定后再评估扩展

后续只有在明确需求和独立验证充分时，才评估：

- License 文件选择；
- 作者元数据；
- Docker 是否生成；
- 可选 AI 协作文件；
- 数据库、Redis 或认证能力组合；
- tests、CI、Alembic profile；
- Copier `_migrations`。

每增加一个选项，都必须重新评估它是否会改变现有代码逻辑或结构；如果会，则应作为独立项目设计，而不是混入本轮 Copier 包装。

## 16. 风险与控制

| 风险 | 影响 | 控制措施 |
| --- | --- | --- |
| 模板化范围继续扩大 | 变成应用重构 | 明确白名单；阶段 0 冻结范围 |
| 所有文件批量 Jinja 化 | 转义问题多、静态文件难验证 | 只对固定标识文件使用 `.jinja` |
| Python 模板改到运行逻辑 | 行为与原项目不一致 | Python 文件仅允许字符串、注释、docstring 替换 |
| 新增 package_name | 触发目录和 import 大规模变化 | 首版固定 `app` package |
| 功能选项组合爆炸 | 被迫改变依赖和代码路径 | 首版不设置功能开关 |
| answers key 后续改名 | update 丢失历史答案 | 问题 key 按公共 API 管理 |
| 模板 tag 被移动 | Copier 无法重放旧版本 | tag 发布后不可变 |
| 静态文件意外变化 | 原代码被无意修改 | 文件清单与 SHA-256 校验 |
| Jinja 残留 | 生成项目不可用 | 全目录残留扫描 |
| secret 写入 answers | 长期明文泄漏 | Copier 不询问运行期 secret |
| lock 绑定单一区域索引 | 用户无法安装依赖 | 发布前明确受众；不对 lock 做 Jinja |
| 没有远程 CI | 发布门禁可能漏跑 | 单一本地命令和 release checklist |
| update 冲突 | 用户难以升级 | 小步 tag、真实 update 测试、干净 Git 分支 |

## 17. 完成定义

满足以下条件后，首版 Copier 改造才算完成：

1. 根目录存在可用的 `copier.yml`；
2. `_subdirectory` 正确指向 `template/`；
3. `copier copy` 默认不需要 `--trust`；
4. 四个安全消息钩子均能渲染；生成过程不运行 task、不联网安装依赖、不操作 Git；
5. 生成项目结构与当前 `template/` 保持一致；
6. Python package 仍为 `app`，入口仍为 `main:app`；
7. 非模板白名单文件与原文件 hash 一致；
8. 白名单文件只替换项目身份标识；
9. 默认和自定义 answers 都能成功生成；
10. 生成项目没有 Jinja 残留和模板维护文件；
11. `.copier-answers.yml` 包含来源、版本和全部非敏感答案；
12. 生成项目不包含 tests、CI workflow 或 Alembic；
13. `uv.lock` 不经过 Jinja 处理并能通过 lock check；
14. `copier update` 在真实用户修改场景下通过；
15. 同版本 recopy 行为稳定且有文档；
16. 模板版本使用不可变 Git tag；
17. README 中的命令、路径和能力边界与真实输出一致；
18. 没有因本次改造引入应用逻辑或目录结构变化。

## 18. 官方依据

- [Copier：Configuring a template](https://copier.readthedocs.io/en/stable/configuring/)
- [Copier：Creating a template](https://copier.readthedocs.io/en/stable/creating/)
- [Copier：Generating a project](https://copier.readthedocs.io/en/stable/generating/)
- [Copier：Updating a project](https://copier.readthedocs.io/en/stable/updating/)
- [Copier：项目发布信息](https://pypi.org/project/copier/)
- [uv：Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
