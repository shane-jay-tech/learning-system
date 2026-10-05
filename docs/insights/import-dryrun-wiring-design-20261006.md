# import_dry_run 预览接线设计（l1004-16；f1d8 遗留1/2/3）

> 产线：执行班 l1004-16（2026-10-06）。**设计稿，UI 接线属产品决策后另派**；差异注：l927-31 管 uploader 残留交互，本单管 dry-run 插入拓扑。

## §一 插入点两侧行号（dashboard.py 导入流现值）

导入链（`ui/pages/dashboard.py`，`确认导入` 按钮回调内）：
- **上游防重**：`:396 fp = hashlib.sha256(blob).hexdigest()` → `:397-402` `_import_consumed_fp` 命中即跳过（l923-09）；
- **下游真导入**：`:403 stats = import_json(dao, raw)` → 指纹登记/缓存作废/`st.rerun()`。
- 预览插入位＝**`:396` 指纹计算之后、`:403` import_json 之前**（f1d8 指定拓扑）：先花指纹去重，再做只读体检，体检通过才进真导入。

## §二 接线设计

```python
fp = hashlib.sha256(blob).hexdigest()
if st.session_state.get("_import_consumed_fp") == fp:
    ...  # 现防重分支不动
else:
    # —— 新增：dry-run 预览（只读，失败不阻断）——
    try:
        from scripts.import_dry_run import inspect_payload, _content_index
        import json as _json
        con = sqlite3.connect(dao.db_path)          # 只读体检；用独立连接，不动 dao 事务态
        con.execute("PRAGMA query_only=ON")
        rep = inspect_payload(_json.loads(raw), con, _content_index())
        con.close()
    except Exception:
        rep = None                                   # 预览失败 ⇒ 记一条 notice，继续走导入
    if rep:
        if rep["errors"]:
            st.error("dry-run 体检发现结构问题，已停止导入：" + "；".join(rep["errors"][:3]))
            st.stop()                                # 结构错误＝导入必败，阻断有据
        # 非阻断呈现（不新增复杂态）：一行摘要 + expander 明细
        merge = rep.get("merge", {})
        st.caption(f"dry-run 预览：attempts +{merge.get('attempts', 0)} / events +{merge.get('learning_events', 0)}"
                   f" / 状态覆盖 {merge.get('problems_status', 0)} 题"
                   f"{'；⚠️ ' + str(len(rep['duplicates'])) + ' 条重复' if rep['duplicates'] else ''}")
        with st.expander("体检明细", expanded=False):
            for k in ("fields", "encoding", "references", "illegal"):
                for item in rep.get(k, [])[:5]:
                    st.markdown(f"- {k}: {item}")
    stats = import_json(dao, raw)                    # 原导入路径零改动
```

- **回退口径（预览失败不阻断导入）**：inspect 抛任何异常 ⇒ `rep=None`，流程照旧直达 import_json——预览是**增强项**，坏了不挡迁移主路（与 l1004-01 Job Object「fail-open 降级」同一纪律）。
- **唯一阻断点**＝`rep["errors"]` 非空（`_validate` 结构失败）：此时 import_json 也必抛同错，提前阻断只是把异常文案变用户可读——不是新增否决权。
- **不新增复杂态**：预览结果只走当帧渲染（caption＋expander），不进 session_state；「确认导入→rerun→回显统计」既有闭环零触碰。
- **连接卫生**：体检连接必须 `PRAGMA query_only=ON`（dry_run 本体的 `open_ro` 语义）＋独立于 dao.conn，避免 streamlit 单连接态被体检污染。

## §三 version 下界校验加严点

- 现值：`core/data_portability.py:59` 只判 `int(version) > FORMAT_VERSION`（过新拒绝）——**version=0/负数/缺失（`get("version", 0)`）一律放行**（f1d8 指出，dry_run 沿用未加严）。
- 加严点（一处）：`:59` 前补 `if int(payload.get("version", 0)) < 1: return "导出文件版本过旧或缺失（version<1）"`。破坏性收益：`{"format":"learning-system-export","version":0}` 之类的半伪构造在结构校验即拒，不进 merge 面。断言影响：data_portability 测试 +1~2（version=0 拒/合法 version=1 过）。

## §四 边界

- 本稿零码；UI 接线（§二）＋version 加严（§三）主班拍板后可开执行单；§二代码块为设计形状非落盘件。
- scripts/import_dry_run.py 本体（:360 main／:134 inspect_payload）现值复核与 f1d8 记载一致，无需改动即可被 UI 侧 import 复用（`_content_index`/`inspect_payload` 均模块级可导入）。
