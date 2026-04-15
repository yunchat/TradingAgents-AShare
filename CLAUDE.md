# TradingAgents-AShare 项目规范

## 项目概述

A 股智能交易分析系统，基于多 Agent LLM 框架。核心模块：
- `tradingagents/` — Agent 逻辑、数据流、LLM 客户端
- `api/` — FastAPI 后端服务
- `scheduler/` — 独立调度进程
- `frontend/` — React 前端
- `tests/` — 测试脚本

## 技术栈

- Python 3.10+，包管理用 `uv`（不用 pip）
- LangChain + LangGraph 构建 Agent 图
- akshare / baostock / yfinance 数据源（优先级：akshare > baostock > yfinance）
- FastAPI + SQLite（生产可换 PostgreSQL）
- React + TypeScript 前端

## 开发规范

### 代码风格
- 最小化修改原则：只改动任务直接相关的代码
- 不添加不必要的注释、类型注解、错误处理
- 数据源接口修改后必须在 `tests/` 下有对应测试脚本验证

### 数据源优先级
- 历史 K 线：Sina (`stock_zh_a_daily`) → Eastmoney (`stock_zh_a_hist`) → Tencent (`stock_zh_a_hist_tx`)
- 实时行情：雪球 (`stock_individual_spot_xq`，需 `XQ_A_TOKEN`)
- Volume 单位统一为**股**（Tencent 的 `amount` 字段需 ×100）

### 环境变量
- 核心配置见 `.env.example`
- `XQ_A_TOKEN`：雪球实时行情 token，盘中数据必须
- `TA_APP_SECRET_KEY`：生产环境必须设置

---

## Git 工作流规范

> 详细规范见 `docs/GIT_WORKFLOW.md`

### 分支结构
```
upstream/main → origin/main（完全同步上游）
origin/main   → origin/dev（rebase，含独特功能）
origin/dev    → origin/release（merge --no-ff，稳定发布）
```

### Remote 配置
| Remote | 仓库 | 说明 |
|--------|------|------|
| `origin` | `yunchat/TradingAgents-AShare` | 个人 fork |
| `upstream` | `KylinMountain/TradingAgents-AShare` | 上游只读 |

### 必须遵守的规则

1. **开发在 `dev` 分支**，不在 `main` 直接开发
2. **提给上游的 PR** 必须从 `upstream/main` 创建干净分支，只包含目标文件变更
3. **rebase 后** 用 `--force-with-lease`，不用 `--force`
4. **发布 release** 用 `git merge --no-ff dev`，打 tag
5. **选择性合并上游功能** 用 `cherry-pick`，不整体 merge

### 同步上游流程
```bash
git fetch upstream
git checkout main && git merge upstream/main && git push origin main
git checkout dev && git rebase main && git push --force-with-lease
```

### 提 PR 给上游流程
```bash
git checkout upstream/main -b fix/your-fix
git diff upstream/main..<commit> -- <file> | git apply
git add <file> && git commit -m "fix: 描述"
git push origin fix/your-fix
# GitHub: yunchat/fix/your-fix → KylinMountain/main
```
