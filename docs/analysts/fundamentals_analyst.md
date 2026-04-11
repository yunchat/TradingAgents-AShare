# 基本面分析师 (Fundamentals Analyst)

## 角色定位

分析个股财务报表数据，从基本面角度评估公司中长期投资价值。

## 时间视角

固定**中期**（medium，财报周期）

## 数据源

| 数据 | 工具/字段 | 说明 |
|------|-----------|------|
| 基本面指标 | `get_fundamentals` | PE、PB、ROE 等估值与盈利指标 |
| 资产负债表 | `get_balance_sheet` | 季度资产负债表 |
| 现金流量表 | `get_cashflow` | 季度现金流量表 |
| 利润表 | `get_income_statement` | 季度利润表 |

数据优先从 `data_collector` 缓存池（`pool["fundamentals"]`、`pool["balance_sheet"]`、`pool["cashflow"]`、`pool["income_statement"]`）读取，缓存未命中时并行调用上述工具。

## 分析逻辑

1. 并行获取基本面指标 + 三张财务报表（季度频率）
2. 结合用户意图构建 horizon 上下文
3. 调用 LLM 生成基本面分析报告（`fundamentals_report`）
4. 提取 `verdict` 和 `confidence`

## 输出

- `fundamentals_report`：完整基本面分析报告
- `analyst_traces`：包含 agent 名、horizon、数据窗口（"财报周期"）、结论、置信度
