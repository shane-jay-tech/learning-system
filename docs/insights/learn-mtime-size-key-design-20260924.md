# 缓存键由 mtime 单因子加强为 (mtime, size)：改法草案

> 任务 l924-07 · 班 `qoder-executor-20260924-0955-learn23` · 2026-09-24 · **设计稿：零生产码改动、零测试件改动**。
> 收口 l923-19 result 的登记项（`zcode-bridge/done/l923-19.result.md:82-83`）：
> 「只比 mtime ⇒『改内容但把 mtime 复原』（`touch -r`、某些同步盘/回滚工具、zip 解包保留时间戳）不会失效。
> 加强版是 `(mtime, size)` 或内容哈希；**卷宗点名 mtime**，本单不外扩，留此登记。」
> 本档把那句"留此登记"变成可执行改法，并**实测**它的收益、代价与残留面。

## 一、现状与锚点复核

| 卷宗锚 | 磁盘实况 | 判定 |
|---|---|---|
| `ui/pages/mistakes.py:20 def _problem_yaml_mtime(...)` | :20 逐字命中 | ✓ |
| `:34 return os.path.getmtime(os.path.join(base, *parts) + ".yaml")` | :34 逐字命中 | ✓ |
| l923-19:82-83 那句登记 | `rg -n "touch -r"` → 命中 :82/:83 | ✓（非幻影） |

三处结构位置：键的组装在 **:52**（`key = (lang, pid, _problem_yaml_mtime(lang, pid))`）；
旧格剪枝在 `:39-48`（`_drop_stale_entries` 按 `k[0]/k[1]` 找同题、用 `k != key` 排除当前格 ——
第三元换成元组后这两处比较**都仍然成立**，实测见第五节"剪枝例仍绿"）；语义说明在 `:11-16` 注释块。

**生产码侧只有一个调用方**（:52）。完整读数（`rg -n "_problem_yaml_mtime" -g '!tmp/**' .`）＝
生产码 2 行（:20 定义／:52 调用）＋ `tests/test_mistakes_lookup_cache.py` 4 处直调
（:219/:220/:221/:223）＋ 本档自身 5 行（**自命中，属纪律档 §廿五 那类假阳，判读时已剔除**）。
⇒ 改返回形状的连带面只落在"键里第三元"这一处 ＋ 测试件那 2 条断言（第五节实测）。

## 二、撞键场景实测（草案要修的就是这一格）

取证脚本 `tmp/l924-07/probe.py`（gitignored）：造一帧真实 yaml → 首帧扫描 →
**改写内容使 size 变化（18B → 45B）并把 mtime 用 `os.utime(ns=…)` 按回原值** → 第二帧查同一题。
时间戳复原在每行输出里自证（`mtime复原=True`）。

| 场景 | 第二帧拿到 | `find_problem` 调用数 | 判定 |
|---|---|---|---|
| **A 现状（键里只并 mtime）** | **旧题面**（内容其实已改） | 1 | **撞键 ⇒ 新题面被吞**，就是 l923-19 那句话的落地复现 |
| **B 草案（键并 `(mtime_ns, size)`）** | 新题面 | 2 | 已失效，且只在 size 真变时多扫一次 |

同时补一条**反向守卫**（防"每次都重扫"骗绿）：size 与 mtime 都不动时，B 仍只扫 1 次（命中路径不退化）。

**残留面（必须一起登记，别让方案看着比实际更强）**——`tmp/l924-07/probe2.py` 用**等长改写**
（`title: 旧题面` → `title: 新题面`，UTF-8 实测两边都是 17 字符 / 落盘 18 字节）＋ mtime 复原：

| 实现 | 第二帧 | 重扫数 | 判定 |
|---|---|---|---|
| 现状（只 mtime） | 旧题面 | 1 | 仍撞键 |
| **草案（`(mtime_ns, size)`）** | **旧题面** | 1 | **仍撞键**（size 没变，加强键帮不上） |

⇒ 草案**严格优于现状**，但**不万能**；等长改写不需要刻意构造（真实题库 409 份 yaml、中位 750B，
改一个同宽汉字即命中）。这条残留的正解是内容哈希，代价见第七节。

## 三、改法草案（判据②上限 20 行；本草案实质 11 行 ＝ 6 加 / 5 删，整块含文件头与 @@ 共 19 行）

```diff
--- a/ui/pages/mistakes.py
+++ b/ui/pages/mistakes.py
@@ def _problem_yaml_mtime(lang: str, pid: str):
-    """题面 yaml 的 mtime；任何一环取不到都返回 None（退化，不抛错）。
+    """题面 yaml 的 (mtime_ns, size) 指纹；任何一环取不到都返回 None（退化，不抛错）。
 
-    pid 形如 `<lang>/<slug>/<stem>`（core/loader.py 的 `_build_problem` 是单源），
-    故题面文件 = 内容根/<lang>/<slug>/<stem>.yaml，直接 stat、不扫全表。
-    内容根单源取 core.loader 的默认目录，避免本文件再硬编码一份 content/ 路径。
+    两个因子来自**同一次** os.stat ⇒ 不会拿到"mtime 是新版的、size 是旧版的"这种撕裂键。
+    用 st_mtime_ns 而不是 st_mtime：后者是 float，进字典键靠二进制相等，ns 整数更稳也更好读。
     """
@@
     try:
-        return os.path.getmtime(os.path.join(base, *parts) + ".yaml")
+        st = os.stat(os.path.join(base, *parts) + ".yaml")
     except OSError:
         return None
+    return (int(st.st_mtime_ns), st.st_size)
```

四个设计选择，逐条给理由（都可被主班单独否掉而不影响其余）：

1. **`os.stat` 一次取两因子**，不用 `os.path.getmtime(...) + os.path.getsize(...)`。
   后者是两次系统调用，且**可能跨在并发写的两侧**（mtime 取到写后、size 取到写前）→ 生成一个
   永不复现的键 → 该题当帧起每次重扫。一次 stat 从根上排除这种撕裂，实测成本还低一半。
2. **`st_mtime_ns` 整数**而非 `st_mtime` 浮点：现值把 float 当键第三元（实测 `1790226075.7202117`），
   能工作是运气好（同一来源回读必等）；换 ns 后键可打印、可 diff、不依赖浮点相等语义。
3. **返回元组而非把两因子拼成一个 int**：`_drop_stale_entries` 与在册桩都是按**整键**比较，
   可读的元组让"键为什么变了"在失败信息里自解释（实测红名里就直接长这样：
   `('python', 'python/01_x/01_p', (1790226075720211800, 18))`）。
4. **函数名建议改为 `_problem_yaml_stamp`**（"mtime" 已不描述返回值）。改名会多带 4 个调用点
   （`tests/test_mistakes_lookup_cache.py:219/220/221/223`，全在同一个例里）；
   **不改名也能收**——上表 diff 就是不改名的版本，把它当第二步的可选动作即可。
   ⚠ 不改名的代价是"函数名撒谎"，属本仓在册的"注释/命名欠准"同族债（见 l924-08 遗留 2）。

`:11-16` 注释块第三行「缓存键第三元是题面 yaml 的 mtime」需同批改写（否则又是"注释为新缺陷背书"），
不计入上面的 11 行——它是一句文字，不是形状变更。

## 四、退化分支：卷宗说"任一取不到返 None"，实况更简单

卷宗「做什么」写的是「退化分支（**任一**取不到返 None 语义不变）」。
但两因子出自**同一次** `os.stat` ⇒ 不存在"mtime 取到、size 取不到"这种半取到的状态。
在册三条退化入口原样保留、语义一字不动：

| 入口 | 现实现位置 | 草案行为 |
|---|---|---|
| pid 不是 `<lang>/<slug>/<stem>` 三段式 | :28-29 | 返回 None（不变） |
| `lang` 与 pid 首段不符（不猜路径） | :28-29 同一条件 | 返回 None（不变） |
| 内容根属性缺失 | :30-32 | 返回 None（不变） |
| 文件已删 / `OSError` | :33-36 | 返回 None（不变） |

⇒ 键仍退化为 `(lang, pid, None)`，仍是"一次写入、进程内不失效"，**不会**变成"永远 miss"
（那会把 O(M+P) 打回 O(M×P)——这条由在册 `test_退化路径_题面yaml不存在时行为回到旧版且不抛错` 钉着，
实测在本改动下**仍绿**，见第五节）。

## 五、对在册用例的影响清单（实测红名集，不靠读代码猜）

先按卷宗判据①内联复核：

```bash
$ rg -n "mtime" tests/ | rg -c ""                       # 41 行命中，跨 3 个文件
tests/test_loader.py:73,111          # 2 行：core/loader 自己的签名 memo 用例，与本缓存无关
tests/test_mistakes_tabs_contract.py:5,17   # 2 行：纯散文提及，无断言
tests/test_mistakes_lookup_cache.py         # 其余 37 行全在这里 —— 本改动的唯一连带面
```

再用 `probe.py` 的 C/D 两步做**经验判定**：把第三节草案实现绑到 `mistakes_page._problem_yaml_mtime`
（`_lookup_problem` 走模块全局解析，因此这一替换等价于落地草案，**且不写任何文件**），
原样跑 `tests/test_mistakes_lookup_cache.py`：

| 步 | 读数 |
|---|---|
| C 绑上草案实现 | `2 failed, 11 passed` rc=1 |
| D 还原后复跑（= 当前 HEAD 基线） | `13 passed` rc=0，`helper 已还原 = True` |

红名**恰好两条**（其余 11 条全绿，含剪枝例、退化例、复杂度例、跨语言例）：

1. `test_mtime辅助_三段式pid映射到题面yaml_其余三类取不到` — 红在 **:219**
   `assert _problem_yaml_mtime("python", pid) == yaml_path.stat().st_mtime`（元组 ≄ float）。
   同例 :220/:221/:223 三条 `is None` 不受影响。
2. `test_mtime进键_改题面yaml后下一帧取新值` — 红在 **:240**
   `assert ("python", pid, yaml_path.stat().st_mtime) in cache`（键形状变了）。
   该例 :248 的承重断言"改题面后取到新对象"在草案下**仍成立**（mtime 也变了）。

⇒ 落地时要同批改的就是这 **2 行**（写法建议 `== (st.st_mtime_ns, st.size)` /
`("python", pid, (ns, size)) in cache`），加若干处散文/docstring（模块 docstring :2/:5/:13-16/:19/:24、
注释 :108、节标题 :194、例名里的 "mtime" 字样）。
**没有一条判据被放宽**：两条都是把"钉 mtime 形状"改成"钉 (mtime,size) 形状"，
且第六节会把覆盖面从"mtime 变"扩到"mtime 不变但 size 变"——净增一条守卫。

⚠ 一条纪律提示：本改动属"夹具钉住返回形状"型（纪律档 §廿三 那类两笔一体），
**只改生产码必然让 :219/:240 红** ⇒ 生产码与这两行必须同笔提交，不可拆。

## 六、撞键场景用例草案（可执行）

追加到 `tests/test_mistakes_lookup_cache.py`（复用本件现成夹具 `_content_root` / `_Problem`）：

```python
def test_同mtime不同size_改题面仍要失效(monkeypatch, tmp_path):
    """l924-07：改内容但把 mtime 原样按回（touch -r／zip 解包／同步盘回滚）。

    这是 mtime 单因子键的**唯一**残留收益面，故前置两条形同契约：
    时间戳必须真的复原了、size 必须真的变了——否则本例在假装测一个没构造出来的场景。
    """
    yaml_path, pid = _content_root(monkeypatch, tmp_path)
    st0 = yaml_path.stat()
    calls = []

    def fake_find(lang, pid_, content_dir=None):
        calls.append((lang, pid_))
        txt = yaml_path.read_text(encoding="utf-8")
        return (object(), _Problem("旧题面" if "旧" in txt else "新题面"))

    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)
    assert mistakes_page._lookup_problem("python", pid)[1].title == "旧题面"
    assert calls == [("python", pid)]

    yaml_path.write_text("title: 这是一个明显更长的新题面\n", encoding="utf-8")
    os.utime(yaml_path, ns=(st0.st_atime_ns, st0.st_mtime_ns))
    st1 = yaml_path.stat()
    assert st1.st_mtime_ns == st0.st_mtime_ns, "前置失效：mtime 没复原成功"
    assert st1.st_size != st0.st_size, "前置失效：size 没变，构造的是无关场景"

    assert mistakes_page._lookup_problem("python", pid)[1].title == "新题面", (
        "同 mtime 不同 size ⇒ 键必须 miss（只并 mtime 的实现会在这一行红，即本档第二节 A）")
    assert len(calls) == 2, "应重扫恰好一次"


def test_同mtime同size_仍按命中处理_不许退化成每次重扫(monkeypatch, tmp_path):
    """反向守卫：加强键不能变成"每次都 miss"。两因子都没动 ⇒ 仍只扫一次。"""
    yaml_path, pid = _content_root(monkeypatch, tmp_path)
    fake_find, calls = _fake_find_problem({("python", pid): (object(), _Problem("题面"))})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)
    for _ in range(4):
        mistakes_page._lookup_problem("python", pid)
    assert calls == [("python", pid)]
```

**这两条草案已按第二节 A/B 的同一套逻辑真跑过**（`probe.py`），读数为：现状下第一条红（拿到旧题面）、
绑上草案后第一条绿；第二条在两种实现下都绿（现状与草案都不重扫）。⇒ 草案不是纸面代码。
等长改写那条残留面**没有对应守卫**（第七节解释为什么刻意不钉它）。

## 七、为什么不顺手做到内容哈希（成本实数）

内容哈希能一并吃掉第二节的残留面，但它是**行为/成本**改动，不该由设计稿顺手带过去：

```bash
$ python -c "…os.stat 与 md5 各 409 份、3 轮取最好…"     # 见 tmp/l924-07 同批实测
每题 os.stat = 6.1 µs   （整库 409 份/帧 = 2.49 ms）
每题 md5(open().read()) = 152.5 µs   （整库 409 份/帧 = 62.36 ms）
倍率 = 25.1x
```

- 真实规模：`content/` 下 **409 份 yaml、共 385,542 B、中位 750 B**（哈希一遍不是零成本但也不贵）。
- 关键在于 `_lookup_problem` 是**每帧每题**都跑（页面 :114/:142/:169 三处调用），
  100 道错题的一帧就从 **0.61 ms → 15.25 ms**，全落在 streamlit 的重跑关键路径上；
  而 stat 版只要 0.61 ms。
- 而且键哈希**必须自己管失效**（哈希了才知道键，取键要先读文件 ⇒ 缓存本身省下的开销又被吃回去一半）。
- ⇒ 建议次序：**先 (mtime, size)**（2 元子、一次 stat、覆盖"同步盘/回滚/zip 解包"这一整类现实场景），
  等真出现"等长改写让开发模式看到旧题面"的实际反馈，再谈哈希（或退一步：给热重载钩子暴露
  `clear_lookup_cache()` —— 在册桩件 docstring :24 早就预告了这条出口，那是 O(1) 且零每帧成本的做法）。

## 八、影响面与不做什么

- **本档唯一受版产出是本设计稿 ＋ 索引两行**（表内 1 行、档头读数 1 条 bullet）；
  生产码 `ui/pages/mistakes.py`、测试件 `tests/*` **一字未动**（`git diff --numstat` 可复算）。
  取证脚本 `tmp/l924-07/probe.py`、`probe2.py`、`out.txt` 在 gitignored `/tmp/` 下，非在册资产。
- 探针全程只在内存里换模块属性、`tempfile.mkdtemp()` 造夹具，并把 `core.loader._DEFAULT_CONTENT`
  指向 tmp 后**还原**（`finally` 里复原，且复跑 D 步 13 passed 佐证没留下串台状态）。
- **未跑全量套件**：只读位按纪律档 §四.2 默认不跑；判据点名的是
  `tests/test_insights_index_closure.py`（已跑，绿）与"在册 mtime 用例影响"（已用定向口径实测红名集）。
- 待裁决三件（本档不代决）：① 是否落地本草案（连带第五节那 2 行同笔）；
  ② 是否同时执行第四节函数改名（多带 4 个调用点）；③ 是否给"每帧成本"设上限从而直接走第七节
  的 `clear_lookup_cache()` 出口。
