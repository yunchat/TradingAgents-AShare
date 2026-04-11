# 新闻分析师 (News Analyst)

## 角色定位

分析个股相关新闻及全球宏观新闻，判断短期新闻面对股价的影响。

## 时间视角

固定**短期**（short）

## 数据源

### 1. 个股新闻

| 项目 | 内容 |
|------|------|
| 工具 | `get_news` |
| 缓存键 | `pool["news"]` |
| 底层接口 | akshare `stock_news_em(symbol=code)` |
| 数据来源 | 东方财富（akshare 封装） |
| 输入参数 | `ticker`（股票代码）、`start_date`、`end_date`（默认近 14 天） |
| 输出字段 | 新闻标题、文章来源、新闻内容（截取前 400 字）、新闻链接，最多 20 条 |

### 2. 全球新闻

| 项目 | 内容 |
|------|------|
| 工具 | `get_global_news` |
| 缓存键 | `pool["global_news"]` |
| 底层接口 | akshare `news_cctv` |
| 数据来源 | 央视新闻（CCTV） |
| 输入参数 | `curr_date`（当前日期）、`look_back_days`（回溯天数）、`limit`（最多 10 条） |
| 输出字段 | 新闻标题、新闻内容（截取前 300 字）；当日无数据时自动回退查询最近 3 天 |

数据优先从 `data_collector` 缓存池读取，缓存未命中时并行调用上述工具。

## 分析逻辑

1. 读取个股新闻 + 全球新闻（14 天窗口）
2. 结合用户意图（`focus_areas`、`specific_questions`）构建 horizon 上下文
3. 调用 LLM 生成新闻面分析报告（`news_report`）
4. 从报告中提取 `verdict`（结论）和 `confidence`（置信度）

## 输出

- `news_report`：完整新闻分析报告
- `analyst_traces`：包含 agent 名、horizon、数据窗口、结论、置信度
