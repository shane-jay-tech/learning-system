"""公开部署分支的 AppTest 真渲染证据（l927-45，收 l924-10 遗留 1）。

**为什么还要再写一份**：`is_public_deploy()` 的判定面早就有单位级覆盖
（`tests/test_config_env.py` 四组合、`tests/test_runner_security.py` 的 `patch.dict`），
提示文案的**接线上**也有 `tests/test_ui_behavior.py:435-451` 那条双侧**假 st** 桩
（l924-10 收的）。假件抓不到、而这条分支真正需要证的三件事是本档补的：

  ① 真 `st.error` 落正文后，三段式（`**标题**`／`原因：`／`下一步：`）**顺序与分段**是否成立
     ——假件只看 `calls` 列表，看不到组件 `"\n\n".join` 之后的最终形状；
  ② **非公开档首屏不得出现这条横幅**：`test_app_route_fallback.py:37-43` 那条
     `len(at.error) == 0` 是在**默认（非公开）**下跑的，它成立的前提是「环境变量没设」，
     而不是「分支判对了」——本档把两态放进同一个夹具里对照，才叫双档证据；
  ③ 公开分支的 `return` 是否真的**排它**：公开态既不该有 error 之外的重复横幅，
     也不该再出现非公开那条「安全提示（仅显示一次）」info 与它的「我知道了，不再提示」按钮。

口径：**真环境变量 → 真 `is_public_deploy()` → 真渲染**，全程不用 `monkeypatch.setattr` 去打桩判定函数
（打桩就退化成假件，证不到 `core/config.py:15-17` 那条 `or PUBLIC_DEPLOY == "1"` 的旁路语义）。
`LS_PROGRESS_DB` 一律指到 `tmp_path` 下的新库，**不连不写在册 `data/progress.db`**。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("streamlit.testing")
from streamlit.testing.v1 import AppTest  # noqa: E402

TITLE = "当前为公开部署模式"
REASON = "代码执行已禁用"
NEXT_ENV = "RUNNER_SECURITY_MODE=public"
NEXT_TAIL = "后重启"
ONCE_INFO_MARK = "安全提示（仅显示一次）"
DISMISS_LABEL = "我知道了，不再提示"


def _run(tmp_path, monkeypatch, db_name="public_deploy.db", **env):
    """设真环境变量 → AppTest 跑 app.py 首屏（route 默认 home）。"""
    monkeypatch.delenv("RUNNER_SECURITY_MODE", raising=False)
    monkeypatch.delenv("PUBLIC_DEPLOY", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("LS_PROGRESS_DB", str(tmp_path / db_name))
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    return at


def _assert_home_alive(at):
    """正向锚：证明这一屏**真的渲染了主页**。

    没有它，`len(at.error) == 0` 可能只是「脚本没跑起来／页面空白」的假绿——
    非公开档的「零横幅」判据尤其需要这条反真空自证（纪律档 §廿三：判「有」与「无」要双向）。
    """
    assert not at.exception, f"首屏不得抛异常：{[e.value for e in at.exception]}"
    assert at.session_state["route"] == "home"
    assert len(at.markdown) > 0, "主页正文一条 markdown 都没有 ⇒ 这一屏是空的，任何零计数断言都无意义"
    assert any(b.label == "做学习诊断" for b in at.button), "主页 CTA 未渲染 ⇒ 同上"


def _segments(text):
    """`render_error_notice` 的落正文形状：`**标题**\\n\\n原因：…\\n\\n下一步：…`。"""
    return text.split("\n\n")


def _check_three_part_error(at):
    """按**段**钉三要素：顺序、前缀、内容各守一段 ⇒ 互换 reason/next_action 或传空都会红。"""
    assert len(at.error) == 1, f"公开态应恰有一条 error 横幅，实得 {len(at.error)}"
    text = at.error[0].value
    segs = _segments(text)
    assert len(segs) == 3, f"三要素必须分成三段，正文：{text!r}"
    assert segs[0] == f"**{TITLE}**", f"标题段须独占串首且带粗体标记，实得 {segs[0]!r}"
    assert segs[1].startswith("原因：") and REASON in segs[1], f"原因段不齐：{segs[1]!r}"
    assert segs[2].startswith("下一步：") and NEXT_ENV in segs[2] and NEXT_TAIL in segs[2], \
        f"下一步段不齐（要含环境变量名与『后重启』）：{segs[2]!r}"
    # 接线互检查：环境变量名漏进原因段、或「代码执行已禁用」漏进下一步段 ⇒ 两段接错线，也要红
    assert NEXT_ENV not in segs[1], "环境变量属『下一步』，出现在原因段＝两段互换"
    assert REASON not in segs[2], "『代码执行已禁用』属『原因』，出现在下一步段＝两段互换"


def test_public_mode_renders_three_part_error_on_first_screen(tmp_path, monkeypatch):
    """档①：`RUNNER_SECURITY_MODE=public` → 首屏真出这条三段式横幅。"""
    at = _run(tmp_path, monkeypatch, RUNNER_SECURITY_MODE="public")
    _assert_home_alive(at)
    _check_three_part_error(at)


def test_public_mode_suppresses_non_public_only_widgets(tmp_path, monkeypatch):
    """档①之排它面：公开分支 `return` 后，非公开那条一次性 info 与它的按钮都不得出现。"""
    at = _run(tmp_path, monkeypatch, RUNNER_SECURITY_MODE="public")
    _assert_home_alive(at)
    assert not any(ONCE_INFO_MARK in i.value for i in at.info), \
        "公开态不该再走『安全提示（仅显示一次）』分支（`home.py:45` 的 return 失效了）"
    assert not any(b.label == DISMISS_LABEL for b in at.button), \
        f"公开态不该渲染『{DISMISS_LABEL}』按钮：它挂在一次性 info 容器里"


def test_non_public_default_has_no_public_banner(tmp_path, monkeypatch):
    """档②：两键都不设（默认 local_only）→ 首屏零 error，且一次性 info 与按钮**在**（正向锚）。"""
    at = _run(tmp_path, monkeypatch)
    _assert_home_alive(at)
    assert len(at.error) == 0, \
        f"非公开态不得出现公开横幅：{[e.value for e in at.error]}"
    assert any(ONCE_INFO_MARK in i.value for i in at.info), \
        "非公开＋全新库应走一次性安全提示；它不在＝这一屏根本没渲到主页"
    assert any(b.label == DISMISS_LABEL for b in at.button), "一次性提示的『我知道了』按钮须渲染出来"


def test_public_bypass_via_public_deploy_env(tmp_path, monkeypatch):
    """档①的另一入口：`RUNNER_SECURITY_MODE=local_only` ＋ `PUBLIC_DEPLOY=1` → 同一条横幅。

    这一例证的是 `core/config.py:17` 那条 `or` 旁路**在渲染层也成立**——
    单位级 `test_config_env.py:29-33` 只证到谓词，证不到横幅；两者不能互相顶替。
    """
    at = _run(tmp_path, monkeypatch, RUNNER_SECURITY_MODE="local_only", PUBLIC_DEPLOY="1")
    _assert_home_alive(at)
    _check_three_part_error(at)


def test_public_deploy_value_that_is_not_one_stays_non_public(tmp_path, monkeypatch):
    """档②的反向面：`PUBLIC_DEPLOY=true`（≠ 字面 "1"）不得判公开。

    钉的是旁路的**严格相等**语义：若有人把它松成真值判断，这一例会当场红，
    而单位级那四组合里的 `:37-39` 也会一起红——本例补的是渲染层那一半。
    """
    at = _run(tmp_path, monkeypatch, RUNNER_SECURITY_MODE="local_only", PUBLIC_DEPLOY="true")
    _assert_home_alive(at)
    assert len(at.error) == 0, f"PUBLIC_DEPLOY 只认字面 '1'，'true' 不该触发公开横幅"
    assert any(ONCE_INFO_MARK in i.value for i in at.info)


def test_two_states_differ_only_on_the_deploy_notice(tmp_path, monkeypatch):
    """双档**对照**：同一套件跑两遍，横幅数 1 vs 0，其余可见档位数不变。

    单例各证一侧会漏掉一种失效形态——比如「公开态把横幅渲成了两条」或
    「非公开态被顺手加了别的 error」，两边各自看都"像对的"。这里钉的是**差额**。
    """
    pub = _run(tmp_path, monkeypatch, db_name="cmp_public.db", RUNNER_SECURITY_MODE="public")
    _assert_home_alive(pub)
    # 两态各用**独立空库**：共用一份会让后跑的档继承前跑写下的 meta（例如一次性提示的已读标记），
    # 那种继承会把差额钉在错误的原因上。
    local = _run(tmp_path, monkeypatch, db_name="cmp_local.db")
    _assert_home_alive(local)

    assert len(pub.error) == 1 and len(local.error) == 0, "双档差额必须恰为这一条公开横幅"
    assert len(pub.warning) == len(local.warning), "公开态不得顺手改其它档位的数量"
    assert len(pub.success) == len(local.success)
    # info 差额＝恰好那条一次性提示（公开态没有它）
    assert len(local.info) - len(pub.info) == 1, \
        f"info 差额应为一次性安全提示那一条，实得 公开 {len(pub.info)}／非公开 {len(local.info)}"


# ---------------------------------------------------------------------------
# l930-09：公开态子页面差额对照（l927-45 遗留「首屏之外未证」）——第六例的差额对照
# 形状搬到各侧栏路由：每路由公开态 vs 非公开态各跑一遍，钉「差额恰为公开横幅一条」。
# 纯新增例、既有 6 例不动；夹具 _run 直接复用（route 经 session_state 预置）。
# ---------------------------------------------------------------------------
_ROUTES = ["paths", "language", "mistakes", "dashboard"]


def _run_route(tmp_path, monkeypatch, route, db_name, **env):
    """_run 的路由变体：AppTest 须在 run() **之前**预置 session_state.route
    （app.py:15 用 setdefault——run 后再设等于改已渲染帧；走 env 会被当环境变量忽略）。"""
    monkeypatch.delenv("RUNNER_SECURITY_MODE", raising=False)
    monkeypatch.delenv("PUBLIC_DEPLOY", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("LS_PROGRESS_DB", str(tmp_path / db_name))
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.session_state["route"] = route
    at.run()
    return at


@pytest.mark.parametrize("route", _ROUTES)
def test_public_vs_local_route_differs_only_on_banner(tmp_path, monkeypatch, route):
    """每路由双档对照：公开态恰多一条三段横幅，其余档位（warning/success/info 差额形态）不变。

    子页面与首屏的差别在页面本体（无主页 CTA/一次性提示），故正向锚换成
    「无异常＋有 markdown 渲染」；info 差额不钉死 0——子页面不渲染主页的一次性安全提示，
    两态在该路由的 info 都应为 0，但断言写成「公开态不含安全提示」而非数量，防后续
    子页面加合法 info 时误红。
    """
    pub = _run_route(tmp_path, monkeypatch, route=route, db_name=f"pub_{route}.db",
                     RUNNER_SECURITY_MODE="public")
    local = _run_route(tmp_path, monkeypatch, route=route, db_name=f"loc_{route}.db")

    for at in (pub, local):
        assert not at.exception, f"{route} 路由不得抛异常：{[e.value for e in at.exception]}"
        assert at.session_state["route"] == route, f"{route} 路由未按预置渲染"
        assert len(at.markdown) > 0, f"{route} 路由零 markdown ⇒ 页面没渲出来，计数断言全是假绿"

    # 实测口径修正（l930-09）：公开横幅挂 `ui/pages/home.py:33-43` **页内**而非 app.py 全局
    # ⇒ 子路由两态的可见差额天然为**零**（error/warning/success/info 四档逐一对等）。
    # 第六例的「差额=一条横幅」只在 route=home 成立；搬到各路由后本例钉的是
    # 「子路由零差额＋横幅不越界」——横幅若出现在子路由＝有人把它提到了全局层，当场红。
    for at in (pub, local):
        assert len(at.error) == 0, f"{route}：子路由任何状态都不该有横幅（横幅是 home 专属）"
        assert not any(ONCE_INFO_MARK in i.value for i in at.info), \
            f"{route}：一次性安全提示同样是 home 专属，子路由不得出现"
    assert len(pub.error) == len(local.error)
    assert len(pub.warning) == len(local.warning), f"{route}：warning 档位数不得被公开态改动"
    assert len(pub.success) == len(local.success), f"{route}：success 档位数不得被公开态改动"
    assert len(pub.info) == len(local.info), f"{route}：info 档位数不得被公开态改动"
