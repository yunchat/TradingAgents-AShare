# Git 开发工作流规范

本项目基于 Fork 工作流进行开发，个人开发在 fork 仓库的 `dev` 分支上进行，同时保持与上游同步。

## Remote 配置

| Remote | 仓库 | 说明 |
|--------|------|------|
| `origin` | `git@github.com:yunchat/TradingAgents-AShare.git` | 个人 fork，日常推送目标 |
| `upstream` | `git@github.com:KylinMountain/TradingAgents-AShare.git` | 上游仓库，只读同步 |

**验证配置：**
```bash
git remote -v
```

## 分支规范

| 分支 | 追踪 | 说明 |
|------|------|------|
| `main` | `origin/main` | 与上游保持同步，不直接开发 |
| `dev` | `origin/dev` | 主开发分支 |
| `feature/xxx` | `origin/feature/xxx` | 独立功能分支（可选） |

---

## 日常开发流程

### 1. 在 dev 分支开发

```bash
git checkout dev
# 开发...
git add <files>
git commit -m "feat: 功能描述"
git push                    # 推送到 origin/dev
```

### 2. 同步上游最新代码

```bash
# 拉取上游最新
git fetch upstream

# 更新本地 main
git checkout main
git merge upstream/main
git push origin main        # 同步到自己的 fork

# 将 dev rebase 到最新 main
git checkout dev
git rebase main
git push --force-with-lease  # rebase 后需要 force push
```

### 3. 开发独立功能（可选）

```bash
# 从 dev 创建功能分支
git checkout dev
git checkout -b feature/your-feature

# 开发完成后合并回 dev
git checkout dev
git merge feature/your-feature
git push origin dev

# 清理功能分支
git branch -d feature/your-feature
git push origin --delete feature/your-feature
```

---

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>: <描述>
```

| type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `refactor` | 重构（不影响功能） |
| `test` | 测试相关 |
| `chore` | 构建/工具等杂项 |

**示例：**
```bash
git commit -m "feat: 新增 smart money 数据源测试脚本"
git commit -m "fix: 修复龙虎榜日期边界问题"
git commit -m "docs: 补充数据时序问题待处理文档"
```

---

## 注意事项

- ⛔ **不要** 直接向 `upstream` 推送
- ⛔ **不要** 在 `main` 分支上直接开发
- ✅ PR 提给上游时，从 `yunchat/TradingAgents-AShare` 的功能分支发起
- ✅ `rebase` 后使用 `--force-with-lease`（比 `--force` 更安全）
