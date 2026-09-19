# pywebview / streamlit-ace 疑点依赖只读核报（2026-09-19 晨间执行班，任务 l918-08，零改动）

> 证据命令（复跑应同数）：
> ```bash
> grep -rn "webview" --include="*.py" --include="*.toml" --include="*.bat" . | grep -v ".venv|tests/|insights|.git"   # → 9 处
> grep -rn "streamlit_ace|streamlit-ace" --include="*.py" --include="*.txt" . | grep -v ".venv|insights|.git"
> pip show pywebview   # → Name: pywebview  Version: 6.2.1（本机已装）
> ```

## 一、pywebview（requirements.txt:3 `pywebview>=4.4,<7`）

| 证据 | 内容 |
|---|---|
| 全仓消费者 | **零业务消费**：仅 `scripts/health_check.py:78-81`（可选探测——未装时打印「desktop mode only; web mode unaffected」非致命）＋`tests/test_launcher.py`（桩替 `sys.modules.setdefault("webview", SimpleNamespace())`）＋.streamlit/config.toml 注释 |
| 桌面入口 | grep `webview.create_window`/`webview.start` 全仓**零命中**——不存在真正用 pywebview 开窗的 launcher |
| freeze | `requirements-freeze.txt` **无 pywebview 行**（9/17「freeze 缺失」现仍成立）；本机 6.2.1 已装但 freeze 未锁 |
| 9/17 判定更新 | 「freeze 缺失＋零 import 双重存疑」→ **import 面复核后更弱化**：仅剩自陈「非必需」的探测引用；freeze 缺失即部署链未装它也通过（旁证非必需） |

**建议：偏删待拍板**。若确认无「桌面窗口模式」发布计划 → 从 requirements.txt 删除该行（health_check 探测保留，其未装分支本就无害）；若桌面模式在路线图 → 保留并补 freeze 行。任一方向都是一行改动，留日间执行。

## 二、streamlit-ace（requirements.txt:2 `streamlit-ace>=0.1.1,<1`）

| 证据 | 内容 |
|---|---|
| 真实消费 | `ui/components.py:17` 惰性 `from streamlit_ace import st_ace`（编辑器组件首次渲染时加载）；app.py:9 注释记载其 import 链 ~0.5s 的性能治理事实 |
| freeze | `requirements-freeze.txt:53 streamlit-ace==0.1.1` ✓ |

**建议：留**——在用、已锁 freeze、且惰性加载治理有据。

## 三、结论表（供日间拍板）

| 依赖 | 判定 | 动作 |
|---|---|---|
| pywebview | 偏删（零消费+freeze 缺失双证） | 删 requirements 行 或 补 freeze——按桌面模式是否在路线图二选一 |
| streamlit-ace | 留 | 无 |

## 四、零改动声明

仅 grep/pip show 只读取证＋本报告；未改 requirements/freeze；未 commit/push。
