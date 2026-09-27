# l927-09 learning 通知/反馈文案一致性抽检（错别字／术语统一／中英混排）

> 班次：`qoder-executor-20260927-1520-learn46`（波次 21 只读采集子班）
> 现取时戳：2026-09-27T17:1x +08:00（`date` 现取，见 result「证据」节）
> 仓现值：HEAD `8ef64c6`、`git status --porcelain` **0 行**（开工前复跑，非引brief 的 `2665f0a`／锁志的 `9de1a34`——两者均已过时）
> 形状：**只读抽检，零文案改动**。文案属用户可见面，改动一律待人工放行。

---

## 一、文案清单计数（先命令后数字）

### 1.1 复跑命令（三条，均为只读）

```bash
# ① 通知/反馈调用点数（app.py + ui/components.py + ui/pages/*.py，剔注释行）
grep -rn "st\.toast\|st\.success\|st\.error(\|st\.warning\|st\.info(\|st\.exception\|render_notice(\|render_info_notice(\|render_success_notice(\|render_error_notice(\|render_empty_state(" \
  app.py ui/components.py ui/pages/*.py | grep -v ":[0-9]*: *#" | wc -l

# ② 学生错误反馈共用表槽位数（core/runners/error_feedback.py，AST 点名赋值，不靠 ast.walk 数碎片）
python -c "import ast,pathlib; t=ast.parse(pathlib.Path('core/runners/error_feedback.py').read_text(encoding='utf-8')); \
a={n.targets[0].id:n for n in ast.walk(t) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}; \
print('HINTS=',len(a['HINTS'].value.elts),' _HEADLINE=',len(a['_HEADLINE'].value.keys))"
```

### 1.2 现值

| 口径 | 数字 |
|---|---|
| ①通知/反馈**调用点**（复跑命令①） | **54** 处 |
| ②展开到「调用点 × 文案槽」的**文案条目**（AST：字面量实参＋f-string 归一＋三元式两档分列） | **101** 条 |
| ├ 面 A 通知块（`app.py` 1＋`ui/components.py` 0＋`ui/pages/*.py` 5 页＋`ui/*.py`） | **62** 条 |
| ├ 面 B 判题即时反馈组件（`verdict_banner`／`ai_feedback_block` 内 `st.markdown` 正文，HTML 标签剥除后计） | **3** 条 |
| └ 面 C 学生错误反馈共用表（`HINTS` 模板 25＋`_HEADLINE` 类目名 7（`none` 档空串不计）＋`_HINT_SEP` 1＋运行期话术模板 3） | **36** 条 |
| 复跑命令② | `HINTS= 25  _HEADLINE= 8`（8 键含空串 `none` ⇒ 计 7） |

⚠ **点名一处与卷宗不符**：卷宗写「抽全量反馈文案（≤100 条）」，磁盘现量 **101** 条。按 brief §3b「按磁盘实况收窄」，本单**全量抽、不截断**，超限 1 条如实登记，未为此删样本。

---

## 二、问题清单（14 条：P1–P13 ＋ P6b，只列不改）

严重度：🔴 需人工裁决（涉安全承诺／需改生产码才能治根）｜🟡 一致性缺陷（纯文案可改）｜🟢 措辞瑕疵。

### P1 🟡 同义词四个并存：判题／判定／评判／点评

同一条判题链上四个词轮着出现，学生无法区分是几件事：

| file:line | 现文案（节选） | 用的词 |
|---|---|---|
| `ui/pages/language.py:332` | 「📝 提交给 AI **评判**」 | 评判 |
| `ui/pages/language.py:352` | 「⏳ AI 老师正在**评判**你的回答…」 | 评判 |
| `ui/pages/language.py:360` | 「✅ 已**判定**，结果在下方」 | 判定 |
| `ui/pages/language.py:380` | 「AI **评判**服务暂时不可用。**判题**结果未记录」 | 评判＋判题（同句两词） |
| `ui/pages/language.py:401` | 「AI **点评**暂时不可用（不影响**判题**结果）」 | 点评＋判题 |
| `ui/components.py:179` | 「未通过 别灰心，看下面的对比和**点评**」 | 点评 |
| `ui/components.py:195` | 「AI 老师**点评**」 | 点评 |
| `ui/pages/language.py:353` | 「⏳ 正在运行代码并请 AI **点评**」 | 点评 |

**建议改法**：定两层单源——机器判＝「判题（结果）」，AI 评语＝「点评」；「判定」「评判」从可见面清除（`ui/components.py:38/44/55/58` 的 docstring 里的「评判结果」属内部注释，另计）。

### P2 🔴 「AI 不可用」同一件事写了 6 套话术，且其中 2 套会让现有分支静默失效

6 套措辞（**这是本单最硬的一条，不只是审美问题**）：

| file:line | 现文案 |
|---|---|
| `ui/pages/language.py:380` | 「⚠️ AI **评判**服务**暂时不可用**。判题结果未记录，请**稍后重试**。」 |
| `ui/pages/language.py:401` | 「AI **点评****暂时不可用**（不影响判题结果）。下一步：**稍后重新提交**即可获得点评。」 |
| `core/ai_review.py:288` | 「AI 点评**暂时不可用**（网络或服务异常），请**稍后再试**。判题本身不受影响。」 |
| `core/ai_review.py:352` | 「AI **暂时连不上**，请**稍后再问**。」 |
| `core/ai_review.py:382` | 「AI 老师**暂时连不上**，请**稍后再问**。」 |
| `core/ai_review.py:456`／`:514` | 「AI **评判****暂时不可用**（网络或服务异常），请**稍后再试**。」（两处逐字重复） |

**耦合实证**（本单新取证，非在册）：文案被子串当哨兵用——

- `ui/pages/language.py:379` 与 `:399`：`if "暂时不可用" in (r.ai_feedback or ""):`
- `core/ai_review.py:60`：`if not text or "暂时不可用" in text or not pid:`

⇒ `ai_review.py:352`／`:382` 用的是「**暂时连不上**」，**不在该哨兵覆盖集内**。这两路降级文案会：①在页面上走 `ai_feedback_block` 原样渲染（不触发那条统一 `render_notice` 提示），②在 `ai_review.py:60` 处仍会入缓存（`_REVIEW_CACHE` 跳过的判据只认「暂时不可用」），下次追问拿到脏的失败文本。
⇒ **任何文案统一动作都会改变这两个分支的行为**，属「改文案＝改逻辑」的耦合形状。

**建议改法（裁决条目，不开写位）**：
① 文案单源化：把 6 套收成 1–2 条常量（如 `core/copy.py::AI_UNAVAILABLE_STUDENT`／`AI_UNAVAILABLE_FOLLOWUP`），页面只引用；
② **同时**把子串嗅探换成显式标志位（`ReviewResult.ai_unavailable: bool`，或 `ai_feedback is None` 语义），否则第 ① 步本身就是行为变更；
③ 回归护栏：补 1 条断言「凡 ai_review 产出的降级串，必须被 language.py 的两处分支识别」的契约测试。
⇒ ②③ 属生产码＋测试位改动 ⇒ **停人工闸后**，本单只出材料。

### P3 🔴 同屏两条反馈语义互斥

`ui/pages/language.py:375`／`:386` 都会先渲染 `verdict_banner`（给出「通过！／未通过」），紧接 `:380` 又对学生说「**判题结果未记录**」。
⇒ 学生看到「未通过」的同时看到「结果未记录」，两句话互斥。
**建议改法**：`:380` 改为「AI 点评未记录（判题结论仍有效），请稍后重试点评。」——把「判题」与「点评」两个记录面分开点名。⚠ 依赖 P2 的语义澄清，建议一并裁决。

### P4 🟡 句末标点两套并存（可量化）

对 101 条逐条取末字符：

| 面 | 带「。」 | 带「！」 | 带「？」 | 无末标点 |
|---|---|---|---|---|
| A 通知块（62） | 9 | 1 | 0 | **52** |
| B 判题反馈（3） | 1 | 0 | 0 | 2 |
| C 共用表（36） | 6 | 0 | 1 | 29 |

同档内就分叉（`render_notice` 档）：`language.py:142`「请先在主页选择一门语言。」带句号，`home.py:201`／`:206` 不带。
**建议口径**：整句陈述带末标点；`render_error_notice` 的 title 槽与 `render_empty_state` 的 message 槽（会被拼成「{message} 下一步：{next_action}」）**不带**末标点，避免产出「…。 下一步：…」。现值：`render_empty_state` 的 12 个 message 槽零句号命中 ⇒ 属**预防性**口径，不是已发生的破损。

### P5 🟡 破折号：单「—」vs 双「——」两套并存（清单内 1:25；扩面后 7:25）

**在 101 条清单内**：用「——」的 25 条（`home.py:201/206` ＋ `error_feedback.py` 共用表 23 条），用「 — 」的**仅 1 条**：
- `ui/pages/dashboard.py:462`：「🎉 解锁新成就：**{icon} {title}** — {description}」

**扩面复跑（`st.markdown`／`section_title` 直写的可见文案，不在 101 条口径内）**——命令：
`grep -rn "[^—]—[^—]" app.py ui core --include=*.py | grep -v '"""'`
⇒ 另有 **6 条**同形分叉：`dashboard.py:636`（「`{pid}` — 逾期 N 天」）、`home.py:224`／`:225`／`:226`／`:238`（季度深查清单）、`path.py:128`（里程碑行「{title} — x/y 题」）。
⇒ 全站真实比例是 **单「—」7 处 vs 双「——」25 处**，不是「孤例」。（`dashboard.py:598` 的 `"—"` 是空值占位符、非文案，不计。）
**建议改法**：中文正文统一「——」；`dashboard.py:462` 与 6 条 markdown 一并收。

### P6 🟡 省略号**三套**形态并存（`...` 3 处／`…` 5 处／`……` 2 处）

复跑：`grep -rn '\.\.\."\|…[^…]\|……' app.py ui --include=*.py`（剔注释行）

| 形态 | 处数 | file:line |
|---|---|---|
| ASCII `...` | 3 | `language.py:297`「AI 正在出题（最长约 45 秒）...」、`:352`、`:353`（spinner_msg 两档） |
| 单 `…` | 5 | `dashboard.py:246`／`:255`「正在生成报告…」、`language.py:485`／`:543`／`:598`「AI 老师在想…（最长约 45 秒）」 |
| 双 `……` | 2 | `language.py:323`「用你自己的话作答……AI 老师会按评分标准给你点评。」、`:530`「…该用 for 还是 while……」 |

⚠ 最刺眼的是**同一个 `st.spinner` 用法内三套齐活**：`:297/:352/:353` 用 `...`，`:485/:543/:598` 用 `…`，全在 `ui/pages/language.py` 一个文件里。
**建议改法**：进度类（spinner）统一「…」，正文省略/悬念类统一「……」，`...` 从可见面清除。

### P6b 🟡 时长单位中英两套：`h` vs 「分钟」

- `ui/pages/path.py:65`「{subtitle} · 预计 {estimated_hours}**h** · {n} 个里程碑」
- `ui/pages/path.py:128`「{title} — {solved}/{total} 题 · **~**{estimated_hours}**h**」——除 `h` 外还多一个 ASCII 波浪号 `~` 当「约」用
- 其余全站用中文单位：`home.py:203`「约 30 分钟」、`home.py:208`「5 分钟看一眼」、`home.py:273`／`diagnostic.py:58`／`path.py:48`「约 2 分钟」、`language.py:297` 等「最长约 45 秒」
**建议改法**：`path.py:65/:128` 改「约 N 小时」，`~` 改「约」；与 P12-8 的「～」孤例一并定一条「波浪号不进中文文案」的规则。

### P7 🟡 中文清单用半角逗号 join（AST 抽不出来，属代码级取证）

- `ui/pages/path.py:135`：`st.info(f"建议先完成：{', '.join(prereq_names)}（可跳过）")` → 实际产出「建议先完成：函数与作用域, 分支判断（可跳过）」，中文专题名之间挂半角逗号。
- `ui/pages/diagnostic.py:99`：`f"还有 {n} 题未作答：第 {', '.join(map(str, unanswered))} 题。"` → 题号清单同形（数字场景较轻）。
**建议改法**：`'、'.join(...)`。另 `:99` 的「第 2、5 题」在 3 个以上未答时会读成序数，建议「第 2、5 题（共 2 题未作答）」或改「未作答题号：2、5」。

### P8 🟡 空态「下一步」里的栏目指向词与实际栏目名对不上（学生照做找不到地方）

| file:line | 文案里的指向词 | 全站实际栏目名 | 判定 |
|---|---|---|---|
| `ui/pages/dashboard.py:141` | 「回来看看**学习图**」 | 无「学习图」；最近的是 `:504`「📅 学习热力图（最近 13 周）」／`:139`「最近 14 天提交趋势」 | **查无此名**（全站 `学习图` 仅此 1 命中） |
| `ui/pages/dashboard.py:574` | 「展示**推荐效果漏斗**」 | `:564`「📈 推荐效果」 | 半对：多了内部指标名「漏斗」 |
| `ui/pages/dashboard.py:644` | 「展示**能力趋势**」 | `:641`「🎯 能力维度趋势（近 30 天）」 | 半对：省了「维度」 |

**建议改法**：文案里的栏目名与 `section_title` 逐字对齐（可加一条闭集校验测试：可见文案里出现的「📅/📈/🎯」类栏目名必须在 `section_title` 实参集合内——属测试位新增，停人工闸后）。

### P9 🟡 内部实现术语裸露给学生（7 处，分两档）

**A 档·受控且合理**（本机单人学习者＝操作者，保留）：
- `app.py:94`「route={route} 没有对应的页面渲染器」
- `ui/pages/path.py:87`「path_id={path_id} 不在路径表中」
- `ui/pages/language.py:146`「语言标识 {lang} 不在语言表（LANG_META）中」
- `ui/pages/language.py:156`「先在**内容目录**生成该语言题库」（指 `content/`）
- `ui/pages/home.py:42`「请移除环境变量 `RUNNER_SECURITY_MODE=public` 后重启」

**B 档·失控**（建议处理）：
- `ui/pages/dashboard.py:356`：`reason={exc}` 把**异常原文逐字**塞进「原因：」槽。导入失败抛的可能是英文 traceback／含绝对路径的 `sqlite3` 文本，与其余 6 处「作者手写过的受控术语」不同档。
  **建议改法**：`reason` 给一句中文引导＋把 `{exc}` 收进可折叠区并截断（如首 200 字符）。
- `core/runners/error_feedback.py:197`：「键「{0}」不在**字典/DataFrame** 列里——先确认列名拼写」。该条生效语言是 `_PY_LIKE`（python／agent_dev），但「DataFrame」是 pandas 术语，纯 Python 学生未必认得；且「列里」与「键」搭配拗口。
  **建议改法**：「键「{0}」不存在——检查 dict 的键名或 DataFrame 的列名拼写」。

### P10 🔴 安全提示文案与实况不符（与 `l927-05` G3、本波 `l927-11` F-1 同源）

- `ui/pages/home.py:55`（`render_info_notice`）：**「本系统的代码执行器使用 subprocess 隔离，适合本机单人学习。」**
- 在册否证：`docs/insights/l927-05-judge-security-review.md:86` 条目 **G3**——全仓 `core/runners/` 内 `rlimit`／`setrlimit`／Job Object／`CREATE_RESTRICTED_TOKEN` **零命中**，白名单＋PATH 收窄＋临时 cwd **不限制**学生代码用绝对路径读写文件、起 socket 出网；并点名 `README.md:64`「带**安全**与超时边界」为「口径与实现不符」。
- 本波 `l927-11` 的 F-1 只读取证再次复核到同一形状（见 `docs/insights/l927-11-fs-constraint-adjudication.md`，同班同波）。
⇒ 「**隔离**」这个词是当前文案里**最强的过度承诺**，且它出现在「安全提示（仅显示一次）」这种学生只会读一遍的位置。
**建议改法（只出文案，不改文件）**：「本系统的代码执行器用**子进程**运行你的代码，只限制**可用命令与超时**，**不限制文件读写与网络**。因此请只在本机单人环境使用。」
⚠ 双闸：①用户可见面 ②安全承诺口径 ⇒ **必须人工放行**，子班不自改。

### P11 🟡 同屏双反馈重复＋措辞分叉

判题后同一帧里 `st.toast`（`language.py:360`）与 `verdict_banner`（`components.py:171/177`）同时说同一件事，且用词分叉：
- toast：「❌ 未通过，看**下方**对比**与**点评」
- banner：「❌未通过 别灰心，看**下面**的对比**和**点评，再试一次。」
⇒ 「下方／下面」「与／和」两组分叉；信息重复。
**建议改法**：banner 承载完整引导语，toast 只留状态词（「❌ 未通过，结果见下方」）；或反过来。二者择一，别同屏两份。

### P12 🟢 措辞／符号瑕疵（8 条）

| # | file:line | 现文案 | 问题 | 建议 |
|---|---|---|---|---|
| 12-1 | `ui/pages/dashboard.py:338` | 「确需重导请重新导出一份内容不同的文件（或换一台机器操作）」 | 缺逗号断句；「重导」为生造缩略 | 「确实需要重新导入时，请换一份内容不同的文件（或换一台设备操作）。」 |
| 12-2 | `ui/pages/dashboard.py:173` | 「题库还没加载到推荐项；试着进入语言主页直接选题。」 | 动宾不搭（「加载到推荐项」） | 「推荐区还没有内容；进入语言主页直接选一道题即可开始。」 |
| 12-3 | `ui/pages/home.py:108` vs `ui/pages/language.py:190` | 「该专题**还没有**题目」／「该专题**暂无**题目」（下半句 `换个专题，或用 AI 出题生成一组` **逐字相同**） | 同状态两说法，且上句分叉下句同文 ⇒ 像复制漏改 | 统一为「该专题暂无题目」 |
| 12-4 | `ui/pages/dashboard.py:141`／`:364`／`:512` | 「还没有**任何**提交记录」／「还没有提交记录」×2 | 同页三处多一个「任何」 | 定一套（建议带「任何」，信息量更足） |
| 12-5 | `ui/pages/home.py:119` vs `ui/pages/mistakes.py:90` | 「**还没有**错题记录」／「**没有**错题也没有到期复习」 | 「还没有／没有」两套 | 统一「还没有」 |
| 12-6 | `ui/pages/home.py:215` | 「**✓** AI 进展已跟上。」 | 确认档符号两套：文案里 `✓`（U+2713）vs `components.py:172`／`language.py:360` 的 `✅`（U+2705） | 统一 `✅`（或统一 `✓`，与 `verdict pass` 的 CSS 图标一并定） |
| 12-7 | `ui/pages/language.py:380` | 「**⚠️** AI 评判服务暂时不可用…」 | `render_notice` 走 `st.warning`，Streamlit 自带 ⚠️ 图标 ⇒ **双 ⚠️** | 删文案里的 emoji，交给组件档位 |
| 12-8 | `ui/components.py:173` | 「通过！{timing}**继续保持～**」 | 全仓唯一「～」波浪号结尾，其余可见文案用「。」／「！」 | 改「。」，或全站定一条「鼓励语气用～」的规则 |

### P13 🟢 成就 vs 徽章 同卡两名

`ui/pages/dashboard.py:456` 标题「🏅 **成就徽章**（x/y）」，同卡内 `:465`「还没有解锁任何**成就**」＋「开始做题即可获得第一枚**徽章**」＋`:462`「解锁新**成就**」。
⇒ 同一物件两个名，且量词「枚」只出现在徽章侧。
**建议改法**：标题「成就徽章」保留，卡内一律「成就」；或全改「徽章」。**注意** `core/achievements.py` 与测试逐字钉着若干文案子串，改前先跑 `tests/test_achievements*.py` 定向核验（本班未跑，见遗留）。

---

## 三、如实零发现／否证掉的维度（别把没查到写成查到了）

| 维度 | 结论 | 依据 |
|---|---|---|
| **错别字** | **零发现** | 异形词／常见错别字扫描（其它/其他、己经/已经、做用/作用、应不/应该、反回/返回、布署/部署）：可见文案面 `其它` **0 命中**，`其他` 命中于 `core/diagnostic.py:67`（推荐 message，可见）与 `home.py:241`（深查清单 markdown）；3 处 `其它` 全在 docstring／行内注释（`dashboard.py:71`、`diagnostic.py:37`、`error_feedback.py:64`），**非用户可见，不计入文案缺陷**，仅作注释面登记。典型错字（己经/做用/应不/反回/布署）零命中。 |
| **中英混排：中文与 ASCII 词粘连（缺半角空格）** | **零发现** | 101 条全过正则 `[\u4e00-\u9fff][A-Za-z0-9_]` 与反向：命中 **0**。本仓「盘古之白」执行得很干净（`AI 老师点评`、`subprocess 隔离`、`README.md 的`、`4 个空格`、`len()` 等均带空格）。 |
| **中英混排：半角标点夹进中文句子（限 101 条清单内）** | **命中 1 条** | `home.py:201`「4 问自检 **+** 5 个信息源全过一遍」——中文句子里用 ASCII `+`。另有 `', '.join` 两处（P7）属运行期拼接、AST 抽不出，单列；`...`／`…`／`……` 与 `h`／`~` 的标点分叉在 `st.spinner`／`st.markdown`／`st.expander` 面上，**不在 101 条口径内**，见 P5／P6／P6b 的扩面复跑命令。 |
| **`render_empty_state` 的 message 槽带句号导致「…。 下一步：」** | **零命中** | 12 个 message 槽末字符均为汉字，P4 的口径建议属**预防性**。 |
| **`io_block` 的透传槽** | 已从清单剔除 | `ui/components.py:187` 的 `{safe}`／`{content}` 是学生输出的原样透传，非文案，探针显式排除（否则面 B 会虚增 1 条）。 |

---

## 四、待人工／遗留

1. **P2＋P3＋P10 三条属「改文案＝改行为」或安全承诺面**，需人工裁决后才能开写单；本单不动任何文案。
2. 本单**未跑**判题文案相关的既有钉串测试（`tests/test_achievements*.py`、`tests/test_error_feedback_rows.py`、`tests/test_dashboard_import_feedback.py` 等），因为并发窗内禁跑（同刻 kaoyan76／colony39／quant47 在别仓），改文案前必须现取基线。
3. **覆盖面**：面 A 只抽 `app.py` ＋ `ui/**` 的**通知档调用**＋面 C 共用表。P5／P6／P6b 三条已对 `st.markdown`／`st.spinner`／`st.expander` 做过**定点扩面抽查**（发现 6 处「—」＋5 处「…」＋2 处 `h`），但**未系统覆盖** `hero()`／`st.button`／`st.caption` 标签与 `core/report.py` 生成的报告正文。若要把文案一致性做成全站闭环，需另开一单扩面（建议先扩 `st.button`＋`st.caption`，那里最可能藏着「重试／再试」的第三套）。
4. 本档**未登索引**：`docs/insights/` 索引由 `tests/test_insights_index_closure.py` 哨兵把守（现 92/92 闭合，刚由主班补登），子班不代登 ⇒ **交主班代登本档与 `l927-10`／`l927-11` 两档**，交班后该哨兵会红 1 例（缺 3 行），属主班的账。

---

## 五、本档全量文案清单在哪

101 条逐条清单（file:line＋调用档＋槽位＋原文）由第一节复跑命令展开即得（AST 探针件在本班快照目录，收班自清）。
本档第二节的表已把**全部命中文题的原文逐字抄入**（未命中条目不占篇幅）；主班如需 101 行全清单，复跑第一节命令①＋把 `render_*`／`st.*` 实参按槽位展开即可复现，无需相信本档转述。
