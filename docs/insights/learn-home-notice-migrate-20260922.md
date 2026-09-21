# home AI 档位 st.warning → render_notice 统一收口（l922-130 双形态并档）

任务：`l922-130-home-warning-migrate`（cwd `D:/code/learning-system`，执行班 `qoder-executor-20260922-0000-learn11`）。
本档按任务书要求「双形态并档」：**§一 先登记迁移前的裸形态**（迁移动作之前落笔），**§二 回填迁移后形态**，§三 记影响面与测试口径。

## 一、改前形态（迁移前登记）

取数：仓库根执行 `sed -n '181,200p' ui/pages/home.py`，HEAD `1831cc7`（工作树 clean），登记时刻 2026-09-22T04:39+08:00。

`ui/pages/home.py::_render_ai_pulse` 时间兜底三档里，**两个提醒档直接调裸 `st.warning`**：

```python
    if days_quarterly >= 90:
        # l919-03：notice 档位统一——提醒类降档 error→warning（与月度浅扫同形态）。
        st.warning(
            f"⏰ **该做季度深查了**（{_label(days_quarterly)}）"
            "——4 问自检 + 5 个信息源全过一遍，约 30 分钟"
        )
    elif days_monthly >= 30:
        st.warning(
            f"📅 **该做月度浅扫了**（{_label(days_monthly)}）"
            "——5 分钟看一眼，确认大版本没变"
        )
```

命中面复核（`grep -n 'st\.warning' ui/pages/home.py`）：全文 **2 处**，`:186`（季度深查档）、`:191`（月度浅扫档）——与任务书锚点 `ui/pages/home.py:186-193` 一致，**锚点未漂移**（锚点给的是跨两档的区间，实际两处调用分别在 186 与 191）。

同页另一条通知（`_render_home_body` 错题提醒 `:107`）**已在册走统一组件**：

```python
        render_notice(f"你还有 {len(mistakes)} 道错题等着复习。")
```

统一组件定义在 `ui/components.py:220`（`sed -n '220,227p'` 实取，锚点未漂移）：

```python
def render_notice(message: str):
    """统一通知条（d914-21，循 c-07 render_error_notice 范式）：st.warning 单形态收口。

    通知类（提醒/等待/复核类提示）用本函数；强调性决策提示（需用户当场取舍、
    带动态枚举清单）仍留页面内联，见各调用点注释。文案语义由调用方保留。
    """
    st.warning(message)
```

⇒ 改前同一页内**同档位两种写法并存**：错题通知经 `render_notice`，AI 档位两处裸 `st.warning`。这就是本单收口的对象。

## 二、改后形态（迁移后回填）

`ui/pages/home.py::_render_ai_pulse` 两档改为经统一组件出，**文案与档位判据逐字未动**，只多一段收口注释：

```python
    if days_quarterly >= 90:
        # l919-03：notice 档位统一——提醒类降档 error→warning（与月度浅扫同形态）。
        # l922-130：档位文案改由 components.render_notice 单点收口（同页错题通知 :107
        # 早已在册走它），页面不再自己直调告警档原语；文案与档位判据逐字未动，见
        # docs/insights/learn-home-notice-migrate-20260922.md。
        render_notice(
            f"⏰ **该做季度深查了**（{_label(days_quarterly)}）"
            "——4 问自检 + 5 个信息源全过一遍，约 30 分钟"
        )
    elif days_monthly >= 30:
        render_notice(
            f"📅 **该做月度浅扫了**（{_label(days_monthly)}）"
            "——5 分钟看一眼，确认大版本没变"
        )
```

改后复核（仓库根）：`rg -n 'st.warning' ui/pages/home.py` → **零命中，rc=1**（整文件归零，不只是该段）。
`render_notice` 无需新增 import——`home.py:13` 原本就从 `ui.components` 导入了它（给 :107 那条错题通知用）。

`else` 分支的 `st.success` 倒计时**未动**：它是「已跟上」的确认态、不是通知档，`components` 里也没有对应的统一 helper，收口它＝越界造组件。

## 三、影响面与测试口径

- **测试侧必须跟着改接线，否则假绿**：`tests/test_home_ai_pulse.py::_patch_st` 原来只换 `home_page.st`。迁移后 warning 落在 `ui.components` 模块名上，那个桩**一条都录不到**，而真实 `streamlit.warning()` 在脚本上下文外调用**不抛错**（只吐 missing ScriptRunContext 告警）⇒ 四条 warning 断言会**静默变红**、但「页面还在出通知」这件事在测试里彻底失明。已按 `tests/test_ui_behavior.py:388`（`d914-21` 同型做法）在 `_patch_st` 里补 `monkeypatch.setattr(components, "st", fake)`。**FakeStreamlit 基类未改**（多班共用，改它会让别的班假绿）。
- 新增 1 例 `test_ai_pulse档位走统一组件render_notice`：spy 拦 `home_page.render_notice` 证「确实经过统一组件」，同时转发组件真身证「仍落 warning 档、没顺手改档」，月度／季度两档一次验完。
- 其余触达 home 的既有用例不受影响：`test_ui_behavior.py::test_home_wrapper_security_notice_and_body` 早已同时 patch 两侧并把 `_render_ai_pulse` 打桩；`test_ergo_h912_13.py::test_home_days_since_exception_logged` 不 patch 任何 st、只查 caplog，且渲染链包在 try 里。
- 读数：`pytest tests/ -k home -q` 改前 **16 passed**、改后 **17 passed**（＋本班新增 1 例）。

## 四、本档只登记不实施

- `ui/pages/home.py` 的其余告警面（`_render_security_notice` 的 `st.error`:36／`st.info`:45、`_render_ai_pulse` 事件档 `st.info`:179、确认态 `st.success`:200）**任务书明令「不改其他页/其他形态」**，本单未动。
- 组件侧仍缺 `render_info`／`render_success` 同族 helper（只有 `render_notice`＝warning 档、`render_error_notice`＝error 档、`render_empty_state`＝info/caption 档）。补齐前其它页面的裸 `st.info/success` 无收口去处 ⇒ 属规划域，未自造。
- `tests/test_home_ai_pulse.py` 档头 docstring 自述录制桩叫 `HomeFake`，盘上实为 `PulseFake`（:19 定义）；`只加测试不改页面代码` 一句也不再成立（本单按任务书改了页面）。**历史自述，未回写**。
