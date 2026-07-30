# 阶段 0 模板基线

本目录记录 Copier 改造前的 `template/` 文件集合与静态文件字节级基线。

## 基线信息

- 基线日期：2026-07-31
- Git 提交：`e88fa9ebc654ecadb6bbc2e183b768a6be131b7a`
- `template/` Git tree：`7bbc83e963b0933549f12e8d48ae6e581cd6373a`
- 文件总数：76
- 后续渲染白名单文件数：10
- 白名单外静态文件数：66
- 内容摘要算法：SHA-256

文件用途：

- `template-files.txt`：按路径排序的完整文件清单；
- `template-render-whitelist.txt`：设计方案 8.2 节登记的后续渲染白名单；
- `template-static.sha256`：白名单外 66 个静态文件的 SHA-256，格式为 `<hash><两个空格><仓库相对路径>`。

所有路径都以仓库根目录为基准，并统一使用 `/` 分隔符。摘要针对阶段 0 工作区中的原始文件字节计算，不对换行符或其他内容做规范化。

## 验证

先确认可通过 Git 找回改造前版本，并且当前 `template/` 与该版本没有差异：

```powershell
git diff --exit-code e88fa9ebc654ecadb6bbc2e183b768a6be131b7a -- template
git rev-parse e88fa9ebc654ecadb6bbc2e183b768a6be131b7a:template
```

第二条命令应输出：

```text
7bbc83e963b0933549f12e8d48ae6e581cd6373a
```

验证完整文件清单：

```powershell
$templateRoot = (Resolve-Path "template").Path
$actualFiles = Get-ChildItem -LiteralPath $templateRoot -Recurse -Force -File |
    ForEach-Object {
        "template/" + $_.FullName.Substring($templateRoot.Length + 1).Replace("\", "/")
    } |
    Sort-Object
$expectedFiles = Get-Content -LiteralPath "docs/baselines/template-files.txt"
$fileDiff = Compare-Object $expectedFiles $actualFiles
if ($fileDiff) {
    $fileDiff
    throw "template/ 文件清单与阶段 0 基线不一致"
}
```

逐项验证白名单外静态文件：

```powershell
$failedFiles = @()
Get-Content -LiteralPath "docs/baselines/template-static.sha256" | ForEach-Object {
    if ($_ -notmatch "^([0-9a-f]{64})  (.+)$") {
        throw "无法解析 SHA-256 基线行：$_"
    }
    $expectedHash = $Matches[1]
    $relativePath = $Matches[2]
    $actualHash = (Get-FileHash -LiteralPath $relativePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        $failedFiles += $relativePath
    }
}
if ($failedFiles) {
    $failedFiles
    throw "白名单外静态文件与阶段 0 基线不一致"
}
```

这些是阶段 0 的只读验收方法，不是阶段 4 的自动化测试或发布门禁。

