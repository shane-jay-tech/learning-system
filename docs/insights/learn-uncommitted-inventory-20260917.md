# learning 未提交改动盘点与提交就绪度（916p-a3-019，2026-09-17，只读）

## 一、M 项清点（命令与数字同段）

```
$ git status --porcelain | grep -cE '^ M'
14        ← 与任务书快照 14 一致；?? 另有 20 项（docs/insights 20 份已由 a3-017 入库收口）
```

## 二、逐项归属表（14 行＝M 项数）

| 路径 | 增删 | 最后触及提交 | 归属判定＋证据 |
|---|---|---|---|
| app.py | +20 | 629ccd2 | 9/13 UI 改造批（侧栏/首页/路由重构族） |
| core/achievements.py | +4 | b14a136 | 成就域跟随（a3-015 成就渲染桩对应的实现面） |
| core/ai_generate.py | +4 | b14a136 | AI 生成增强族（judge-edges 域） |
| core/ai_review.py | +7 | cdec1fe | AI 审阅增强族 |
| core/report.py | +9 | 629ccd2 | 报告导出跟随（9/13 UI 改造批） |
| tests/test_ergo_h912_13.py | +5 | 7cd3d73 | h912-13 工效批测试跟随 |
| tests/test_ui_behavior.py | +9 | 629ccd2 | UI 行为测试跟随（本班 a3-015 复用其 FakeStreamlit，未改它） |
| ui/components.py | +52 | 629ccd2 | 9/13 UI 改造批（组件库扩展最大头） |
| ui/pages/dashboard.py | +15 | a56be3d | h912-13 dashboard 工效跟随（本班 a3-015 补测的宿主文件） |
| ui/pages/home.py | +4 | 7cd3d73 | 9/13 首页改造 |
| ui/pages/language.py | +24 | 629ccd2 | 9/13 语言页改造 |
| ui/pages/mistakes.py | +2 | 629ccd2 | 9/13 错题本改造 |
| ui/pages/path.py | +8 | 629ccd2 | 9/13 路径页改造 |
| ui/styles.py | +9(约) | 629ccd2 | 9/13 样式系统改造 |

## 三、提交就绪（python -m pytest tests -q，同段）

```
$ python -m pytest tests -q
384 passed, 7 skipped in 29.22s      （failed=0；含 a2/a3 本夜新增 8+9 用例后的现值）
```

## 四、两栏结论

- **可立即提交**：14 项全部就绪（verify 全绿）——建议按三组分批：①UI 改造族（app.py＋ui/components＋ui/pages×6＋ui/styles，9/13 批）②core 增强（achievements/ai_generate/ai_review/report）③测试跟随（test_ergo_h912_13/test_ui_behavior）。
- **需日间拍板**：无强制项；仅提示 tests/test_ui_behavior.py 的 M 含 9/13 之后的追加，若与 ui 改造族分批提交注意先后。

## 五、验收对照

- ✅ M 计数 14 一致（同段）。
- ✅ 归属表 14 行＝M 项数，每行增删/最后提交/判定+证据。
- ✅ pytest 384 passed/7 skipped 同段。
- ✅ 两栏结论非空。零改动/零提交/零 stash；不 push。
