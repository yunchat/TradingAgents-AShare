# VPA 优化方案 v1.0

> 基于当前代码实现（`data_collector.py` + `volume_price_analyst.py`）的精确改造方案。

---

## 问题诊断

| # | 问题 | 当前代码位置 |
|---|------|-------------|
| 1 | 盘中量比未投影修正，10:00 量比 0.4 被误判为"背离" | `data_collector.py:114` |
| 2 | `vp_harmony` 阈值偏宽（`>1.0/<0.8`），缺少"异常(放量滞涨)"分类 | `data_collector.py:148-160` |
| 3 | `_intraday_label` 在渲染层才调用，导致 `vp_harmony` 计算时无法感知盘中状态 | `data_collector.py:189` |
| 4 | `HumanMessage` 历史+今日混为一块，LLM 受近因效应干扰 | `volume_price_analyst.py:52-57` |
| 5 | `_market_phase_note` 只说"信号不稳定"，未告知 LLM 量比已投影修正 | `volume_price_analyst.py:10-22` |

---

## 改动一：`data_collector.py`

### 1.1 新增 `_get_progress_factor`（放在 `_intraday_label` 之后）

```python
def _get_progress_factor() -> float:
    now = datetime.now()
    m = now.hour * 60 + now.minute
    if m <= 570: return 0.05
    if m <= 690: return max(0.05, (m - 570) / 240.0)
    if m < 780:  return 0.5
    if m <= 900: return (120 + (m - 780)) / 240.0
    return 1.0
```

### 1.2 `_compute_vpa_indicators`：提前调用 `_intraday_label`，投影修正最后一行

将原来 `data_collector.py:189` 的 `_intraday_label()` 调用**移到** `volume_ratio` 计算之后、`vp_harmony` 之前：

```python
df["vol_ma"] = df["volume"].rolling(window).mean()
df["volume_ratio"] = df["volume"] / df["vol_ma"]

# ── 盘中投影修正（只修正最后一行今日数据）──
intraday_label, is_intraday = _intraday_label()   # 从 L189 移到这里
today_str = cn_today_str()
if is_intraday:
    last = df.iloc[-1]
    last_dt = last.get("date", "")
    last_dt_str = last_dt.strftime("%Y-%m-%d") if hasattr(last_dt, "strftime") else str(last_dt)
    if last_dt_str == today_str:
        df.at[df.index[-1], "volume_ratio"] /= _get_progress_factor()
```

### 1.3 替换 `vp_harmony` 为威科夫矩阵（替换 `data_collector.py:148-160`）

```python
vr  = df["volume_ratio"]
pct = df["pct_change"]
df["vp_harmony"] = np.select(
    [
        (pct >  0.005) & (vr > 1.2),
        (pct >  0.005) & (vr < 0.7),
        (pct < -0.005) & (vr > 1.2),
        (pct < -0.005) & (vr < 0.7),
        (pct.abs() <= 0.005) & (vr > 1.8),
    ],
    [
        "一致(量增价涨)",
        "背离(量缩价涨)",
        "一致(量增价跌)",
        "背离(量缩价跌)",
        "异常(放量滞涨)",
    ],
    default="中性(量价均衡)",
)
```

### 1.4 渲染层：`is_today_row` 标注 `(预估)`（修改 `data_collector.py:221-225`）

```python
if is_today_row:
    dt += intraday_label
    vr_label += "(预估)"
    harmony = row["vp_harmony"] + "[预估]"
    has_intraday_row = True
else:
    harmony = row["vp_harmony"]
```

脚注改为：
```python
lines.append("\n> [预估] 量比已按时间进度投影修正，收盘后自动还原为真实值")
```

---

## 改动二：`volume_price_analyst.py`

### 2.1 盘中时解耦 HumanMessage（替换 `volume_price_analyst.py:50-58`）

```python
phase = cn_market_phase()
is_intraday = phase in ("in_session", "lunch_break")

if is_intraday and isinstance(vpa_data, str) and "\n" in vpa_data:
    vpa_lines = vpa_data.splitlines()
    # 脚注行以 "> " 开头
    fn_idx = next((i for i, l in enumerate(vpa_lines) if l.startswith("> ")), len(vpa_lines))
    history_part = "\n".join(vpa_lines[:fn_idx - 1])
    today_part   = "\n".join(vpa_lines[fn_idx - 1:])
    human_content = (
        f"以下是 {ticker} 在 {current_date} 的量价分析（数据窗口：{data_window}）。\n\n"
        f"### 第一部分：历史量价背景（已确认数据）\n{history_part}\n"
        f"> 请先评估历史区间整体趋势：底部吸筹、放量拉升、还是高位派发？\n\n"
        f"### 第二部分：今日盘中动态快照（量比已按时间进度投影修正）\n{today_part}\n"
        f"> 对比历史背景，今日预估量能是增强了趋势，还是产生了异动？\n\n"
        f"【原始 K 线数据参考】\n{stock_data}"
    )
else:
    human_content = (
        f"以下是 {ticker} 在 {current_date} 的量价分析预计算数据（数据窗口：{data_window}）。\n\n"
        + _market_phase_note(current_date)
        + f"{vpa_data}\n\n"
        f"【原始 K 线数据参考】\n{stock_data}"
    )

messages = [
    SystemMessage(content=horizon_ctx + system_message + "\n\n请全程使用中文。"),
    HumanMessage(content=human_content),
]
```

---

## 改动范围汇总

| 文件 | 改动 | 净增行数 |
|------|------|---------|
| `data_collector.py` | 新增 `_get_progress_factor` | +8 |
| `data_collector.py` | 投影修正逻辑（移动 `_intraday_label` 调用 + 修正最后一行） | +8，删 L189 |
| `data_collector.py` | 威科夫矩阵替换 `vp_harmony`（4层嵌套 → `np.select`） | 改 13 行 |
| `data_collector.py` | 渲染层 `(预估)` 标注 + 脚注 | 改 3 行 |
| `volume_price_analyst.py` | 盘中解耦 HumanMessage | 改 10 行 |

---

## 效果对比

| 场景 | 优化前 | 优化后 |
|------|--------|--------|
| 13:40 涨1.7%，原始量比0.8 | 背离(量缩价涨)，结论：反弹无力 | 一致(量增价涨)[预估]，结论：预估全天放量，承接有力 |
| 10:00 跌2.0%，原始量比0.4 | 背离(量缩价跌)，结论：空头枯竭 | 一致(量增价跌)[预估]，结论：开盘30分钟已达全天预估1.6倍，恐慌杀跌 |
| 收盘后量比0.8，涨1.7% | 背离(量缩价涨) | 背离(量缩价涨)（`is_intraday=False`，progress=1.0，自动还原） |
