# learning 7 个 skipped 测试核查与分类（l916-01，只读）

- 任务：l916-01-learning-skipped-audit（created 2026-09-16T00:05:51，软预算 ≤25 分钟）
- 执行：sweep-20260915-2300（GLM-5.3-Flash），2026-09-16 04:3x

## 一、实跑（先命令后数字）

```
python -m pytest tests -q -rs
→ 368 passed, 7 skipped in 34.67s
```

## 二、逐条分类（7 条＝分类表行数=skipped 数）

| 文件:行 | 原因原文 | 分类 |
|---|---|---|
| tests/test_cpp_runner.py:16 | g++ not available; skipping C++ runner tests | 依赖缺失（编译器） |
| tests/test_cpp_runner.py:27 | 同上 | 依赖缺失 |
| tests/test_cpp_runner.py:34 | 同上 | 依赖缺失 |
| tests/test_cpp_runner.py:44 | 同上 | 依赖缺失 |
| tests/test_r_runner.py:13 | Rscript not available; skipping R runner tests | 依赖缺失（R 运行时） |
| tests/test_r_runner.py:19 | 同上 | 依赖缺失 |
| tests/test_r_runner.py:25 | 同上 | 依赖缺失 |

## 三、可解除者

- 7 条均为**外部工具链依赖**（g++ / Rscript），非显式标记、非平台不符；
- 可解除前提＝本机安装 MinGW g++ 与 R + Rscript 并加入 PATH（装依赖属日间动作，本单不实施）；
- 解除后自动转绿（skip 判定按 shutil.which 探测），无需改测试。

## 四、声明

未改测试标记、未装依赖、不 push。

## 遗留问题

无。
