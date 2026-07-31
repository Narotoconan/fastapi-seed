# FastAPI Copier Scaffold

本仓库维护一份固定 FastAPI 工程基线的 Copier 模板。`template/` 是唯一生成源；仓库根目录的
`copier.yml`、维护环境、设计文档等不会进入生成项目。

首版只收集五个项目身份字段：`project_name`、`project_title`、`project_description`、
`project_version` 和 `redis_prefix`。它不会按答案增删功能，也不会改变 `app`、`config` 或
`main:app` 的既有结构。

## 项目来源

本项目基于 [Narotoconan/fastapi-template](https://github.com/Narotoconan/fastapi-template)
改造，并在原有 FastAPI 工程模板基础上封装为 Copier 脚手架。

## 前置条件与安装

需要 Git、Python 3.12 和 [uv](https://docs.astral.sh/uv/)。建议把锁定版本的 Copier 安装为独立工具：

```bash
uv tool install "copier==9.17.0"
copier --version
```

模板维护者也可以在仓库根目录使用锁定的维护环境：

```bash
uv sync --locked
uv run copier --version
```

下文默认使用独立的 `copier` 命令；若使用维护环境，请将其替换为 `uv run copier`。

## 生成项目

### 从当前本地仓库生成

当前尚未发布正式模板 tag。开发或评估时，先确认模板仓库工作区干净，再从仓库根目录生成到一个
不存在或为空的同级目录：

```bash
copier copy --vcs-ref=HEAD . ../my-service
```

Copier 会依次询问五个身份字段，并把目标目录本身作为项目根，不会再套一层 `project_name` 目录。
生成结果会保存 `.copier-answers.yml`，其中包含模板来源、版本和非敏感答案；应将它提交到生成项目的
Git 历史中。

### 从正式版本生成

正式发布后应使用不可变 tag。以下尖括号内容是占位符，必须替换成真实值：

```bash
copier copy --vcs-ref=<template-tag> <template-git-url> <target-directory>
```

长期维护的项目应使用稳定远端 URL 和不可变 tag；本地 `HEAD` 方式只用于当前仓库的开发与评估。

## 生成后启动

进入生成目录，先检查静态 lock 是否仍与项目身份一致：

```bash
cd ../my-service
uv lock --check
```

默认身份会直接通过。若自定义了 `project_name` 或 `project_version`，uv 可能要求刷新根项目元数据；
确认组织采用的包索引后执行：

```bash
uv lock
uv lock --check
```

随后安装锁定依赖：

```bash
uv sync --locked
```

复制环境变量示例并填写实际值：

```powershell
Copy-Item .env.example .env.local
```

Linux / macOS：

```bash
cp .env.example .env.local
```

至少配置 `DB_PASSWORD` 和 `JWT_SECRET_KEY`；数据库或 Redis 不在本机时还需配置对应主机和端口。
启动开发服务：

```bash
uv run --env-file .env.local uvicorn main:app --reload
```

更多运行、Docker 和应用边界说明见生成项目自身的 `README.md`。

## 更新已生成项目

日常模板升级使用 `update`。执行前必须满足：

- `.copier-answers.yml` 已提交；
- 生成项目是 Git 仓库且工作区干净；
- answers 中记录的模板源和目标 tag 可访问；
- 更新在独立分支进行。

在生成项目根目录执行，并把占位符替换为真实的新 tag：

```bash
git switch -c chore/copier-update
copier update --vcs-ref=<new-template-tag>
git status --short
git diff --check
```

检查所有 diff、冲突标记和 `.rej` 文件，确认 `.copier-answers.yml` 中的 `_commit` 已更新，再运行该项目
实际具备的质量检查。若 `pyproject.toml` 发生身份或依赖变化，还应重新执行 `uv lock --check`。

## 同版本重放

`recopy` 忽略生成后形成的差异，按同一模板版本重新渲染模板管理文件。需要诊断漂移或恢复这些文件时，
先提交或备份用户修改，再在生成项目根目录执行：

```bash
copier recopy --vcs-ref=:current:
```

该命令可能覆盖模板管理文件中的用户改动。日常升级应优先使用 `copier update`，不要把 `recopy` 当作
常规升级命令。

## Secrets 与交付边界

Copier 只收集项目身份，不询问或保存数据库密码、Redis 密码、JWT secret、Token 等运行期配置。
`secret: true` 也不等于加密，因此首版没有 secret 问题。运行期值继续通过 `.env.example`、
`.env.docker.example` 或部署环境注入；不要提交含真实凭据的环境文件。

生成项目不包含：

- `tests/` 测试套件；
- `.github/workflows/` 或其他 CI workflow；
- Alembic 及数据库迁移脚本。

这些能力需由下游项目按实际需求自行接入。模板也不配置 tasks、migrations 或自定义扩展，因此
`copy`、`update` 和 `recopy` 默认都不需要 `--trust`，且不会自动安装依赖、初始化 Git、启动容器或
执行其他命令。

## `uv.lock` 索引策略

生成项目的 `uv.lock` 是静态文件，不经过 Jinja，也不由 Copier task 联网重建。当前 lock 绑定清华
PyPI 镜像，适合明确采用该索引的环境：

- 不通过 Copier 问题动态选择包索引；
- 不手工替换 lock 内 URL；
- 不维护多份条件化 lock；
- 面向其他索引或通用受众发布前，应在目标索引环境重新生成一份静态 lock；
- 每个发布候选生成结果都应通过 `uv lock --check` 和 `uv sync --locked`。

自定义项目名或版本导致 lock 根项目元数据过期时，应在生成项目内确认索引后运行 `uv lock`，并将更新后的
`uv.lock` 与 `.copier-answers.yml` 一并提交；模板生成过程本身不会执行这一步。
