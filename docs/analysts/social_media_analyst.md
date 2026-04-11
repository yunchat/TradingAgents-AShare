# 社交媒体/舆情分析师 (Social Media Analyst)

## 角色定位

分析个股相关舆情、涨停池及市场热门股票，判断短期市场情绪。

## 时间视角

固定**短期**（short，7 天窗口）

## 数据源

| 数据 | 工具/字段 | 说明 |
|------|-----------|------|
| 个股新闻 | `get_news` | 近 7 天个股相关新闻 |
| 涨停池 | `get_zt_pool` | 指定日期涨停股票池 |
| 雪球热门股票 | `get_hot_stocks_xq` | 雪球平台当前热门股票 |

数据优先从 `data_collector` 缓存池（`pool["news"]`、`pool["zt_pool"]`、`pool["hot_stocks"]`）读取，缓存未命中时并行调用上述工具。

## 分析逻辑

1. 并行获取个股新闻 + 涨停池 + 雪球热门股
2. 结合用户意图构建 horizon 上下文
3. 调用 LLM 生成舆情分析报告（`sentiment_report`）
4. 提取 `verdict` 和 `confidence`

## 输出

- `sentiment_report`：完整舆情分析报告
- `analyst_traces`：包含 agent 名、horizon、数据窗口（"7天"）、结论、置信度
