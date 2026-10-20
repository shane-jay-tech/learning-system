# demo 站像素级重叠实测：P4/P8 判定＋3 行 CSS 预演（l1004-17，ab94 遗留1）

> 产线：执行班 l1004-17（2026-10-06）。**仓内零文件改动**（learning-system-demo porcelain 前后同）；实测走同源探针包装页（`D:/code/tmp/shift-20261006/l1004-17/probe.html`，宿主临时件）：iframe 同源直量 `getBoundingClientRect` 回写包装页 DOM 读出。截图通道在宿主 IAB 侧故障（见 §五），**rect 数字齐全、判定完整，截图缺位如实标**。

## §一 四档＋补测档 rect 读数（base 态，无注入）

| 视口 | sidebar | main | stats 溢出* | foot bottom vs 视口 | docScrollW vs innerW |
|---|---|---|---|---|---|
| 1440×900 | 248×900 | x=248 w=1100 | -481（nowrap 收余） | 878 ≤ 900 ✓ | 1425 ≤ 1440 ✓ |
| 768×1024 | 248×1024 | x=248 w=505 | 0 | 1002 ≤ 1024 ✓ | 753 ≤ 768 ✓ |
| 390×844 | 248×844 | x=248 w=310 | 0 | 822 ≤ 844 ✓ | **558 > 390（横溢 168px）** |
| 360×640 | 248×640 | x=248 w=310 | 0 | 618 ≤ 640 ✓ | **558 > 360（横溢 198px）** |
| 640×360 补测（P8 矮档） | 248×360 | x=248 w=377 | 0 | **565 > 360 ✗** | 625 > 640（微溢） |

\* stats 溢出＝子项 right 最大值 − 容器 right（负数＝有富余）。stats 三档全部 `flex-wrap: nowrap` 但 **子项互不越界**（CJK+空格可内部断行收缩：390 档三子项宽 51/41/14 竖排收缩）。

## §二 P4/P8 二值判定

- **P4（`.hero .stats` 无 flex-wrap）＝「视觉重叠」否／「溢出」真（但溢出主体不是 stats 互叠）**：四档 stats 子项全部收在容器内（overflow ≤0，无一项越过容器右缘）；真实溢出面是 **main 整列被固定 248px sidebar 挤出视口**——390/360 档 main right=558 vs 视口 390/360（横溢 168/198px），stats 右缘 484>390 需横向滚动才可见。ab94 的「三个 stat min-content 之和无换行出口」在引擎下被 CJK 断行化解，**未复现互叠**。
- **P8（矮视口 sidebar foot 顶出）＝真（条件触发）**：四指定档（高 ≥640）foot 全部在视口内；补测 640×360 横屏手机档实锤——`scrollH 565 vs clientH 360`、foot bottom=565（**顶出 205px**）、`footBelowViewport=true`＋`footOutsideSidebar=true`、sidebar `overflowY: visible` 无自有滚动 ⇒ foot **不可达**（100vh 固定高，页面滚动也带不出来）。
- 通用发现：sidebar 与 main 同层 flex，`overlapSidebarMainPx=0` 全档成立——**「视觉重叠」整域为否**，ab94 P 系全部是「溢出/不可达」而非叠盖。

## §三 verdict code 溢出实测（合成样本预演，px 换算口径订正）

- 真实面：四档静态首页 `.verdict` 均 0 个（需先判题才渲染）——用合成 `.verdict code`（61 字符无空格 token＝矿内 MAX unbreakable）在 360 档预演。
- **无 CSS**：`overflow-wrap: normal`，code 元素宽 **427px**，把 main 撑到右缘 787 vs 视口 360 ⇒ **内容横溢 427px**。
- **px 换算订正**：427px ÷ 61 字符 ÷ 14px = **0.50em/字符**（Chromium monospace 实际 advance）——ab94 用 0.55/0.6/0.65em 推算 471/512/556px 需求行宽，**实测系数取区间下界之下**，所需行宽 ≈427px（360 视口下无论怎么留白都放不下，必须断行）。
- **注入 `overflow-wrap:anywhere` 后**：code 宽 280px、收进 verdict 容器 313px、scroll 溢出 0——第三行 CSS 有效。

## §四 3 行 CSS 预演（640×360 注入前后对照）

```css
@media (max-width:980px){.sidebar{position:absolute;left:-248px}.main{padding:16px}}
.verdict code{overflow-wrap:anywhere}
```
注入后（640×360）：sidebar x=-248/right=0（移出屏）、main x=0 w=625（padding 16 生效）、**docScrollW 625 ≤ 640＝横溢治愈**、stats 收余 -54。注意：该最小改法是**无把手抽屉**——sidebar 连同 foot 移出屏后没有开启按钮，P8 的 foot 从「顶出不可达」变「隐藏不可达」，可达性要靠后续加抽屉开关（主班拍板时一并定）。

## §五 截图缺位说明（如实）

- 宿主 IAB 截图 API 故障：`browser screenshot activity capture failed for guest` → 重试 `surface preparation timed out after 3000ms`（显示窗格＋延时重试均无效）。六档截图未能落盘。
- 替代证据链：rect 数字（§一/§三/§四）全部来自真实排版引擎 getBoundingClientRect；探针包装页 `tmp/shift-20261006/l1004-17/probe.html`（URL 参数 `?v=WxH&inject=1/2/3`）留档可复跑，人工浏览器打开即见渲染并可自行截图。
- styles.css 零改动 ✓（探针在包装页向 iframe 注入 style，仓内文件零触碰）。

## 补截图节（l1007-10，2026-10-07）

l1004-17 缺位六档已由 CDP headless Edge 补齐（shot6.mjs 零依赖驱动，Page.captureScreenshot 通道——IAB 故障的替代通道与 l1004-28 同款）：shot-1440x900／768x1024／390x844／360x640／640x360／640x360-fix 六档 PNG 落 learning-system/tmp/（demo 仓 tmp 同份）。390/360 档 innerWidth 980＝桌面视口 fallback（meta viewport 未设时的真实渲染形态，与 l1004-17 rect 溢出结论互证）。640x360-fix 档=CSS 预演（iframe max-width 抑制）。


