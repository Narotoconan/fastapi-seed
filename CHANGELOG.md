# 变更日志

## [1.0.0] - 2026-08-01

### 新增

- 基于 [Narotoconan/fastapi-template](https://github.com/Narotoconan/fastapi-template)
  改造并发布首个 Copier 脚手架版本。
- 建立最小 Copier 控制面，并将 `template/` 固定为唯一生成源。
- 支持 `project_name`、`project_title`、`project_description`、
  `project_version` 和 `redis_prefix` 五个项目身份参数。
- 在生成项目中保存 `.copier-answers.yml`，支持模板来源和生成答案追踪。
- 提供 `copier copy`、`copier update` 和 `copier recopy` 使用说明。
- 建立默认参数、自定义参数、静态文件一致性、模板渲染、语法检查、
  `update` 和 `recopy` 的本地验收测试。
- 提供统一的本地发布门禁：`uv run pytest`。

### 安全性与兼容性

- 仅对项目身份相关白名单文件进行模板化，保持原有应用代码逻辑和目录结构不变。
- 不收集或保存数据库密码、Redis 密码、JWT 密钥等运行期敏感信息。
- 不使用 Copier tasks、extensions 或 migrations，项目生成默认不需要 `--trust`。
- `uv.lock` 作为静态文件分发，不在项目生成期间联网重建依赖。