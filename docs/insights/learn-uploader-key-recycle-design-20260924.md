# learning 学习数据导入位：换 widget key 让「被拦帧」文件消失 ＋ 陈旧键有界回收 裁决稿（l924-22）

> 性质：**只出稿，零生产码改动**（`ui/` / `core/` / `tests/` 一字未动）。盘态实验全部在 `tmp/l924-22/` 的
> 探针里跑，不 import 生产模块、不连真实数据库、不启停 Streamlit 服务。
> 交主班的出口在 §七。取证时刻：2026-09-25T01:1x+08:00，learning HEAD `8da2dd9`，本机 streamlit **1.58.0**。

## 一、一句话结论

1. 「换 widget key 让被拦帧的文件消失」这条路**在真实 Streamlit 里确实成立**（实测：换 key 那一帧
   `file_uploader.value is None`）。
2. 但 l923-09 与生产码注释记下的代价自述——「每次导入在 `session_state` 留一个陈旧键（**无界增长**）」——
   **按字面读被否证**：用户可见的 `session_state` 键集**有界**（实测恒为 1，脚本内当帧最多 2），
   真无界的不是它，而是 Streamlit 内部两张按 key/id 记账的表（`KeyIdMapper` 双向映射 ＋ `widget_metadata`），
   实测每换一个新 key 各 **+1 条、不复用、不回收**。
3. 所以「陈旧键回收」不需要自写回收逻辑，**只要给 key 取模**（`v{gen % N}`）即可把这两张表的上界从
   「导入次数」钉成常数 N。实测 N=2 就能同时保住「文件消失」与「上界=2」。
4. 顺带否证第二条在册自述：**「pop/赋值已实例化控件的 key 会抛 `StreamlitAPIException`」在 1.58.0 未复现**
   （pop / 赋值均不抛，pop 后下一帧 value 为 None）。这条路可用与否**取决于真浏览器端**是否把文件重新回报，
   本单测不到（见 §六）。

## 二、锚点复核（卷宗三处前提逐条实测）

| 卷宗前提 | 实测结果 | 取数命令 |
|---|---|---|
| `zcode-bridge/done/l923-09.result.md` 有那段「换 widget key 代价＝陈旧键无界增长、本单未做」 | **在**（该文件「遗留问题」段，命中 5 行含「陈旧键」「无界增长」「换 widget key」） | `grep -n "widget key\|陈旧键\|无界增长" D:/code/zcode-bridge/done/l923-09.result.md` |
| `ui/pages/dashboard.py:318` 是「# 导入成功后 file_uploader 的控件态由 key 持久化…」 | **行号已漂**：该注释现落 `:328`，`if st.session_state.get("_import_consumed_fp") == fp:` 现落 `:337`（卷宗写的 `:327`）。语义与文本逐字仍在 ⇒ 前提成立，行号不可引 | `grep -n "_import_consumed_fp" ui/pages/dashboard.py` |
| 防重门是**按内容指纹**（同字节第二次确认只提示不写库） | **在**，且既有 4 例看守（`tests/test_import_dedup.py`，含「防重是内容级不是一次性锁」「失败不留指纹」两条判别力例） | `grep -c "^def test_" tests/test_import_dedup.py` |

**本稿一律只用唯一文本锚点、不写行号**（同文件历史上两单因插入把注释推走 +6/+10 行）。

## 三、完成标准 ①：无界增长复算（两轨，M 次实测）

### 3.1 页内轨（FakeStreamlit 实测，现行实现＝key 恒定）

用仓内既有假件跑 **M=8 次内容各不相同的成功导入**，逐帧取 `session_state` 键集：

```
$ PYTHONIOENCODING=utf-8 python -m pytest tmp/l924-22/probe_footprint.py -q -s
导入次数  session_state 键数  相对首帧新增键
      1                3  ['_import_consumed_fp']
      ...（2..8 行完全相同）...
      8                3  ['_import_consumed_fp']
```

读数：**8 次导入后净新增 1 个键**，键名固定、逐次覆盖 ⇒ 现行方案的页内足迹与导入次数**无关**。

### 3.2 框架轨（真实 Streamlit 1.58.0 会话，AppTest，M=20 帧「每次导入换一个新 key」）

```
$ PYTHONIOENCODING=utf-8 python tmp/l924-22/probe_internal_tables.py
run in_script outer_uploader _old_state key_id_map w_meta outer_total
   0         1              1          1          1      1           1
   1         2              1          3          2      2           2
   2         2              1          3          3      3           2
   ...（此后每行 key_id_map / w_meta 各 +1，其余三列不动）...
  19         2              1          3         20     20           2
增长判据：in_script 末-首 = 1 ／key_id_map 末-首 = 19 ／_old_state 末-首 = 2
```

各列口径与结论：

- `in_script`：脚本内 `st.session_state.to_dict()` 里 `data_import_uploader*` 的个数。**饱和于 2**
  （当帧可见「上一帧那个陈旧键 ＋ 本帧新键」，下一帧就被清掉）。
- `outer_uploader`：脚本外合并态 `filtered_state` 的同前缀键数。**恒为 1**。
- `_old_state`：跨帧饱和于 3。
- `key_id_map` / `w_meta`：**线性 1:1 增长，20 帧 → 20 条**，这是唯一真的无界的两张表。

机制定位（读装的包，非本仓代码）：`streamlit/runtime/state/session_state.py` 的
`on_script_finished()` → `_remove_stale_widgets()` 每帧末尾按「本帧活动 widget id 集」剪枝，
所以**带值的用户键态会被回收**；但同一个函数里的 `WStates.remove_stale_widgets()` **只重写
`self.states`、不碰 `self.widget_metadata`**，`_key_id_mapper` 也无对应删除动作
（旁证：该文件另一处注释原话「This prevents unbounded growth across long sessions with many stale
widget IDs」只覆盖了 `_query_param_bound_widget_ids` 一张表）。

⇒ **对 l923-09 那句代价自述的修正口径**：代价不是「session_state 无界长」，而是
「**每个用过的 uploader key 在 Streamlit 内部永久留 2 条映射 + 1 个 metadata 对象**」。
量级很小（一次导入＝几十字节级），但**它确实不回收**，所以不能写成「有界」；写成
「可见键有界、内部 key↔id 映射按用过的 key 数线性增长」才准。

## 四、完成标准 ②：回收边界 N 值建议（含上界实测）

先证「换 key 真能达成目标」（A 对照＝现行实现，B 判别＝换 key）：

```
$ PYTHONIOENCODING=utf-8 python tmp/l924-22/probe_recycle.py
A 对照组（key 恒定 = 现行实现）
   上传后第 1 帧: STATE data_import_uploader__v0 FILE:learning_data_20260924.json
   再跑一帧（key 未变）: ... FILE:learning_data_20260924.json | uploader.value is None? False
B 判别组（导入后 gen+=1 ⇒ key 变）
   换 key 后那一帧: STATE data_import_uploader__v1 FILE:NONE | uploader.value is None? True
   再下一帧（应仍为空）: ... FILE:NONE
C 上界组（连导 12 次，每帧都换 key）
         不复用（M 个不同 key）: key_id_map= 12 widget_metadata= 12 可见键=1
                 模 2 复用: key_id_map=  2 widget_metadata=  2 可见键=1
                 模 4 复用: key_id_map=  4 widget_metadata=  4 可见键=1
                 模 6 复用: key_id_map=  6 widget_metadata=  6 可见键=1
```

**建议：`N = 2`（模 2 复用），实现形态 `key = f"data_import_uploader__v{gen % 2}"`，`gen` 只在
「导入成功」分支自增。** 依据：

1. 目标行为只要求**相邻两帧 key 不同**，N=2 已是满足该要求的最小值；实测 N=2/4/6 都能让被拦帧
   `value is None`。
2. 内部两张表的上界恰等于 N（`key_id_map` = N、`widget_metadata` = N），**与导入次数彻底解耦**——
   不需要「保留最近 N 个 key、其余删掉」这类自维护回收代码（那种代码既无删除接口可依赖，
   又会把回收正确性变成自己的债）。
3. 不建议 N=1：N=1 就是「永远不换 key」＝现行实现，文件不会消失（A 组实测）。
4. 若将来要「撤销上一次导入」再抬到 N=3；**本单不预留**（无对应用户诉求，属投机泛化）。
5. `gen` 本身要放 `session_state`（不是模块级变量），否则会跨会话串号；它自己占 1 个固定键，
   覆盖式写入，不构成增长面。

**与现行指纹门的取舍（这是本稿真正要裁决的东西）**：换 key 只解决「视觉上那行文件名还挂着」，
它**不替代**内容指纹门——两个机制解决的是两个问题：

| 机制 | 解决的问题 | 代价（实测口径） |
|---|---|---|
| 现行 `_import_consumed_fp` | 二次确认**不把只追加表翻倍**（数据正确性） | 页内 1 个固定键，与次数无关 |
| 换 key（模 2） | 被拦帧**不再显示那个文件**（可见性/可操作性） | 内部 2 条 key↔id 映射 + 2 个 metadata，上界=2；**且用户仍看不到「为什么刚才能点现在不能点」的说明** |

⇒ **推荐组合**：`指纹门保留不动` ＋ `key 模 2 轮换` ＋ `被拦帧提示文案不变`。指纹门是数据安全面，
换 key 是体验面，**不要因为换了 key 就删指纹门**（换 key 后用户重选同一文件仍会二次确认，
那正是 `test_guard_is_per_content_not_a_one_shot_lock` 守的场景）。

## 五、完成标准 ③：用例清单（草案，≥2 条；本单不写实现）

放件建议：`tests/test_import_dedup.py` 同族（复用 `tests/test_dashboard_import_feedback.py` 的
`_pkg / _Upload / _wire`，双侧 patch `dashboard_page.st` 与 `components.st`——只 patch 页面侧
就一条 warning 都录不到，是那个文件头注已点名的「绿灯零覆盖」坑）。

1. **TC-1（判别力例：换 key 真发生）**——同一份文件成功导入后，下一帧渲染时 `file_uploader`
   收到的 `key` kwarg **必须与上一帧不同**；再导一次后**必须回到第一次那个 key**（证模 2 而非单向递增）。
   做法：`_wire` 里把 `fake.file_uploader` 换成记录 `kw["key"]` 的闭包，取三次导入的 key 序列断言
   `len(set(seq[:2])) == 2` 且 `seq[2] == seq[0]`。
   ⚠️ 反向陷阱：**不得**用「`session_state` 里键的个数」当本例判据——模 2 下个数恒为 2，
   与「有没有真的轮换」无关，那样写是永绿。
2. **TC-2（回归护栏：指纹门不被换 key 顶掉）**——「同一文件导入 → 换 key → 用户重新选同一份文件 →
   第二次确认」这条路径上，三张只追加表行数必须**一字不动**，且出现「已跳过重复导入」提示。
   这条是 `test_second_confirm_on_the_same_file_appends_nothing` 的**加强版**（原版不重选文件，
   换 key 后新分支必须单独钉一次）。
3. **TC-3（上界自证，只读不写库）**——连导 8 次各不相同的包，断言 `gen` 只增长、
   `session_state` 里 `data_import_uploader*` 前缀键数 **恒 == 1**（假件按「当帧注册」建模）。
   作用是把「不无界」写成看守，防止后人改成 `v{gen}` 不复用。
   ⚠️ 本例只能守**页内侧**；Streamlit 内部 `key_id_map` 无公开接口，**测不到**，见 §六。
4. **TC-4（失败不留痕）**——导入抛异常那一帧 **不得**自增 `gen`（否则用户改文件重传会多换一次 key，
   白丢一格状态）。断言坏文件连按两次 `gen` 不变、错误提示仍恰好两条。

完成标准里「≥2 条用例草案」由 TC-1..TC-4 四条覆盖，其中 TC-1/TC-2 是核心（一条证新行为、
一条护栏旧行为）。

## 六、否证与未坐实面（要人工/浏览器才能定的，本单不判）

1. **否证 l923-09 的「session_state 留陈旧键（无界增长）」**：见 §三两轨实测。可见键有界（1/2），
   无界的是框架内部两张表。
2. **否证生产码注释「控件实例化后 pop/赋值它的 key 会抛 `StreamlitAPIException`」**：
   ```
   $ PYTHONIOENCODING=utf-8 python tmp/l924-22/probe_mutate_key.py
   ② 已挂文件态（被拦帧现场）：
       PHASE mutate value_is_none=False
       OK pop 控件 key 未抛异常
       OK 赋值控件 key=None 未抛异常
   pop 之后再跑一帧： ['PHASE render value_is_none=True'] | uploader.value = None
   ```
   （`st.session_state[key].clear()` 那条抛的是 `AttributeError: 'NoneType' object has no attribute 'clear'`，
   因为 `pop` 已经把键取走，不是 Streamlit 的门禁。）
3. 🔴 **未坐实：真浏览器里「服务端 pop 键」到底能不能让文件名消失。** AppTest **没有前端**，
   服务端删了状态下一帧自然是空；真实上传件的值在浏览器侧，Streamlit 的 file_uploader 有「重连后
   前端重新回报已选文件」的历史行为，**这条静态测不到**。⇒ 若采纳 §四的 pop 路线（本稿不推荐），
   必须补一次浏览器目检；本稿推荐的**模 2 换 key 路线不依赖这条**（换 key 后 widget id 变了，
   前端那份文件与新 id 无对应）。
4. 🔴 **未坐实：`UploadedFileManager` 侧是否另有留存。** 上传字节的所有权在
   `streamlit/runtime/uploaded_file_manager.py`，它**按文件 id 而非 widget key** 记账，
   换 key 不改变它的生命周期；本探针只量了 SessionState 一侧的表。⇒ 若关心长会话内存，
   需另开一单量 file manager。
5. ⚠️ Streamlit 的 stale 剪枝时机是 `on_script_finished`，所以**当帧**内旧键仍可被读到
   （`in_script` 恒为 2 的原因）。任何「数 session_state 键」的断言都要写清取的是**哪一帧**，
   否则不同取法差 1。

## 七、交主班的出口

- 本稿**不改生产码、不改测试件**（卷宗「不改生产码」＋授权面只到 `docs/insights/**`）。
- 需要裁决的是：① 是否接受「被拦帧文件消失」这个体验改动（产品判断，l923-09 已推过一次）；
  ② 若接受，按 §四「模 2 轮换 ＋ 保留指纹门」实施，并**顺手订正** `ui/pages/dashboard.py` 那段
  注释里被否证的两句话（陈旧键无界增长／pop 必抛异常）——订正文本见 §三、§六，
  ⚠️ 改注释时**别在注释里写行号**（同文件已漂过 +10 行）。
- 索引登记已随本档同批完成（`docs/insights/learn-insights-index-20260918.md`，A==B 闭合，
  哨兵复跑见 result §验收）。

## 八、复算命令（终扫，全部本单实跑过）

```bash
# 索引闭合（完成标准 ④）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
# 三条对账口径（A 磁盘 / B 表条目 / C 未列项）
ls docs/insights/*.md | wc -l
grep -c '^| docs/insights/' docs/insights/learn-insights-index-20260918.md
# 本稿全部盘态证据（不连库、不启服务）
PYTHONIOENCODING=utf-8 python tmp/l924-22/probe_app_keys.py
PYTHONIOENCODING=utf-8 python tmp/l924-22/probe_internal_tables.py
PYTHONIOENCODING=utf-8 python tmp/l924-22/probe_recycle.py
PYTHONIOENCODING=utf-8 python tmp/l924-22/probe_mutate_key.py
PYTHONIOENCODING=utf-8 python -m pytest tmp/l924-22/probe_footprint.py -q -s
# 既有防重看守（本稿不动它，实施时要一起跑）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_import_dedup.py tests/test_dashboard_import_feedback.py -q
```

> `tmp/` 已在 `.gitignore`（`git check-ignore -v tmp/l924-22/probe_recycle.py` → `.gitignore:19:/tmp/`），
> 探针件不进 porcelain；主班代提交只收本档＋索引件。
