# 判题沙箱网络/身份/PATH 三面材料（l1004-21；28d8 F-2/F-5/F-6）

> 产线：执行班 l1004-21（2026-10-06）。**材料型，落码属安全边界变更另派**；与 l927-11（F-1 文件系统零约束）拼成完整边界档——本档为网络/身份/PATH 三面，索引见 §四。

## §一 现值（白名单与 PATH 清单贴出）

- `_ENV_ALLOWLIST`（`core/runners/python_runner.py:39-43`）：`SYSTEMROOT / PATH / TEMP / TMP / USERPROFILE / APPDATA / LOCALAPPDATA / PYTHONIOENCODING / PROCESSOR_ARCHITECTURE`——九键。
- `_safe_env`（`:51-61`）：白名单取值＋`PYTHONIOENCODING=utf-8`＋**PATH 收窄**＝`[dirname(sys.executable)] + [System32, Windows 根]`（`:46-48`，nt only）；PROCESSOR_ARCHITECTURE 为崩溃规避保留（:38 注释，非敏感）。
- 复用面：cpp_runner/r_runner 自行构造 env（rg 命中两处，非 `_safe_env` 直调）——同族收口若做须三 runner 同批。
- F-2 网络面现值：无任何 socket/出站管控；代理变量（HTTP_PROXY 等）不在白名单＝被剥。

## §二 三面收口方案（各带单人桌面/公开部署两档处置）

### F-2 出站网络零管控

| 档 | 处置建议 |
|---|---|
| 单人桌面（local_only 默认） | **文档化接受**（28d8 给的次选）：沙箱护栏而非安全边界（README:64/home.py:55-57 信任口径），学生代码本机直连的风险＝学生自己承担，与「能 import requests」同阶。可在 docs 注记「出站未管控」防误判 |
| 公开部署（public） | 现设计 check_security 直接拒绝执行（base.py:31）⇒ 不适用；若未来放开受控执行则升**必需**：Windows 侧 WFP 出站白名单（按进程/Job Object 绑定，与 l1004-01 Job Object 同挂点）或最小deny；POSIX 侧 netns/proxy。属安全边界变更另派 |

### F-5 env 白名单泄漏用户名

| 档 | 处置建议 |
|---|---|
| 单人桌面 | **再收窄一档仍建议做**（低破坏性）：`USERPROFILE/APPDATA/LOCALAPPDATA` 三键可从白名单剔除——学生代码拿用户名的唯一通道；但注意连带：pip/缓存放铺设（本沙箱不装包，TEMP/TMP 够用）；破坏性面＝若题面/引导代码读 `%APPDATA%` 会 KeyError（census：题库 408 题无此依赖可先扫） |
| 公开部署 | 必做项之一；同白名单再收（SYSTEMROOT/PATH/TEMP 之外全剥）＋用户名面在 Job/受限 token 下天然隔离 |

### F-6 PATH 含解释器安装目录

| 档 | 处置建议 |
|---|---|
| 单人桌面 | **接受现状＋注记**：解释器目录（含 Scripts/、DLLs、python.exe 同级工具）可被按名调用——单人边界下与学生自己开终端同阶；收窄到「只有 python.exe 单文件目录」不可行（解释器运行需要同目录 DLL），**最小化方案＝虚拟环境专目录**（为判题建 venv，目录内只 python+pip+标准库，第三方入口脚本不落于此）——工程量中等，收益＝挡 `pip.exe`/`easy_install` 等旁路 |
| 公开部署 | 与上同案但升必需；venv 隔离＋`py -I`（python_runner 已 `-I`）＋Job Object 三件套 |

## §三 两档总表

| 面 | 单人桌面 | 公开部署（若放开执行） |
|---|---|---|
| F-2 出站 | 文档化接受 | WFP/Job 出站白名单（必需） |
| F-5 env | 剔 USERPROFILE/APPDATA/LOCALAPPDATA 三键（低破坏，建议做） | 同左（必需） |
| F-6 PATH | 接受＋注记；venv 专目录为可选加固 | venv 专目录（必需） |

## §四 边界档索引

- 本档（F-2/F-5/F-6）＋`docs/insights/l927-11-fs-constraint-adjudication.md`（F-1 文件系统）＋`docs/insights/l927-05-judge-security-review.md`（G 系巡检）＋`sandbox-resource-limits-design-20261006.md`（D-2/3/4 资源面，l1004-01）＝四份拼出沙箱边界全图；README「安全边界」专节（现缺，home.py:58 引用悬空）若补写，以上四份为素材源。
