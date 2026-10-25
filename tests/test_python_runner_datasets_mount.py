# -*- coding: utf-8 -*-
"""l930-07：PythonRunner 只读挂载 content/datasets/ 进 tmpdir 的 runner 级钉桩
（l927-19 遗留最小可批形状 a）。

钉三件事：①学生代码里 `datasets/` 可见且可读（CSV 行数>0）；②挂载件整树只读
（写尝试必 OSError）；③学生代码看不到仓内其它路径（白名单式单点挂载的负面验证：
仓库根的 core/ 不可达）。全程走真 PythonRunner（子进程 -I 沙箱），零 mock。
"""
import os

from core.runners.python_runner import PythonRunner


def test_datasets_mounted_readable_and_readonly(tmp_path):
    code = (
        "import os, csv\n"
        "names = sorted(os.listdir('datasets'))\n"
        "with open(os.path.join('datasets', 'hr_employees.csv'), encoding='utf-8') as f:\n"
        "    rows = list(csv.DictReader(f))\n"
        "try:\n"
        "    open(os.path.join('datasets', 'hr_employees.csv'), 'a').close()\n"
        "    print('WRITABLE')\n"
        "except OSError:\n"
        "    print('READONLY')\n"
        "print('FILES', len(names))\n"
        "print('ROWS', len(rows))\n"
    )
    r = PythonRunner().run(code)
    assert "READONLY" in r.stdout, f"挂载件应为只读，实得：{r.stdout}"
    # l1025-012：题面数据基座族扩容（l1025-001..003 新增 research_data/survey_data/ml_dataset/sales_data 四 CSV）→ 8 件
    assert "FILES 8" in r.stdout, f"datasets 应挂 8 件（7 CSV+生成器），实得：{r.stdout}"
    assert "ROWS 500" in r.stdout, f"CSV 应可读且有数据，实得：{r.stdout}"


def test_mount_is_single_point_no_repo_root_visibility(tmp_path):
    """白名单式单点挂载的负面验证：仓内 core/ 目录不在沙箱可见面。"""
    code = (
        "import os\n"
        "print('HAS_CORE', os.path.isdir('core'))\n"
        "print('CWD', os.path.basename(os.getcwd()))\n"
    )
    r = PythonRunner().run(code)
    assert "HAS_CORE False" in r.stdout, f"仓内 core/ 不得可见（单点挂载），实得：{r.stdout}"
    assert "CWD ls_py_" in r.stdout, "工作目录应为临时沙箱"
