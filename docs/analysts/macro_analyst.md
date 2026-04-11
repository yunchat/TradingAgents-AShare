# 宏观分析师 (Macro Analyst)

## 角色定位

分析行业板块资金流向及近期相关新闻，判断宏观与板块环境对个股的中长期影响。

## 时间视角

固定**中期**（medium）

## 数据源

### 1. 行业板块资金流向

| 项目 | 内容 |
|------|------|
| 工具 | `get_board_fund_flow` |
| 缓存键 | `pool["fund_flow_board"]` |
| 底层接口 | akshare `stock_fund_flow_industry(symbol="即时")` |
| 数据来源 | 东方财富 `push2.eastmoney.com`（akshare 封装） |
| 输入参数 | 无（固定取即时数据） |
| 输出字段 | 板块名称、今日主力净流入-净额、今日主力净流入-净占比、今日超大单净流入、今日大单净流入等，返回前 10 名板块排名文本 |

### 2. 个股近期新闻

| 项目 | 内容 |
|------|------|
| 工具 | `get_news` |
| 缓存键 | `pool["news"]` |
| 底层接口 | akshare `stock_news_em(symbol=code)` |
| 数据来源 | 东方财富 `np-listapi.eastmoney.com`（akshare 封装） |
| 输入参数 | `ticker`（股票代码）、`start_date`（开始日期）、`end_date`（结束日期，默认近 7 天） |
| 输出字段 | 新闻标题、文章来源、新闻内容（截取前 400 字）、新闻链接，最多返回 20 条 |

数据优先从 `data_collector` 缓存池读取，缓存未命中时并行调用上述工具。

## 分析逻辑

1. 获取今日行业板块资金流向 + 近 7 天个股新闻
2. 结合用户意图构建 horizon 上下文
3. 调用 LLM 生成宏观板块分析报告（`macro_report`）
4. 提取 `verdict` 和 `confidence`

## 输出

- `macro_report`：完整宏观分析报告
- `analyst_traces`：包含 agent 名、horizon、数据窗口（"板块数据"）、结论、置信度
