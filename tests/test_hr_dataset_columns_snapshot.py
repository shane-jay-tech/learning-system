# -*- coding: utf-8 -*-
"""HR 三件数据集的**列级**快照钉桩（l924-25，2026-09-25）。

补谁的缺口
----------
l923-27 的 `tests/test_hr_dataset_determinism.py` 已经钉了**逐字节 md5 ＋ 全表头字符串
＋ 总行数 ＋ 行尾形态**。md5 红只能说明「整件变了」，说不清**哪一列、哪一维**变了。
本桩补的是**列级三件套**，让将来任何一层红都能直接读出漂移坐标：

    第 1 层（列名序列）红 → 表头被单方面改（列名/列序变了，diff 直接指名）
    第 2 层（行数）    红 → 生成条数或表头行数变了（期望值从生成器签名推导，不是抄现盘）
    第 3 层（逐列空值）红 → 某一列的空值分布变了，红信息按列给出旧/新计数

与 l923-27 的分工：**本桩不碰 md5、不碰既有 determinism 测试件**（判据 ④）。
两桩是「整件指纹」与「列级坐标」的关系，任何一次未申报的数据集改动至少红一根。

取值口径（🔴 三层各自的"来源"不一样，别当成同一种快照）
--------------------------------------------------------
- **第 1 层的期望值不写死列名字面量**：由「把生成脚本复制到 tmp 目录实跑一次产出的表头」
  现取（生成器是唯一口径来源：`content/datasets/generate_hr_data.py` 的
  `csv.DictWriter(fieldnames=list(rows[0].keys()))`）。
  ⇒ 好处：仓内 csv 被手工改表头会**当场红**，而"生成器合法加了一列"不会假红在这一层。
  ⇒ 那"合法加列"谁报警？第 1 层的**列数 int 快照**（`N_COLS`）＋第 3 层的**键集 == 表头**
  ＋l923-27 的 md5 层，三处一起红。加列的正确动作见下一节。
- **第 2 层期望值 = 生成器函数签名的默认 `n`**（AST 读 `def gen_employees(n=500)` 等三处），
  所以 501/201/301 这三个数是**推导出来的**（`n + 1` 行含表头），不是抄盘上的字面量。
  ⇒ 改默认条数时本层会跟着签名走而**不假红**；但若只改了 csv 没改生成器，必红。
- **第 3 层是真正的数据快照**（唯一必须写成字面量的部分），取值命令见下方"重取快照"。

新增列 / 重生成时的行为（读这段再动手）
--------------------------------------
生成器加了列并有意重生成三件 csv ⇒ 本桩会红在：**列数 int**、**第 3 层键集**（新列没有快照键），
l923-27 红在 md5。正解顺序（不要靠放宽断言消红）：
  1. `python content/datasets/generate_hr_data.py` 之前先确认 12 道引用题面（`content/python/2?_hr_*`）
     的 `expected_output` 是否还成立——l923-27 的「数据集 ↔ 题面答案对平」用例管这条；
  2. 重生成后用下面的命令重取三件快照，回填 `N_COLS` 与 `NULLS`；
  3. 同步更新 l923-27 的 `PINNED/PINNED_HEADER/PINNED_LINES`（它不更新会红，本桩不替代它）。

重取快照（一行，只读）
----------------------
  PYTHONIOENCODING=utf-8 python -c "import csv,io,json;[print(n,json.dumps(sum(1 for r in csv.DictReader(io.open('content/datasets/'+n,encoding='utf-8',newline='')))for _ in [0]) or '',json.dumps({k:sum(1 for r in csv.DictReader(io.open('content/datasets/'+n,encoding='utf-8',newline='')) if r[k]=='') for k in next(csv.reader(io.open('content/datasets/'+n,encoding='utf-8',newline=''))))},ensure_ascii=False)) for n in ['hr_employees.csv','hr_recruitment.csv','hr_survey.csv']]"

只读边界：零生产码改动、零仓内 csv 改动（生成只写 tmp 副本目录）、零网络、零写库。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_hr_dataset_columns_snapshot.py -q
"""
import ast
import csv
import io
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
DATASET_DIR = REPO / "content" / "datasets"
GENERATOR = DATASET_DIR / "generate_hr_data.py"

# csv → 生成它的函数名（第 2 层期望值从该函数的默认 n 推导）
CSV_TO_FUNC = {
    "hr_employees.csv": "gen_employees",
    "hr_recruitment.csv": "gen_recruitment",
    "hr_survey.csv": "gen_survey",
}

# 列数快照（2026-09-25T02:2x @ HEAD e71816d 磁盘实取；键集/列名不写死，见头注「取值口径」）。
N_COLS = {"hr_employees.csv": 11, "hr_recruitment.csv": 8, "hr_survey.csv": 24}

# 第 3 层：逐列空值计数快照。空值口径 == 「csv 字段为空串」，
# 与 pandas.read_csv 的 NaN 口径在本三件上等价（本桩内有前置断言自证：无引号字段、无纯空白字段）。
# 2026-09-25 磁盘实取：三件里**只有 leave_date 有空值**（378/500 = 未离职者留空，
# 生成器 `leave_date = ... if left else ""`，`random() < 0.25` ⇒ 期望约 25% 非空）。
NULLS = {
    "hr_employees.csv": {
        "age": 0, "department": 0, "education": 0, "employee_id": 0, "gender": 0,
        "hire_date": 0, "leave_date": 378, "performance_score": 0, "salary": 0,
        "satisfaction_score": 0, "training_hours": 0,
    },
    "hr_recruitment.csv": {
        "apply_date": 0, "candidate_id": 0, "channel": 0, "cost_yuan": 0,
        "days_in_process": 0, "department": 0, "final_stage": 0, "result": 0,
    },
    "hr_survey.csv": {
        **{"employee_id": 0},
        **{f"uwes_{i}": 0 for i in range(1, 10)},
        **{f"pls_{i}": 0 for i in range(1, 8)},
        **{f"lmx_{i}": 0 for i in range(1, 8)},
    },
}

DATASETS = sorted(CSV_TO_FUNC)


# --------------------------------------------------------------------------
# 口径来源（全部现取，不抄盘上字面量）
# --------------------------------------------------------------------------

def _read_csv(path: Path):
    """返回 (表头列名序列, 数据行 dict 列表)。`newline=""` 是 csv 模块的硬性要求。"""
    with io.open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [dict(zip(header, r)) for r in reader]
    return header, rows


def _generator_default_n(func_name: str) -> int:
    """AST 读生成器里 `def gen_xxx(n=500)` 的默认值（不 import，避免模块级 random.seed 影响本进程）。"""
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            args, defaults = node.args.args, node.args.defaults
            if not defaults:
                raise AssertionError(f"{func_name} 没有默认参数，第 2 层口径需重估")
            name, value = args[-len(defaults)].arg, defaults[0]
            assert name == "n", f"{func_name} 的默认参数名不是 n（现为 {name}），口径需重估"
            assert isinstance(value, ast.Constant) and isinstance(value.value, int), f"{func_name}(n=…) 不是整型字面量"
            return value.value
    raise AssertionError(f"生成脚本里找不到 {func_name}，本桩的 csv↔函数映射已过期")


@pytest.fixture(scope="session")
def regen_dir(tmp_path_factory):
    """生成脚本的 tmp 副本实跑目录（`OUT_DIR` 跟着 `__file__` 走 ⇒ 只写副本目录）。"""
    work = tmp_path_factory.mktemp("hr-cols-regen")
    shutil.copyfile(GENERATOR, work / GENERATOR.name)
    proc = subprocess.run([sys.executable, str(work / GENERATOR.name)],
                          cwd=str(work), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    assert proc.returncode == 0, f"生成脚本副本执行失败 rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    assert sorted(p.name for p in work.glob("hr_*.csv")) == DATASETS, "副本产出的文件集合与本桩映射不符"
    return work


@pytest.fixture(scope="session")
def repo_snapshot():
    """三件仓内现件的 (表头, 数据行) —— 整个 session 只读一次。"""
    return {name: _read_csv(DATASET_DIR / name) for name in DATASETS}


# --------------------------------------------------------------------------
# 前置：锚点仍成立 ＋ 空值口径可与 pandas 对齐
# --------------------------------------------------------------------------

def test_锚点_三件csv与生成脚本都在位():
    assert GENERATOR.exists(), "生成脚本被移走，本桩的口径来源没了"
    for name in DATASETS:
        assert (DATASET_DIR / name).exists(), f"数据集 {name} 不在位"
    # 卷宗锚点：`def gen_employees(n=500):` 仍是三处默认条数（推导第 2 层期望值的依据）
    assert _generator_default_n("gen_employees") == 500


@pytest.mark.parametrize("name", DATASETS)
def test_空值口径_无引号字段且无纯空白字段(name, repo_snapshot):
    """第 3 层的"空串 == pandas NaN"等价前提：这两条一旦破了，快照口径要重述。"""
    raw = (DATASET_DIR / name).read_bytes()
    assert b'"' not in raw, f"{name} 出现引号字段 ⇒ csv 层空串与 NaN 的对应关系要重新核"
    header, rows = repo_snapshot[name]
    bad = [(i, c) for i, r in enumerate(rows) for c in header if r[c] != "" and r[c].strip() == ""]
    assert not bad, f"{name} 存在纯空白字段（行/列 {bad[:3]}）⇒ 空值口径需重述"


# --------------------------------------------------------------------------
# 三件 × 三层
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", DATASETS)
def test_层1_列名序列与生成器同源且列数与快照对平(name, repo_snapshot, regen_dir):
    """漂移坐标：哪一列被改名/换位/增删。期望值**不写死字面量**，取自生成器实跑产物。"""
    repo_header, _ = repo_snapshot[name]
    gen_header, _ = _read_csv(regen_dir / name)
    added = [c for c in gen_header if c not in repo_header]
    removed = [c for c in repo_header if c not in gen_header]
    assert not added and not removed, (
        f"{name} 表头与生成器产物不同源：新增 {added} 缺失 {removed}\n"
        f"  仓内 {repo_header}\n  生成器 {gen_header}"
    )
    assert repo_header == gen_header, (
        f"{name} 列名集合相同但**列序**变了（题面按列名取数，列序变只影响人工读表与 diff 可读性）：\n"
        f"  仓内 {repo_header}\n  生成器 {gen_header}"
    )
    assert len(repo_header) == N_COLS[name], (
        f"{name} 列数从 {N_COLS[name]} 变成 {len(repo_header)} ⇒ 合法加/删列后要按头注"
        f"「新增列时的行为」回填 N_COLS 与 NULLS（md5 层在 l923-27，会同时红）"
    )


@pytest.mark.parametrize("name", DATASETS)
def test_层2_行数等于生成器默认n加一(name, repo_snapshot):
    """漂移坐标：数据条数。期望值从 `def gen_xxx(n=…)` 签名推导，不写 501/201/301 死字面。"""
    n = _generator_default_n(CSV_TO_FUNC[name])
    _, rows = repo_snapshot[name]
    assert len(rows) == n, f"{name} 数据行数 {len(rows)} ≠ 生成器默认 n={n}（csv 被增删行或默认值被改）"
    # 含表头总行数按字节里的换行计数，与 `wc -l` 同口径（本三件纯 CRLF 且以 CRLF 收尾）
    with io.open(DATASET_DIR / name, "rb") as f:
        total_lines = f.read().count(b"\n")
    assert total_lines == n + 1, f"{name} 含表头行数 {total_lines} ≠ n+1={n + 1}"
    assert (DATASET_DIR / name).read_bytes().endswith(b"\r\n"), f"{name} 末尾无换行 ⇒ `wc -l` 会少报 1，口径需重述"


@pytest.mark.parametrize("name", DATASETS)
def test_层3_逐列空值计数快照(name, repo_snapshot):
    """漂移坐标：具体哪一列的空值分布变了（红信息按列给旧/新计数）。"""
    header, rows = repo_snapshot[name]
    assert set(header) == set(NULLS[name]), (
        f"{name} 快照键集与表头不符 ⇒ 有列没被快照覆盖（新增列？）："
        f"表头缺快照键 {sorted(set(header) - set(NULLS[name]))}／快照有而表头无 {sorted(set(NULLS[name]) - set(header))}"
    )
    actual = {c: sum(1 for r in rows if r[c] == "") for c in header}
    diff = {c: (NULLS[name][c], actual[c]) for c in header if actual[c] != NULLS[name][c]}
    assert not diff, (
        f"{name} 空值分布漂移（列: 快照→现值）：{diff}\n"
        f"⇒ 数据集被改过（或随机流变了），按头注顺序：先核 12 道引用题面答案，再重取快照"
    )


def test_跑完本桩仓内三件csv仍零改动(repo_snapshot):
    """副作用自证：本桩只读仓内件，生成只写 tmp 副本。"""
    for name in DATASETS:
        p = DATASET_DIR / name
        header, rows = _read_csv(p)
        assert header == repo_snapshot[name][0] and len(rows) == len(repo_snapshot[name][1])
    assert sorted(p.name for p in DATASET_DIR.glob("hr_*.csv")) == DATASETS, "数据集目录多出了本桩映射外的 csv"


if __name__ == "__main__":  # pragma: no cover - 便于手工重取快照
    for _name in DATASETS:
        _h, _r = _read_csv(DATASET_DIR / _name)
        print(_name, "cols=%d rows=%d" % (len(_h), len(_r)),
              {c: sum(1 for r in _r if r[c] == "") for c in _h})
