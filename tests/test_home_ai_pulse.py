# -*- coding: utf-8 -*-
"""home _render_ai_pulse 30/90 天档位补测（l918-19）。

钉时间兜底三档（:184-199）与「已完成浅扫/深查」按钮的 set_meta 行为（:214-232）：
  ①quarterly ≥90 天 → st.warning「该做季度深查了」（l919-03 降档翻桩）；
  ②monthly ≥30 天（quarterly <90）→ st.warning「该做月度浅扫了」；
  ③两档未到 → st.success 倒计时文案；
  ④按钮：完成月度浅扫 → set_meta('ai_pulse_monthly')；完成季度深查 → set_meta 双键。
dao.get_meta_ts 用可控假值驱动 _days_since；error/warning/success/tabs/buttons 经
HomeFake 录制；只加测试不改页面代码。
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import ui.pages.home as home_page
from tests.test_ui_behavior import FakeStreamlit


class PulseFake(FakeStreamlit):
    EXTRA = {"caption", "metric", "download_button", "page_link", "text_input",
             "number_input", "selectbox", "multiselect", "checkbox", "slider",
             "text_area", "date_input", "toast", "balloons", "file_uploader",
             "image", "table", "bar_chart", "plotly_chart", "altair_chart"}

    def __getattr__(self, name):
        if name in self.EXTRA:
            def call(*a, **kw):
                self.calls.append((name, a, kw))
                return self
            return call
        return super().__getattr__(name)


def _dao(days_monthly_ts, days_quarterly_ts, buttons=None):
    dao = MagicMock()
    seq = {None if k is None else k: v for k, v in {} .items()}

    def get_meta_ts(key):
        return {
            "ai_pulse_monthly": days_monthly_ts,
            "ai_pulse_quarterly": days_quarterly_ts,
        }.get(key)
    dao.get_meta_ts.side_effect = get_meta_ts
    dao.get_meta.return_value = None
    return dao


def _ts(days_ago):
    """生成 days_ago 天前的 'YYYY-MM-DD HH:MM:SS'（UTC），供 _days_since 解析。"""
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")


def _patch_st(monkeypatch, fake):
    monkeypatch.setattr(home_page, "st", fake)
    # load_all_paths 在 _detect_pulse_event 里是函数内局部 import（from core.paths import …），
    # 必须 patch 源模块 core.paths；空路径让事件检测循环零迭代。
    import core.paths as cp
    monkeypatch.setattr(cp, "load_all_paths", lambda: [])
    return fake


def _texts(fake, kind):
    return [str(c[1][0]) for c in fake.calls if c[0] == kind]


def test_quarterly超90天_warning深查档(monkeypatch):
    fake = _patch_st(monkeypatch, PulseFake())
    home_page._render_ai_pulse(_dao(_ts(5), _ts(95)))
    warnings = _texts(fake, "warning")
    assert any("该做季度深查了" in w and "距上次 95 天" in w for w in warnings), warnings
    assert not any("该做季度深查了" in e for e in _texts(fake, "error")), "降档后不得再走 error"


def test_monthly超30天_warning浅扫档(monkeypatch):
    fake = _patch_st(monkeypatch, PulseFake())
    home_page._render_ai_pulse(_dao(_ts(35), _ts(60)))
    warnings = _texts(fake, "warning")
    assert any("该做月度浅扫了" in w and "距上次 35 天" in w for w in warnings), warnings


def test_正常档_success倒计时(monkeypatch):
    fake = _patch_st(monkeypatch, PulseFake())
    home_page._render_ai_pulse(_dao(_ts(10), _ts(40)))
    success = _texts(fake, "success")
    assert any("AI 进展已跟上" in s and "月度浅扫还有 20 天" in s and "季度深查还有 50 天" in s
               for s in success), success


def test_从未做过_9999兜底走warning(monkeypatch):
    """l919-03 翻桩：提醒类降档 error→warning，9999 兜底文案随之走 warning。"""
    fake = _patch_st(monkeypatch, PulseFake())
    home_page._render_ai_pulse(_dao(None, None))
    warnings = _texts(fake, "warning")
    assert any("从未做过" in w for w in warnings), warnings


def test_完成按钮写meta(monkeypatch):
    # 月度浅扫按钮 → set_meta('ai_pulse_monthly','done')
    fake = _patch_st(monkeypatch, PulseFake(buttons={"✓ 我已完成本月浅扫": True}))
    dao = _dao(_ts(5), _ts(5))
    home_page._render_ai_pulse(dao)
    called = [c for c in dao.set_meta.call_args_list if c.args[0] == "ai_pulse_monthly"]
    assert called, "完成月度浅扫应 set_meta ai_pulse_monthly"
    # 季度深查按钮 → 双键 set_meta
    fake2 = _patch_st(monkeypatch, PulseFake(buttons={"✓ 我已完成本季度深查": True}))
    dao2 = _dao(_ts(5), _ts(5))
    home_page._render_ai_pulse(dao2)
    keys = {c.args[0] for c in dao2.set_meta.call_args_list}
    assert {"ai_pulse_quarterly", "ai_pulse_monthly"} <= keys, "季度深查完成应双键置 done"
