# streamlit 四态视口按钮遮挡量测（l1004-28；b21a 遗留1，浏览器面）

> 产线：执行班 l1004-28（2026-10-06）。副本库（`tmp/shift-20261006/l1004-28/tmp-progress.db`，`LS_PROGRESS_DB` 注入）＋显式 `--server.address 127.0.0.1 --server.port 8645`；驱动＝headless Edge `--remote-debugging-port=9223`＋零依赖 CDP 脚本（`cdp_drive.mjs`，Node24 全局 WebSocket；Emulation.setDeviceMetricsOverride 切视口、Runtime.evaluate 量 rect、Page.captureScreenshot 截图）。styles.css 与生产码零改动 ✓。六张截图 `shot-*.png` 在宿主 l1004-28/。

## §一 四态＋基态＋缩放态 rect 读数（滚到提交区后量测；run 按钮 `[data-testid=stButton]>button`「▶ 提交运行」）

| 态 | 视口 | run 按钮 rect (x,y,w,h) | inViewport | 中心顶层元素（elementFromPoint） | fixed/sticky 元素 |
|---|---|---|---|---|---|
| base | 1280×800 | 698,563,207×46 | ✓ | 按钮本体（none） | **0 个** |
| a 竖 | 360×640 | 20,297,320×46（全宽） | ✓ | none | 0 |
| b 横 | 844×390 | 529,159,105×**73** | ✓ | none | 0 |
| b' 横 | 932×430 | 563,192,126×46 | ✓ | none | 0 |
| c 键盘近似 | 360×**300** | 20,127,320×46 | ✓（scrollIntoView 后） | none | 0 |
| d 200% 缩放（近似） | 1280×800 dpr=2 | 694,563,204×46 | ✓ | none | 0 |

**二值判定**：
- 「被任何 position:fixed/sticky 元素覆盖」＝**六态全否**——页面扫描 fixed/sticky 可见元素恒 0 个，按钮中心 elementFromPoint 六态全部命中按钮本体。
- 「落进可视区」＝滚到提交区后六态全 ✓；不滚动初载时按钮在折叠下（base y=563 边缘、其余更深），属正常滚动页非遮挡。
- b844 横屏窄列使按钮文本换行（105×73 双行）——面积反而增大，非遮挡但观感差，登记观感项。

## §二 近似口径如实声明

- **c 键盘态**：CDP 无真键盘折叠；用可视高 300px 视口近似。真实键盘是 visualViewport 收缩（本态 VV 读数 vvh=300 全幅），结论「键盘场景可滚动至可见、非遮挡死锁」为近似结论。
- **d 200% 缩放**：以 deviceScaleFactor=2 近似（CSS px 不变、像素倍增）；真浏览器 Ctrl+缩放会改 CSS 视口宽，未单独测。
- **编辑器 rect**：`.stCodeEditor` 选择器未命中（streamlit 代码组件 iframe 化），脚本回落抓到的 textarea 是页底「问 AI」输入框（y=3641-4699 各态），**不作为编辑器遮挡判据**——编辑器遮挡判定留待带真组件选择器的批次（登记）。

## §三 顺带三项（b21a 在册项读数，裁决留主班）

1. **smoke_boot 绑定坐实**：`scripts/smoke_boot.py:17-20` Popen 参数只有 `--server.port 8599 --server.headless true`，**不传 --server.address** ⇒ streamlit 缺省绑 `0.0.0.0`（全部网卡）——本班对照：显式传 address 后 netstat 实证 `127.0.0.1:8645 LISTENING`（仅回环）。smoke 服务的 8599 在本机 LAN 可达＝登记项坐实（是否补 address 属 smoke 脚本写位）。
2. wrap=False／.io-box 240px／.editor-wrap 挂空三条：`ui/styles.py` 现值 rg 命中 `.io-box`/`.editor-wrap`（`ui/styles.py` 代码区样式段）与 `ui/components.py` io-box 类名拼装——**具体 240px 值与挂空断言的逐字读数未展开**（预算内未做，读数留主班裁决批次）。

## §四 数据面披露（sha8 双点）

- **tmp 副本库前后不同值**：`cd2dbce4 → e6256877`，**写者已定位＝1 行 `learning_events` 埋点**（id=98，`lesson_viewed`，python/01_hello_and_vars，UTC 00:37:56＝会话内浏览课程页触发）——量测浏览行为本身触发课程埋点，非意外污染。
- **生产库零触碰实锤**：`data/progress.db` 收班 sha8=`cd2dbce4`＝开工时副本基准值（副本开工时即从生产复制）⇒ 生产前后同值 ✓。
- 端口/进程清理：streamlit pid 66680 与 headless Edge pid 80168 已按 PID taskkill，netstat 复核 8645/9223 仅余 TIME_WAIT ✓。
