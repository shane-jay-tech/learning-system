# learning 散落 st.warning/info/error/success 裸用普查（2026-09-19 日间续班，任务 l918-26，只读零改动）

> 锚点：`learning-error-feedback-20260913.md:34`「其余散落 st.warning…如需统一，可另立 render_notice 双形态函数，留下批」——本普查为该批的前置材料。
> 复跑：`grep -rn "st\.warning\|st\.info\|st\.error\|st\.success" ui/pages/ app.py | wc -l` → **17**。
> 既有规范件：`ui/components.py:177 render_error_notice`（标题+原因+下一步三段式）与 `:220 render_notice`（信息条）。ui 代码在途 M，本单零触碰。

## 一、逐文件清单（17 处，file:line＋当前档位＋建议）

### diagnostic.py（4 处）

| file:line | 当前 | 内容摘要 | 建议 |
|---|---|---|---|
| diagnostic.py:31 | info | 「按第一感觉选择即可…不会限制后续课程」 | **合理保留**（引导语，非异常） |
| diagnostic.py:56 | warning | 「还有 N 题未作答：第…题」 | 合理保留（阻塞提醒，含具体缺号=可操作） |
| diagnostic.py:73 | success | 「诊断完成！答对 X/Y」 | 合理保留（完成反馈） |
| diagnostic.py:76 | info | rec["message"] | 合理保留（推荐结果展示） |

### language.py（1 处）

| file:line | 当前 | 内容摘要 | 建议 |
|---|---|---|---|
| language.py:347 | info | 「AI 点评暂时不可用（不影响判题）…稍后重新提交」 | **候选迁 render_notice**——「降级+下一步动作」形态正是 render_notice 的目标形态；但当前场景嵌在判题流程中间，迁移动纳入批内统一处理 |

### dashboard.py（3 处）

| file:line | 当前 | 内容摘要 | 建议 |
|---|---|---|---|
| dashboard.py:107 | info | 「题库还没加载到推荐项…」 | 合理保留（空态引导，测试已钉） |
| dashboard.py:236 | success | 导入完成统计 | 合理保留（操作成功反馈） |
| dashboard.py:338 | success | 「🎉 解锁新成就」 | 合理保留（庆祝语义，error_notice 无法表达） |

### path.py（2 处）

| file:line | 当前 | 内容摘要 | 建议 |
|---|---|---|---|
| path.py:45 | success | 「📋 诊断推荐：…」 | 合理保留 |
| path.py:135 | info | 「建议先完成：…（可跳过）」 | 合理保留（前置提示） |

### home.py（6 处）

| file:line | 当前 | 内容摘要 | 建议 |
|---|---|---|---|
| home.py:36 | **error** | 公开部署模式提示（代码执行禁用） | **保留裸用**——这是部署级硬阻断横幅，非「操作反馈」；error 档位正确 |
| home.py:45 | info | 安全提示（仅显示一次） | 合理保留（一次性公告） |
| home.py:179 | info | pulse 事件触发提示 | 合理保留 |
| home.py:185 | **error** | 「该做季度深查了」 | **候选降 warning**——提醒类非错误；但现有测试已钉 error 档（l918-19），迁移需同步翻桩 |
| home.py:190 | warning | 「该做月度浅扫了」 | 合理保留（提醒，档位正确） |
| home.py:197 | success | 「✓ AI 进展已跟上」 | 合理保留 |

### mistakes.py（1 处）

| file:line | 当前 | 内容摘要 | 建议 |
|---|---|---|---|
| mistakes.py:39 | success | 「没有错题也没有到期复习，做得不错！」 | 合理保留（正向空态） |

### app.py（0 处）

app.py 无裸用。

## 二、分级结论

1. **17 处中 15 处档位与语义匹配**（info/success/warning 用在引导/反馈/提醒上），裸用≠乱用；
2. 真正的「统一候选」仅 **2 处**：language.py:347（降级+下一步 → render_notice 形态）、home.py:185（error→warning 降档，须同步翻 l918-19 钉桩）；
3. home.py:36 部署横幅建议**保持裸 st.error**——render_error_notice 的「三段式错误卡」形态不适合全宽阻断横幅；
4. 若下批立 render_notice 双形态函数，迁移面按本清单为 2 处（其余 15 处维持），成本可控。

## 三、零改动声明

grep 只读普查；python -m pytest tests -q 前后数值不变（**441 passed, 7 skipped**）；ui 代码在途 M 零触碰；未 push。
