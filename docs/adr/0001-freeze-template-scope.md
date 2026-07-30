# ADR-0001：冻结 Copier 模板化范围

- 状态：已接受
- 日期：2026-07-31
- 依据：`docs/fastapi-copier-scaffold-design.md`
- 改造前基线提交：`e88fa9ebc654ecadb6bbc2e183b768a6be131b7a`

## 背景

`template/` 是已经确认的 FastAPI 项目源代码。当前工作的目的，是在后续阶段为它增加 Copier 控制面、有限的项目身份渲染和升级协议，而不是重新审查或重构应用。

如果没有明确、可验证的边界，模板化可能逐步扩大到应用架构、功能组合、依赖集合或运行行为，导致生成结果偏离当前基线。

## 决策

1. 将基线提交中的整个 `template/` 认定为固定、可信的模板输入。
2. 阶段 0 不修改 `template/` 的任何文件内容、文件名或目录结构。
3. 后续阶段也不得修改应用逻辑、业务行为、公共接口、模块划分、导入路径、配置加载、启动方式或现有依赖集合。
4. Python 包固定为 `app`，配置包固定为 `config`，应用入口固定为 `main:app`；首版不引入 `src/` layout 或 `package_name`。
5. 后续只允许对设计方案登记的渲染白名单进行项目身份标识替换。扩大白名单前，必须先更新设计方案和替换契约。
6. 生成项目明确不包含以下模板维护或下游工程设施：
   - 根目录模板维护文档与验证代码；
   - `tests/`；
   - `.github/workflows/`（CI workflow）；
   - `alembic/`。
7. 不得为了上述排除项删除或改写当前 `template/` 中已有的依赖、文档或代码。`template/.github/copilot-instructions.md` 是既有协作说明，不属于 CI workflow，继续保留。
8. Copier 首版不提供数据库、Redis、JWT、限流、Docker、tests、CI 或 Alembic 功能开关，也不收集运行期 secret。
9. Copier 生成期间不安装依赖、不初始化 Git、不启动容器、不执行数据库操作，也不运行其他外部命令。

## 基线证据

- 改造前版本：Git 提交 `e88fa9ebc654ecadb6bbc2e183b768a6be131b7a`
- 改造前 `template/` Git tree：`7bbc83e963b0933549f12e8d48ae6e581cd6373a`
- 当前文件清单：`docs/baselines/template-files.txt`
- 后续渲染白名单：`docs/baselines/template-render-whitelist.txt`
- 白名单外静态文件 SHA-256：`docs/baselines/template-static.sha256`

## 结果

- 应用变更与 Copier 控制面变更被明确分离。
- 后续可以通过 Git 和 SHA-256 检查发现意外的文件、路径或字节级漂移。
- tests、CI 和 Alembic 可由下游团队自行决定，不成为首版生成结果的一部分。
- 任何需要改变当前应用逻辑或目录结构的需求，都必须脱离本轮 Copier 包装单独设计和验收。

