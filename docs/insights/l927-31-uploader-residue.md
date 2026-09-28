# 导入反馈 uploader 残留交互裁决材料（l927-31，只读位·零码改动）

- 任务：`zcode-bridge/done/l927-31.task.md`（班 `qoder-executor-20260928-0210-learn52`，2026-09-28）
- 盘面：`D:\code\learning-system` @ HEAD `4309041`，`git status --porcelain` 开工现取 = 0
- 合并上游：`zcode-bridge/done/l922-105-import-feedback-survive.result.md` ＋ `zcode-bridge/done/l923-09.result.md`
- 纪律：完成标准④明写「零码改动」⇒ 本班一行生产码未动；探针脚本落 `D:\code\tmp\qoder-executor-20260928-0210-learn52\`
- 环境：`streamlit==1.58.0`（`requirements-freeze.txt:173` 钉死；`requirements.txt:1` 允许 `>=1.32,<2`）

## 一、残留面到底是什么（两档合并＋现值盘态）

导入块现值（`ui/pages/dashboard.py:316-360`）：

| 行 | 内容 | 与残留面的关系 |
|---|---|---|
| `:317` | `with st.expander("📥 导入学习数据（换机器迁移）", expanded=False):` | 残留文件的**容器**；`expanded=False` 只是首帧默认，折叠态由前端按 element id 维持 |
| `:318` | `st.caption("导入会**合并**进当前数据…")` | 乙案的落字点 |
| `:319-320` | `uploaded = st.file_uploader(…, key="data_import_uploader")` | 固定 key ⇒「控件态由 key 持久化」的落点 |
| `:321` | `if uploaded is not None:` | 残留文件的直接可见后果：这一支**一直为真** |
| `:322` | `if st.button("确认导入", …):` | 按钮一直可点 |
| `:336-342` | `fp = hashlib.sha256(blob)…`；同指纹 ⇒ `render_notice("…已跳过重复导入…")` | l923-09 的防重；**提示写在 expander 体内** |
| `:344-354` | `import_json` → 记 `_import_consumed_fp` → 记 `_import_feedback` → 作废导出缓存 → `st.rerun()` | 成功回显被 rerun 吞，改由下一次渲染首行 `st.success` |
| `:114-117` | `_render_dashboard_body` 开头 `pop("_import_feedback")` ＋ `st.success(...)` | 成功提示在**页面最顶**，与文件所在位置分离 |

两档各说的那一半，合起来才是完整残留面：

1. **l922-105（防重之前）**：二次点击**真的会写库** ⇒ `attempts`/`learning_events`/`rubric_scores` 翻倍
   （`tests/test_data_portability.py` 把 append 表翻倍记为 by-design）。这一半已被 l923-09 封住。
2. **l923-09（防重之后）**：被拦那一帧**文件仍在、按钮仍可点**，只是只出提示。
   ⇒ 现在残留的是**可见性与心智负担**，不是数据风险：
   - ①文件不消失 ⇒ 用户读作「没导成功」或「还能再导一次」；
   - ②「已跳过重复导入」提示落在 expander **体内**（`:338`）⇒ 若那一帧 expander 是折叠的，用户点了按钮、
     库没写、**屏幕上也看不到任何解释**；
   - ③成功提示落在**页面顶部**（`:114-117`）⇒ 与「文件还躺在下面选择框里」形成矛盾信号。
3. **本班新点的耦合面（上游两档都没写）**：`_import_consumed_fp` 是**单槽**（`:337` 读、`:345` 覆盖，
   只记最后一份）。l923-09 遗留问题 3 说「A→B→A 第三次会放行」，但没点出：
   **正因为文件清不掉**，用户要导第二份必须先重新选择文件覆盖同一个 uploader 槽，
   所以单槽在现状交互下够用；一旦甲案让文件消失，「空框里重新选同一份 A」成为可达路径 ⇒ 单槽防重会漏。
   ⇒ 残留案与指纹槽是**同一裁决定里的两件事**，拆成两单会留下中间态缺陷。

## 二、控件态语义实测（对生产码注释的半句否证）

现值 `dashboard.py:332-335` 与 `tests/test_import_dedup.py:12-19` 都写着：
「控件实例化后 **pop/赋值**其 key 会抛 `StreamlitAPIException`，换 key 重建又会**每次导入留下一个陈旧
session_state 键**（＝§十二 点名的 `editor_*` 无界增长同型缺陷）」。
用 `streamlit.testing.v1.AppTest`（同进程假运行时、零网络、零落库、不 import 本仓模块）打四条，
streamlit 1.58.0 ＋ python 3.12.9：

| 探针 | 读数 | 结论 |
|---|---|---|
| 例2 实例化后**赋值** `st.session_state["upk"]=None` | `StreamlitAPIException: 'st.session_state.upk' cannot be modified after the widget with key 'upk' is instantiated.` | ✅ 成立 |
| 例1 实例化后 **pop** `st.session_state.pop("upk", None)` | `POP_OK(未抛)` | 🔴 **不成立**——注释把 pop 和赋值混为一句 |
| 例3 pop 之后下一帧读值 | `POP_OK(未抛)` ＋ `value_after_pop = None(已清)` | 服务端侧的值确实清掉了（⚠ 见下方外推限制） |
| 例4 换 key 重建 ×3 次点击后筛 `upk_*` | `['upk_1', 'upk_2']`（`upk_0` 不在列） | 见例5——**这个读数会骗人**，筛不到 ≠ 没驻留 |
| 例5 换 key 后对 `upk_0` 三口径复查（`probe_stalekey.py`） | 第1轮 `in`＝True 且仍可读出 `UploadedFile(...)`；第2轮同；**第3轮 `in`＝False、取值 `KeyError`**；迭代全长 6→7→8→**8** | 🔴 注释那半句**方向对、口径错**：换 key **确实会留陈旧键**（还会连着留约 2 帧），但**不是无界增长**——第 3 帧起被 stale-widget 回收，稳态驻留 ≈2 个 |

源码侧对照（`D:\Program\Lib\site-packages\streamlit\`，只读）：

- 守卫只挂在 `__setitem__`：`runtime/state/session_state.py:594-611`
  （`if widget_id in widget_ids or user_key in form_ids: raise StreamlitAPIException(...)`）；
  `__delitem__`（`:615-636`）**无同款守卫** ⇒ pop 不抛是结构性的，不是版本巧合。
- 陈旧键回收机制：`on_script_finished → _remove_stale_widgets`（`:866-906` 调用、`:906-953` 实现）删掉
  本轮未实例化的 **widget id** 条目；`:969-971` 另有一句
  `This prevents unbounded growth across long sessions with many stale widget IDs`，
  但它管的是 `_query_param_bound_widget_ids`（查询参数绑定集），**不是** user-key 条目本身。
  user key 要等它映射的 widget id 被清后才随之不可读 ⇒ 这正解释了例5 的「滞后约 2 帧」。
  迭代侧另有一层迷惑：`_keys()`（`:498-510`）会把 user key 经 `_get_widget_id` 映射成 widget id 露出，
  所以「按 `upk_` 前缀筛不到」既可能是已回收、也可能只是换了个名字——必须用 `in`／`[]` 复判。
- 官方文档化的「即使给了 key 也能 reset」杠杆：`elements/widgets/file_uploader.py` docstring `:358-362`
  「Changing `type`, `accept_multiple_files`, or `max_upload_size` resets the widget even when a key is
  provided」＋ id 计算 `:537-546` 的 `key_as_main_identity={"type","accept_multiple_files","max_upload_size"}`。

🔴 **外推限制（必须写进裁决前提）**：例3 只证明**服务端**值被清；`AppTest` 的「客户端」是测试桩，
不会像浏览器那样在同一 element id 重挂时把自己 React state 里的文件再送回服务端。
「文件从 uploader 里消失」这个**可见效果**属前端语义，只读路径上取不到 ⇒ 需日间人工浏览器窗验（§四）。

⇒ 一句话给主班：**甲案被引的两大代价都被夸大**——「pop 会抛」不成立（只有赋值会抛）、
「陈旧键无界增长」不成立（实测稳态驻留 ≈2 个，约 2 帧后被回收）；
但两项都**不是零代价**：赋值仍禁、陈旧键仍会短驻留。残留案的性质因此从
「做不到无痕」变成「做得到、代价很小，但**可见效果待浏览器验**」。

## 三、两案与代价

### 甲：key 重置清空（让文件消失）

- **甲-1 换 key**：`seq = st.session_state.get("_uploader_seq", 0)`，
  `key=f"data_import_uploader_{seq}"`，成功分支里 `st.session_state["_uploader_seq"] = seq + 1`（＋ `st.rerun()` 已在）。
  改动面：`dashboard.py` 导入块约 5 行；测试侧 FakeStreamlit 是 lambda 注入（`test_dashboard_import_feedback.py:82`），
  几乎零改桩。风险：①仍**不能赋值**当前帧的 key（例2 那半句是真的，pop 可以但不是赋值）；
  ②陈旧 user-key 会短驻留约 2 帧（例5 实测，稳态 ≈2 个，非无界）⇒ 若同屏另有按前缀扫 session_state 的
  审查件（§十二 那类），要认这条；③可见效果依赖 §二 的前端未证面。
- **甲-2 保 key、翻参与 id 的参数**（不新增 user-key，官方语义最正）：
  三个可用参数各有副作用——`type` 改可选扩展名、`accept_multiple_files` **会把返回值从单文件变 list**
  （最危险，直接改 `uploaded` 形状）、`max_upload_size` 改上限（仓内 `.streamlit/config.toml` 未设该键，
  走 streamlit 默认；翻 ±1MB 属「丑但无害」）。⇒ 甲-2 实际只有 `max_upload_size` 一支可用。
- **若判甲，必须同批定的两件配套**（否则甲比现状更糟）：
  ①单槽指纹升为有界集合（§一-③耦合面）；
  ②提示移出 expander 体（`:338` 的 `render_notice` 与成功回显同层），
    否则「文件消失了＋提示在折叠框里」＝用户既看不到成功也看不到原因。

### 乙：维持现状＋文案说明

- 改动面：`:318` 那句 caption 追加一行，例如
  「导入后这个文件会**留在选择框里**，这是正常的——再点一次『确认导入』不会重复写入；
  要导另一份，直接重新选择文件即可。」
- 零行为改动、零改桩、零 streamlit 语义依赖、一行可回退。
- 代价：①③两错觉不消除；②（提示在折叠框里）仍在。

### 推荐：**乙先落，甲登记为「浏览器验证前置」的待办**

理由三条：
1. 风险面不对称：现在**数据已经被防重保护**，残留只是可见性；乙改一行，甲要同时动 4 处
   （key／指纹槽／提示位置／测试桩）。
2. 甲的**收益前提未证**：若浏览器仍回送文件，甲-1 会退化成「每按一次就换一个 key、文件照旧在」，
   比现状更差，还会引来一轮陈旧键审查。
3. 可回退性：乙一行 caption 撤得掉；甲回退要四处同撤。
⇒ 若人工判「文件必须消失」，则**甲-1 ＋ 有界集合指纹 ＋ 提示出框**三件同批，不拆单。

## 四、需人工浏览器窗验的三条（可直接排的协议）

前置：`python app.py` 起面板（日间人工窗，非本班权限），备两份导出 JSON（A、B 内容不同）。

1. **甲-1 的可见效果**：导入 A 成功后，浏览器里 A 这个文件是否真的从选择框消失？
   判据：点「确认导入」两次 ⇒ 第二次是否变成不可点/无文件可提交。
2. **expander 折叠态与提示可见性**（现状即相关）：展开折叠框 → 导入 A 成功 → 页面回顶部成功条；
   此时折叠框是**展开还是折叠**？再点一次「确认导入」，「已跳过重复导入」那条 warning **在屏上看得见吗**？
   判据：看得见 ⇒ ②号缺陷只是"要多展开一次"；看不见 ⇒ ②号是**实际缺陷**，与甲乙之争无关，应单列。
3. **单槽漏面的可达性**：导入 A → 重新选择 B → 导入 B → 再重新选择 A → 导入 ⇒
   是否出现「A 那批被追加第二遍」（`attempts` 翻倍）。判据：面板顶部答题总数或导出 JSON 的行数对比。

复算读数字段：三条都只读 UI 与导出件，**不连生产库写路径**；若需查库，走只读 `mode=ro` 且以 size／sha 三点取样为准
（口径见 `l927-11-fs-constraint-adjudication.md`）。

## 五、顺带否证/订正（不另开档）

- `tests/test_import_dedup.py:5-6` 写「`ui/pages/dashboard.py:289-290` 的 `file_uploader`，任务书写的 :289
  逐字命中，未漂移」——现值 `:319-320`，**已漂**（该文件自 l923-09 起 +30 行）。该档只是头注，无断言受害。
- `l923-09.result.md` 证据段写 `render_notice` 住在 `ui/components.py:220`——现值 `:249`。
- `dashboard.py:332-335` 注释里那两半句错（pop 会抛／陈旧键无界）建议改写为
  「**赋值**会抛（源码守卫只挂 `__setitem__`）；pop 不抛但**前端可能仍回送文件**；换 key 的陈旧 user-key
  会**短驻留约 2 帧**后被 stale-widget 回收（实测稳态 ≈2 个，**非无界**），
  **该结论绑定 streamlit 1.58.0，requirements 允许 `>=1.32,<2`，
  升级或降级需重跑 `probe_uploader.py`＋`probe_stalekey.py`（**源码见本档 §七附录**，
  临时件已按横幅纪律自清）**」——本班未改（只读位）。

## 六、本单不动的东西

- `ui/pages/dashboard.py`、`ui/components.py`、`tests/**`：零改动。
- `docs/insights/learn-insights-index-20260918.md`：不改（主班随代提交补登）。
- `data/progress.db`：不连不写；探针全程用 AppTest 假运行时，未 import 本仓 `ProgressDAO`。

## 七、附录：探针源码（临时件已按横幅纪律自清，本附录即复跑口径）

复跑方式：把下面两段分别存成临时 `.py`（**不要落在仓根**），在仓库根
`PYTHONIOENCODING=utf-8 python <该文件>`；预期读数见 §二表。

```python
# probe_uploader.py —— 例1/例2/例3/例4
from streamlit.testing.v1 import AppTest
FILES = [("a.json", b'{"attempts": []}', "application/json")]
def _at(src):
    at = AppTest.from_string(src); at.default_timeout = 20; at.run(); return at
def _upload(at):
    at.file_uploader[0].set_value(FILES); at.run(); return at

POP_AFTER = """
import streamlit as st
up = st.file_uploader("f", key="upk", type=["json"])
if st.button("b", key="btn"):
    try:
        st.session_state.pop("upk", None); st.session_state["outcome"] = "POP_OK(未抛)"
    except Exception as e:
        st.session_state["outcome"] = f"{type(e).__name__}: {e}"
st.session_state["seen_none_after_render"] = (up is None)
"""
SET_AFTER = POP_AFTER.replace("st.session_state.pop(\"upk\", None)",
                              "st.session_state[\"upk\"] = None")
POP_BEFORE = """
import streamlit as st
if st.button("b", key="btn"):
    try:
        st.session_state.pop("upk", None); st.session_state["pop_outcome"] = "POP_OK(未抛)"
    except Exception as e:
        st.session_state["pop_outcome"] = f"{type(e).__name__}: {e}"
up = st.file_uploader("f", key="upk", type=["json"])
st.session_state["value_after_pop"] = "None(已清)" if up is None else f"仍有文件:{up.name}"
"""
KEYSWAP = """
import streamlit as st
seq = st.session_state.get("seq", 0)
up = st.file_uploader("f", key=f"upk_{seq}", type=["json"])
if st.button("b", key="btn"):
    st.session_state["seq"] = seq + 1
st.session_state["stale_keys"] = sorted(k for k in st.session_state if str(k).startswith("upk_"))
"""
for name, src in [("例1 pop", POP_AFTER), ("例2 赋值", SET_AFTER), ("例3 pop前置", POP_BEFORE)]:
    at = _upload(_at(src)); at.button[0].click().run()
    print(name, dict(at.session_state.filter_state))
at = _upload(_at(KEYSWAP))
for _ in range(3):
    at.button[0].click().run()
print("例4", at.session_state["stale_keys"], at.session_state["seq"])
```

```python
# probe_stalekey.py —— 例5（三口径复查，防「筛前缀筛不到」被误读成已回收）
from streamlit.testing.v1 import AppTest
SRC = """
import streamlit as st
seq = st.session_state.get("seq", 0)
up = st.file_uploader("f", key=f"upk_{seq}", type=["json"])
if st.button("b", key="btn"):
    st.session_state["seq"] = seq + 1
st.session_state["probe_present"] = "upk_0" in st.session_state
try:
    st.session_state["probe_value"] = repr(st.session_state["upk_0"])[:40]
except Exception as e:
    st.session_state["probe_value"] = type(e).__name__
st.session_state["iter_len"] = len(list(st.session_state))
"""
at = AppTest.from_string(SRC); at.default_timeout = 20; at.run()
at.file_uploader[0].set_value([("a.json", b'{"x": 1}', "application/json")]); at.run()
for i in range(1, 4):
    at.button[0].click().run()
    print(f"第{i}轮", at.session_state["probe_present"], at.session_state["probe_value"],
          "iter_len=", at.session_state["iter_len"])
```

表行正则探针（§二 I7/I8/I9 的复跑，与哨兵 `:38` 同型）：

```python
import re
_ROW = re.compile(r"^\|\s*(docs/insights/[^\s|]+)")
txt = ('| docs/insights/real-a.md | x\n'
       '   | docs/insights/indented-b.md | x\n'
       '```\n| docs/insights/fenced-c.md | x\n```\n'
       '| ./docs/insights/dot-d.md | x\n'
       '| docs/Insights/mixed-e.md | x\n'
       '| docs/insights/space f.md | x\n')
print([m.group(1) for ln in txt.splitlines() for m in [_ROW.match(ln)] if m])
# 实测：顶格行命中／缩进行不命中／围栏内示例行命中／'./' 不命中／混大小写不命中／含空格截到空格前
```

