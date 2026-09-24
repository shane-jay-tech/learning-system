# -*- coding: utf-8 -*-
"""`core/progress.format_local_ts` 钉桩（l924-23，2026-09-25）。

补的缺口（函数级终扫实测，台账见 `docs/insights/learn-core-final-scan-20260924.md`）：
`format_local_ts` 此前是 core/ 里**唯一「有生产消费点而 tests/ 零名引用」**的函数——
两个消费点都在 UI（`ui/pages/mistakes.py` 的上次提交 caption、`ui/pages/dashboard.py` 的最近活动行），
都是直接把串拼进文案，任何换算/截断口径错了**页面不会报错，只会静默显示错时刻**
（正是该函数 docstring 自己点名的「差 8 小时，昨晚的提交显示成今天下午」那一型反人类）。

⚠️ 时区不 flaky 的写法（完成标准 ①）：期望值一律由**显式 UTC datetime 对象**走
`.astimezone()` 得到，**不复用被测函数里的 `strptime`/`split('.')` 链路**——
两端同源会让「解析口径写错」这一整类缺陷测不出来（假绿）。
本机偏移恰为 0（UTC）时，UTC→本地换算类断言会退化成「与原文相等」，属平台事实而非本桩失能；
换算是否真发生由 `test_小数秒形与整秒形同值` ＋ `test_输出不含秒与时区尾巴` 两例兜住。

只读被测件，零写盘、零 DB、零网络。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_format_local_ts.py -q
跨时区不 flaky 自证：TZ=UTC / TZ=Pacific-Kiritimati / TZ=Etc-GMT-12 三态各跑一次（命令在 result 证据节）。
"""
from datetime import datetime, timedelta, timezone

import pytest

from core.progress import format_local_ts

LOCAL_OFFSET = datetime.now(timezone.utc).astimezone().utcoffset()
FMT = "%Y-%m-%d %H:%M"


def _expect(dt_utc: datetime) -> str:
    """与实现不同源的期望构造：显式 UTC 瞬时 → 平台本地 → 目标展示格式。"""
    return dt_utc.astimezone().strftime(FMT)


def test_空值与假值都渲染成空串():
    """库里 ts 列可能是 NULL 或空串（在册观察：事件表有空串行），展示位必须得到 ''。"""
    assert format_local_ts("") == ""
    assert format_local_ts(None) == ""
    assert format_local_ts("") != "None", "空值不得被 str() 兜成 'None' 显示给用户"


def test_解析失败逐字原样返回():
    """契约：转换不了就退回原文（宁显示 UTC 也别显示空白）。三种失败形态都钉。"""
    for raw in ("不是时间戳", "2026/09/20 09:30", "2026-13-45 99:99:99",
                "2026-09-20 09:30:00+08:00", "  2026-09-20 09:30:00"):
        assert format_local_ts(raw) == raw, f"解析失败应原样返回，实得 {format_local_ts(raw)!r}"


def test_小数秒形与整秒形同值():
    """带 `.123456` 的串必须先截到秒再解析（否则整条退回原文，用户看到带秒的 UTC）。"""
    whole = "2026-09-20 09:30:00"
    for frac in ("2026-09-20 09:30:00.1", "2026-09-20 09:30:00.123456",
                 "2026-09-20 09:30:00.999999"):
        assert format_local_ts(frac) == format_local_ts(whole), \
            f"{frac!r} 应与 {whole!r} 同值（小数秒被截断），实得 {format_local_ts(frac)!r}"


@pytest.mark.parametrize("dt_utc", [
    datetime(2026, 9, 20, 9, 30, tzinfo=timezone.utc),
    datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),          # 跨年/年初
    datetime(2026, 12, 31, 23, 30, tzinfo=timezone.utc),      # 跨日边界：换算后可能进次日
])
def test_utc到本地换算与平台口径一致(dt_utc):
    """主判据：展示值 == 「同一瞬时按本机时区格式化」。期望端不走被测实现（见文件头注）。"""
    raw = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
    assert format_local_ts(raw) == _expect(dt_utc)


def test_本机偏移非零时换算不是空操作():
    """判别力例（自适应，不在 UTC 机器上造假红）：只要本机时区不是 UTC，
    展示值就必须**不等于**库里那串 UTC 原文——这正是 docstring 承诺要修的事。"""
    raw = "2026-09-20 09:30:00"
    out = format_local_ts(raw)
    if LOCAL_OFFSET == timedelta(0):
        assert out == raw[:16], "本机即 UTC：偏移为 0 时展示值应等于原文的「到分钟」部分"
    else:
        # ⚠️ 与 raw[:16] 比而不是与 raw 比：输出格式本来就没有秒，跟带秒的原文比是**永真断言**。
        assert out != raw[:16], f"偏移 {LOCAL_OFFSET} 却给出与 UTC 原文同一分钟，说明换算没发生"


def test_输出格式不含秒也不含时区尾巴():
    """展示位是 f-string 直插，格式一变（多个秒、加 +08:00）就污染两处 UI 文案。"""
    out = format_local_ts("2026-09-20 09:30:00")
    assert len(out) == 16 and out[4] == "-" and out[13] == ":", f"应为 'YYYY-MM-DD HH:MM'，实得 {out!r}"
    for junk in ("Z", "+0", ":", "  "):
        if junk != ":":
            assert not out.endswith(junk), f"输出不该带 {junk!r} 尾巴"
    datetime.strptime(out, FMT)                              # 可再解析：口径自洽
