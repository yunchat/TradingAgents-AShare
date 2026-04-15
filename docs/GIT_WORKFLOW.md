# Git 开发工作流规范

本项目基于 Fork 工作流进行开发，支持独立功能开发、选择性合并上游功能、以及稳定版本发布。

## Remote 配置

| Remote | 仓库 | 说明 |
|--------|------|------|
| `origin` | `git@github.com:yunchat/TradingAgents-AShare.git` | 个人 fork，日常推送目标 |
| `upstream` | `git@github.com:KylinMountain/TradingAgents-AShare.git` | 上游仓库，只读同步 |

```bash
git remote -v  # 验证配置
```

---

## 分支结构

```
upstream/main  ──────────────────────────────────────►
                    ↓ merge（完全同步）
origin/main    ──────────────────────────────────────►  跟踪上游，不直接开发
                    ↓ rebase（定期同步）        ↑ cherry-pick（选择性合并）
origin/dev     ──────────────────────────────────────►  主开发分支，含独特功能
                    ↓ merge --no-ff（手动发布）
origin/release ──────────────────────────────────────►  稳定发布版本，用于部署
```

| 分支 | 追踪 | 说明 |
|------|------|------|
| `main` | `origin/main` | 与上游完全同步，不直接开发 |
| `dev` | `origin/dev` | 主开发分支，含独特功能 |
| `release` | `origin/release` | 稳定发布版本 |
| `fix/xxx` | `origin/fix/xxx` | 提交给上游的 PR 分支 |

---

## 日常开发流程

### 1. 在 dev 分支开发

```bash
git checkout dev
# 开发...
git add <files>
git commit -m "feat: 功能描述"
git push
```

### 2. 同步上游最新代码

```bash
git fetch upstream

# 更新 main
git checkout main
git merge upstream/main
git push origin main

# dev rebase 到最新 main
git checkout dev
git rebase main
git push --force-with-lease
```

### 3. 选择性合并上游功能到 dev

```bash
# 查看上游有哪些新 commit
git log dev..upstream/main --oneline

# 只挑选需要的 commit
git checkout dev
git cherry-pick <commit-hash>
git push origin dev
```

### 4. 发布 release

```bash
git checkout release
git merge --no-ff dev -m "release: vX.X.X"
git tag vX.X.X
git push origin release --tags
```

### 5. 提交 PR 给上游

```bash
# 从 upstream/main 创建干净分支
git checkout upstream/main -b fix/your-fix

# 只 apply 需要提交的文件变更
git diff upstream/main..<your-commit> -- <file> | git apply
git add <file>
git commit -m "fix: 描述"
git push origin fix/your-fix

# 在 GitHub 上从 yunchat/fix/your-fix → KylinMountain/main 创建 PR
```

---

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

| type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具等杂项 |

---

## 注意事项

- 不要直接向 `upstream` 推送
- 不要在 `main` 分支上直接开发
- `rebase` 后使用 `--force-with-lease`（比 `--force` 更安全）
- 提给上游的 PR 分支必须从 `upstream/main` 创建，只包含目标文件的变更
