# AI 判题真实延迟与失败率测量：flash×10＋gpt×10（l1004-26，a6b8 遗留1）

> 产线：执行班 l1004-26（2026-10-06 09:05-09:15，**平时段**执行——非峰时（14-18）符合「峰时不排」纪律；矿源建议的谷时未等，20 次小量纸面成本 ¥<0.5）。逐条留痕：`D:/code/tmp/shift-20261006/l1004-26/latency_results.json`（20 条，kind/i/pid/ms/fail/head80）。
> 禁 sol ✓；只跑 20 次不加量 ✓；C++/R 未跑（工具链缺）✓。

## §〇 环境面先行发现（真实失败面的第一层）

- **learning-system `.venv` 缺 `openai` 包**：第一次全量跑（venv 解释器）20/20 秒败（130-140ms），llm_call rc=2 逐字：`[llm_call] openai package not installed. Run: pip install openai`——**ai 真实链路在当前 venv 内根本不可用**（此前 a6b8「全走 stub」的上游原因）。禁装依赖 ⇒ 换 **D:/code 根 python**（openai 2.44.0＋yaml 均在位）重跑，20/20 成功。
- 结论：真实延迟数字绑定根 python 解释器；venv 修复（装 openai 或 docs 注明用根 python 起服务）属执行单另派。

## §一 20 条读数汇总（根 python，2026-10-06 平时段）

| 链 | n | min | p50 | max | 失败 |
|---|---|---|---|---|---|
| review×10（_FAST_CHAIN flash 先手，DeepSeek 官方） | 10 | 5,203ms | **6,005ms** | 8,884ms | **0** |
| grade_open_answer×10（_QUALITY_CHAIN gpt 先手，711ev gpt-5.6-terra；python 8＋agent_dev 2） | 10 | 8,486ms | **11,725ms** | 14,620ms | **0** |

- rc 留痕：探针经 review() 黑盒走（函数吞 rc 按设计），空文本/离线兜底文案「暂时不可用」作失败代理；**显式 rc 一条**：`$ python /d/code/scripts/llm_call.py --model flash --prompt "回复一个字：好" → 好；RC=0`。venv 跑的 rc=2 逐字见 §〇。
- n=20 只报序号统计（每链 n=10），**不撑分位数**（p50 为中位数，明示样本量）。
- 落点摘录（前 80 字，脱敏——题面/点评文本本身无个人数据）：20 条 head 全部非空，review 落点为中文点评段（R-3/R-4 合规形态），grade 落点含评分反馈；score 分布 95×1、100×9。

## §二 费用口径

- **纸面预估（执行前）**：flash 每次约 1.5K in＋350 out，DeepSeek 平段估 1.5/4.5 ¥/M ⇒ 10 次 ≈ ¥0.04；gpt-5.6-terra 每次约 2K in＋600 out 走 711ev 积分 ⇒ 10 次估 ¥0.1-0.3；合计上界 **¥0.5**。
- **余额/用量读数：未取**——查询需持 API key 直调厂商接口，触碰凭据红线（secrets 只读键名不读值纪律的延伸），以纸面估算替代并如实明示；精确用量可由主班在 DeepSeek/711ev 后台按 2026-10-06 09:05-09:15 窗口人工查。
- 实际消耗与预估同量级（全部单链一次成功，无重试放大）。

## §三 与 stub 读数偏差

- a6b8 全 stub：本地构造即时返回（0 网络延迟）⇒ **review 真实 p50 6.0s、grade 真实 p50 11.7s，stub 低估两个数量级**；grade（terra＋长 rubric prompt）约为 review（flash）的 2 倍。
- 判分体验含义：grade 11.7s p50/14.6s max 落在 TIMEOUT_SEC 预算内但贴近链预算（_CHAIN_BUDGET_SEC ~45s 设计合理）；若未来 flash 涨价/降速，grade 链 gpt→flash 的 flash 退路延迟同级。

## §四 边界

- 真网络调用共 20＋1（rc 留痕 smoke）＝21 次，无重试；venv 20 次秒败未产生计费（未达 API）。
- 禁改生产码 ✓（探针在宿主 tmp/shift-20261006/l1004-26/）。
