# ui/pages 各页覆盖率缺口盘点（2026-09-19 晨间执行班，任务 l918-13，只读）

> 复跑命令：`python -m pytest tests -q --cov=ui.pages --cov-report=term`（395 passed/7 skipped，零 failed）。

## 一、逐页数字表（2026-09-19 实测，TOTAL 72%）

| 页 | 语句 | 覆盖率 | 主要未覆盖大段 |
|---|---|---|---|
| dashboard.py | 345 | **81%** | 167-205（复习健康度下半/成就/热力图渲染）、311-323/335-338（推荐漏斗细节）、402-409 |
| diagnostic.py | 61 | **70%** | 55-61/81-97（诊断路径分支） |
| home.py | 207 | **69%** | 267-317（最大连续段：主页下部板块）、189-197 |
| language.py | 340 | **55%（最低）** | 320-350/375-447/452-501/511-556（答题页交互主体：判分提交/代码编辑器联动/提示流） |
| mistakes.py | 115 | **73%** | 67-91（错题详情渲染段） |
| path.py | 148 | **93%（最高）** | 零散 6 行 |

## 二、补测优先级建议（只读材料）

| 优先级 | 页 | 理由 |
|---|---|---|
| P1 | language.py | 覆盖率最低（55%）＋语句最多（340）＋未覆盖段是**判分提交/编辑器联动**等核心交互——回归风险最大 |
| P2 | home.py | 69%＋最大连续未覆盖段 267-317（50 行整块） |
| P3 | mistakes.py | 73%＋67-91 单段 25 行（错题详情），fixture 模式可复用 dashboard 单的 FakeStreamlit |
| P4 | diagnostic.py | 70% 但仅 61 语句，绝对缺口小 |
| 维持 | path.py / dashboard.py | 93%/81%，收益递减 |

fixture 复用：tests/test_dashboard_page_render.py 的 DashboardFakeStreamlit＋_wire_page 模式可直接迁移到 language/home/mistakes（已知桩缺口：ace 编辑器组件与 navigate 相关录制需按页补 EXTRA）。

## 三、零改动声明

仅 pytest 覆盖率只读运行（.coverage 产物不入库，未 add）；git diff --stat 空；未 push。
