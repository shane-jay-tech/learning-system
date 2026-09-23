# -*- coding: utf-8 -*-
"""HR 三件数据集的再生成确定性钉桩（l923-27，2026-09-23）。

钉什么
------
`content/datasets/generate_hr_data.py` 在**模块级**定死 `random.seed(42)`（:8），
生成体全部包在 `if __name__ == "__main__":`（:107）里，`OUT_DIR` 取自
`__file__` 所在目录（:9）⇒ 把脚本复制到任意目录再执行，产物天然落在那个目录，
不碰仓内件。本桩正是利用这一点：复制脚本到 tmp_path 执行，逐字节（md5）对账
仓内 `hr_employees.csv` / `hr_recruitment.csv` / `hr_survey.csv` 三件现件。

为什么值得钉（爆炸半径实测）
----------------------------
`git grep -l "hr_employees\\|hr_recruitment\\|hr_survey" -- 'content/**/*.yaml'`
现读 **12 件**（20_hr_pandas 4 件 / 21_hr_viz 4 件 / 22_hr_model 4 件），题面里
`pd.read_csv("content/datasets/hr_*.csv")` 是运行时读取，`expected_output` 是
**手写死在这三件 csv 的具体抽样上**的。也就是说：谁改了生成参数、改了随机数的
消费顺序、或升级解释器后顺手重生成，这 12 道题的标准答案会 **silently 失效**
（判分器只比字符串，不会告诉你是数据集漂了）。本桩让这件事从「无声」变成「一次
可 diff 的有意行为」。

两层断言互补，不是一层
----------------------
1. **逐字节 md5 钉值**：改生成器（参数 / 随机消费顺序 / 解释器随机流）⇒ 红。
2. **数据集 ↔ 题面答案对平**（`test_hr数据集仍是01_dept_headcount的答案地基`）：
   改 csv 的人即使同步更新了钉死的 md5，只要没回头改题面 `expected_output`
   照样红。反过来重生成 + 同步改题面则两题都绿 —— 这是本桩希望的「有意行为」路径。

已知边界（转红时**不要放宽断言**）
---------------------------------
- `random` 的 Mersenne Twister 序列在 CPython 内跨小版本**不保证**逐位相同
  （`choice` 一类 API 的实现历史上改过）。本桩在 **Python 3.12.9 + pandas 3.0.3**
  亲验逐字节复现。若将来解释器升级把它弄红，正解是**重生成三件 csv 并逐题复核
  12 个 `expected_output`**，不是把 md5 改成"弱比较"。
- 第 4/5 名（Marketing 65 / HR 65）是并列的，但题面要的是**前 3**，前 3 与第 4 名
  之间计数严格递减，所以裁切不依赖并列排序实现；测试内还显式 assert 了这条
  （并列一旦吃掉第 3 名，本桩会主动失效报错，而不是给出假绿/假红）。

只读：零生产码改动、零仓内 csv 改动、零网络、零写库。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_hr_dataset_determinism.py -q
仓内现件 md5 复算（一行）：
  python -c "import hashlib;[print(p, hashlib.md5(open(p,'rb').read()).hexdigest()) for p in __import__('glob').glob('content/datasets/hr_*.csv')]"
"""
import csv
import hashlib
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parent.parent
DATASET_DIR = REPO / "content" / "datasets"
GENERATOR = DATASET_DIR / "generate_hr_data.py"

# 2026-09-23 磁盘实算快照：仓内现件逐字节 md5（键 = 文件名，值 = (md5, 字节数)）。
# 字节数一并钉住是第二维：md5 相同而 size 不同不可能，但 size 相同 md5 不同很常见，
# 红的时候先看这两列能立刻分清「整件重写」还是「局部值变了」。
PINNED = {
    "hr_employees.csv": ("579f97fb67c8a51abf9ce4a27a6e7f1a", 30507),
    "hr_recruitment.csv": ("a1e6d9882afebf2ed471411c3bfa3402", 13570),
    "hr_survey.csv": ("578c8547635f32a1d9d32fb50fc91265", 16660),
}

DATASET_STEMS = ("hr_employees", "hr_recruitment", "hr_survey")

# 列名快照：md5 只能告诉你「整件不一样」，列名漂移能立刻告诉你是哪一维变了。
# 口径 = 生成脚本里 DictWriter(fieldnames=rows[0].keys()) 的键序，题面按列名取数。
PINNED_HEADER = {
    "hr_employees.csv": "employee_id,department,hire_date,leave_date,salary,"
                        "performance_score,training_hours,satisfaction_score,age,gender,education",
    "hr_recruitment.csv": "candidate_id,channel,apply_date,final_stage,days_in_process,"
                          "result,cost_yuan,department",
    "hr_survey.csv": "employee_id," + ",".join(f"uwes_{i}" for i in range(1, 10)) + ","
                     + ",".join(f"pls_{i}" for i in range(1, 8)) + ","
                     + ",".join(f"lmx_{i}" for i in range(1, 8)),
}

# 行形态快照（表头 + 数据行）：501 / 201 / 301 行含表头
PINNED_LINES = {"hr_employees.csv": 501, "hr_recruitment.csv": 201, "hr_survey.csv": 301}

# 锚点：这三件是「题面运行时读数据集」的入口，钉住可防止 csv 被改名/搬走
HR_QUESTION_YAML = DATASET_DIR.parent / "python" / "20_hr_pandas" / "01_dept_headcount.yaml"


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _run_generator(work_dir: Path, mutate=None) -> dict:
    """把生成脚本复制到 work_dir 执行（OUT_DIR 跟着 __file__ 走），返回 {文件名: md5}。

    mutate: 可选 `(源码: str) -> str`，在副本上改源码后写回 —— 变异自证用。
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    copy = work_dir / GENERATOR.name
    shutil.copyfile(GENERATOR, copy)
    if mutate is not None:
        copy.write_text(mutate(GENERATOR.read_text(encoding="utf-8")), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(copy)],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, f"生成脚本执行失败 rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    return {p.name: _md5(p) for p in sorted(work_dir.glob("hr_*.csv"))}


# --------------------------------------------------------------------------
# 锚点复核（卷宗「背景与锚点」三条，全部改成可执行断言）
# --------------------------------------------------------------------------

def test_锚点_模块级定死seed42且OUT_DIR跟随file():
    src = GENERATOR.read_text(encoding="utf-8")
    lines = src.splitlines()
    assert lines[7].strip() == "random.seed(42)", lines[7]
    assert 'OUT_DIR = os.path.dirname(os.path.abspath(__file__))' in src
    assert 'if __name__ == "__main__":' in src
    # 三条生成语句必须在 __main__ 保护块内（否则 import 就会覆写仓内 csv）
    guard_idx = lines.index('if __name__ == "__main__":')
    for fn in ("gen_employees()", "gen_recruitment()", "gen_survey()"):
        call_idx = next(i for i, ln in enumerate(lines) if ln.strip() == fn)
        assert call_idx > guard_idx and lines[call_idx].startswith("    "), f"{fn} 跑到了保护块外"


def test_锚点_import生成器不落地任何csv(tmp_path):
    """保护块生效的直接证据：以 import 方式加载副本后，目录里不应出现 csv。"""
    copy = tmp_path / GENERATOR.name
    shutil.copyfile(GENERATOR, copy)
    sys.path.insert(0, str(tmp_path))
    try:
        import generate_hr_data  # noqa: F401  模块级 seed(42) 会执行，生成体不会
    finally:
        sys.path.pop(0)
        sys.modules.pop("generate_hr_data", None)
    assert list(tmp_path.glob("hr_*.csv")) == []
    assert sorted(p.name for p in DATASET_DIR.glob("hr_*.csv")) == sorted(PINNED)


def test_锚点_题面运行时读三件csv():
    """12 个引用题的入口字面量：题面里就是 pd.read_csv("content/datasets/hr_employees.csv")。"""
    text = HR_QUESTION_YAML.read_text(encoding="utf-8")
    assert 'df = pd.read_csv("content/datasets/hr_employees.csv")' in text
    refs = sorted(
        str(p.relative_to(REPO).as_posix())
        for p in REPO.glob("content/*/*/*.yaml")
        if any(n in p.read_text(encoding="utf-8") for n in DATASET_STEMS)
    )
    assert len(refs) == 12, (
        f"引用这三件数据集的题面从 12 件变成 {len(refs)} 件 ⇒ 爆炸半径要重估、"
        f"答案对平用例可能也要扩面：{refs}"
    )
    assert all(r.startswith("content/python/2") for r in refs)


# --------------------------------------------------------------------------
# 主桩：同 seed 再生成 == 仓内现件逐字节
# --------------------------------------------------------------------------

def test_同seed再生成逐字节等于仓内现件(tmp_path):
    produced = _run_generator(tmp_path / "regen")
    assert set(produced) == set(PINNED), f"生成的文件名集合变了：{sorted(produced)}"
    for name, (md5, size) in PINNED.items():
        assert produced[name] == md5, f"{name} 再生成结果偏离钉值 —— 生成参数或随机消费顺序被改"
        repo_md5, repo_size = _md5(DATASET_DIR / name), (DATASET_DIR / name).stat().st_size
        assert (repo_md5, repo_size) == (md5, size), f"仓内现件 {name} 已被改动，与钉值不符"
        assert (produced[name], (tmp_path / "regen" / name).stat().st_size) == (md5, size)


@pytest.fixture(scope="module")
def regen_once(tmp_path_factory):
    """整模块只跑一次生成脚本，供形态类用例复用（避免 3 次 subprocess）。"""
    work = tmp_path_factory.mktemp("hr-regen")
    produced = _run_generator(work)
    return work, produced


@pytest.mark.parametrize("name", sorted(PINNED))
def test_再生成产物的行尾与表头与仓内现件同形(name, regen_once):
    """纯 CRLF + 无裸 CR + 列名/行数快照 —— md5 之外的第二、第三维读数。"""
    work, _ = regen_once
    raw = (work / name).read_bytes()
    repo_raw = (DATASET_DIR / name).read_bytes()
    assert raw == repo_raw, f"{name} 逐字节不一致"
    assert raw.count(b"\r\n") == repo_raw.count(b"\n") == PINNED_LINES[name], f"{name} 行数漂移"
    assert b"\r" not in repo_raw.replace(b"\r\n", b""), f"{name} 存在裸 CR"
    assert repo_raw.endswith(b"\r\n")
    assert repo_raw.split(b"\r\n", 1)[0].decode("utf-8") == PINNED_HEADER[name], f"{name} 仓内列名/列序漂移"
    assert raw.split(b"\r\n", 1)[0].decode("utf-8") == PINNED_HEADER[name], f"{name} 再生成列名漂移"


# --------------------------------------------------------------------------
# 变异自证：钉桩有判别力，不是恒真
# --------------------------------------------------------------------------

def test_变异自证_seed改43三件全部转红(tmp_path):
    produced = _run_generator(tmp_path / "mut-seed", mutate=lambda s: s.replace("random.seed(42)", "random.seed(43)"))
    assert set(produced) == set(PINNED)
    for name, (md5, _) in PINNED.items():
        assert produced[name] != md5, f"改 seed 后 {name} 仍与钉值相同 ⇒ 本桩对随机流变更失明"


def test_变异自证_交换生成顺序同样转红(tmp_path):
    """随机消费顺序（而非参数）被改，也必须被同一根桩抓到。"""

    def mutate(src: str) -> str:
        swapped = src.replace(
            "    gen_employees()\n    gen_recruitment()\n    gen_survey()",
            "    gen_recruitment()\n    gen_employees()\n    gen_survey()",
        )
        assert swapped != src, "变异未生效：__main__ 三行调用格式已变，请同步本用例"
        return swapped

    produced = _run_generator(tmp_path / "mut-order", mutate=mutate)
    assert any(produced[n] != PINNED[n][0] for n in PINNED), "交换生成顺序后逐字节仍一致 ⇒ 随机流未被三件共享，结论需重估"


def test_变异自证_行数参数改动可被抓到(tmp_path):
    produced = _run_generator(tmp_path / "mut-n", mutate=lambda s: s.replace("def gen_employees(n=500)", "def gen_employees(n=501)"))
    assert produced["hr_employees.csv"] != PINNED["hr_employees.csv"][0]


# --------------------------------------------------------------------------
# 数据集 ↔ 题面答案对平（防「重生成后只改钉值不改题面」）
# --------------------------------------------------------------------------

def test_hr数据集仍是01_dept_headcount的答案地基():
    """不依赖 pandas 的排序实现，用纯 python 复算题面 expected_output。

    题面（`content/python/20_hr_pandas/01_dept_headcount.yaml`）要的是
    「按人数从多到少排序，输出前 3 个部门名称和人数」，其 `expected_output` 手写为
    `Finance 79 / Sales 70 / Legal 68`。这三档计数严格递减、且与第 4 名（65）之间
    无并列 ⇒ 复算口径唯一。若哪天并列吃掉第 3 名，本用例会先 assert 失效并报出
    原因，而不是给出随排序实现漂移的结果。
    """
    with (DATASET_DIR / "hr_employees.csv").open(encoding="utf-8", newline="") as f:
        counts = Counter(row["department"] for row in csv.DictReader(f))
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    assert len(ranked) == 8, f"部门数变化（现 {len(ranked)}），裁切口径要重估"
    assert ranked[2][1] > ranked[3][1], "第 3 与第 4 名并列 ⇒ 「前 3」的裁切依赖排序实现，本桩不适用"

    expected = yaml.safe_load(HR_QUESTION_YAML.read_text(encoding="utf-8"))["expected_output"]
    recomputed = "\n".join(f"{dept} {n}" for dept, n in ranked[:3])
    assert recomputed == expected.strip(), f"数据集与题面答案脱钩：复算={recomputed!r} 题面={expected!r}"


def test_全桩跑完仓内三件csv仍零改动():
    """本文件所有 subprocess 生成只写 tmp_path —— 收尾自证副作用为零。"""
    for name, (md5, size) in PINNED.items():
        p = DATASET_DIR / name
        assert (_md5(p), p.stat().st_size) == (md5, size), f"{name} 被本桩跑测改动了"


if __name__ == "__main__":  # pragma: no cover - 便于手工复算钉值
    for _name, (_md5_, _size) in PINNED.items():
        _p = DATASET_DIR / _name
        print(_name, _p.stat().st_size, _md5(_p), "pinned:", _md5_, _size)
