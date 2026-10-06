# demo 站 file:// 直开行为取证：三层面分级＋README:39 对照（l1004-18，75ea 遗留5）

> 产线：执行班 l1004-18（2026-10-06）。**底稿型**——README/OPERATIONS/INVENTORY 三处「未验证」措辞改不改交主班，本单不改正文。
> 方法：headless Edge（`msedge --headless=new --enable-logging=stderr --dump-dom`，Chromium 真内核）以 `file:///D:/code/learning-system-demo/index.html` 直开；WASM 层用等价复现页（宿主临时件 `tmp/shift-20261006/l1004-18/probe-file*.html`，走 runners.js 同款 CDN 加载链）真触发。

## §一 层1 结构/样式：加载成功 ✓

- `--dump-dom` 输出（dom_dump.html 5,385B）含完整结构：`.hero`／`#lang-nav` 五导航钮／`.grid` 五卡（agent_dev/python/sql/r/cpp）。其中 **`.grid` 卡片是 app.js renderHome 的产物**（静态 index.html 的 main 为空挂载点）——见层2。
- 样式：styles.css 相对引用（同目录 file:// 子资源，不受 CORS 约束），控制台**零样式/资源加载错误**；Edge Tracking Prevention 仅对 CDN 脚本报 storage 拦截 INFO（非阻塞错误，逐字：「Tracking Prevention blocked access to storage for https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js.」×4）。

## §二 层2 JS 执行：成功 ✓

- dom_dump `:52-57` 出现 `<div class="grid"><div class="card" data-lang="agent_dev">…×5 卡`——**app.js 已执行并完成首页渲染**；data.js/runners.js/app.js 三脚本无一条报错进控制台。

## §三 层3 WASM：**意外反转——file:// 下可跑，README:39 自述被实测否证**

等价复现页（runners.js:35-38 同款 URL：`cdn.jsdelivr.net/pyodide/v0.26.4/full/`＋`sql.js@1.10.3/dist`）真触发结果：

```
$ msedge --headless=new --disable-gpu --enable-logging=stderr --virtual-time-budget=30000 \
    --dump-dom "file:///D:/code/tmp/shift-20261006/l1004-18/probe-file2.html"
→ PY_RUN_OK sum(range(10))=45        （Pyodide 0.26.4 真加载＋真执行 Python）
→ SQL_RUN_OK sum=42                  （sql.js 1.10.3 WASM 真加载＋SQLite 建表求值）
→ 控制台 CORS 错误：0 条（rg "CORS|Access to fetch" 仅 0 命中；全程仅 9 条 Tracking Prevention INFO）
```

**机理**：矿内静态推断「WASM 取回受 CORS 限制」的前提是 CDN 不带 CORS 头；实测 jsdelivr 全线 `Access-Control-Allow-Origin: *`，file:// 的 null origin 也在 `*` 豁免内 ⇒ fetch WASM 不被拦。README:39「直接双击 index.html…浏览器会拦截 WASM 运行环境，Python/SQL 跑不起来」在本引擎（Edge headless＝Chromium 真内核）＋本 CDN 组合下**不成立**。

### 边界（措辞订正时须一并写明的限定）

1. 结论绑定**当前引擎代际＋jsdelivr**：CDN 的 CORS 头策略、浏览器代际（老 Chromium/Firefox/Safari 行为可能不同）任一变化即可翻转——三档措辞建议写「Chromium 系实测可跑（2026-10-06，Edge headless）」，不建议写无条件「能跑」。
2. 本取证是**等价复现页**（同 URL 链直调 loadPyodide/initSqlJs），非 UI 点击全链路；demo 自身 runner 包装层若另有 file:// 敏感逻辑未覆盖（runners.js 通读未见，仅 loadScript+loadPyodide/initSqlJs 两链）。
3. headless 环境差异：无用户配置/扩展；真实浏览器上 Tracking Prevention/广告拦截扩展可能拦 CDN（控制台已见 storage 级 INFO，属用户环境变量）。

## §四 三处「未验证」措辞的实证底稿（改不改交主班）

| 档 | 现措辞 | 实证后可写的最小订正 |
|---|---|---|
| README_部署指南.md:39 | 「浏览器会拦截 WASM 运行环境，Python/SQL 跑不起来」 | 「经实测（Edge/Chromium，2026-10-06）file:// 下 Pyodide/sql.js 可从 CDN 加载运行；但本地服务器仍是推荐路径（引擎差异/扩展拦截不受控）」 |
| OPERATIONS.md／INVENTORY.md | 「file:// 直开：未验证」 | 「已验证（2026-10-06 headless Edge）：结构/JS/WASM 三层均可加载执行；多引擎兼容未测」 |

## §五 产物

- dom_dump.html／console_stderr.log／wasm_dump.html／wasm2_dump.html／wasm2_console.log／probe-file.html／probe-file2.html 均在宿主 `tmp/shift-20261006/l1004-17..18/` 留档。
- 仓内零文件改动（README/OPERATIONS/INVENTORY 未动；demo 域 porcelain 前后同）。
