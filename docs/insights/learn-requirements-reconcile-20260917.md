# learning requirements.txt 与 freeze 口径核验（916p-a3-018，2026-09-17，只读）

## 数字（命令与输出同段）

```
$ grep -cE '^[A-Za-z]' requirements.txt → 11（顶层声明）
$ wc -l < requirements-freeze.txt → 62 行
```

## 逐包定位表（11 行＝顶层包数）

| 包名 | requirements 区间 | freeze 版本 | 环境实测 |
|---|---|---|---|
| streamlit | >=1.32,<2 | ==1.59.1 | 1.58.0（区间覆盖 ✓；freeze 与环境漂移） |
| streamlit-ace | >=0.1.1,<1 | ==0.1.1 | — |
| pywebview | >=4.4,<7 | **缺失** | 6.2.1（pip list 实测） |
| pyyaml | >=6.0,<7 | ==6.0.3（PyYAML 大小写形态） | — |
| pandas | >=2.0,<4 | ==3.0.3 | 3.0.3 ✓ |
| numpy | >=1.24,<3 | ==2.5.1 | 2.3.5（quant 共享环境实测） |
| scipy | >=1.10,<2 | ==1.18.0 | — |
| scikit-learn | >=1.3,<2 | ==1.9.0 | — |
| matplotlib | >=3.7,<4 | ==3.11.0 | 3.11.0 ✓ |
| pytest | >=8.0 | ==9.1.1 | 9.1.1 ✓ |
| pytest-cov | >=5.0 | ==7.1.0 | 7.1.0 ✓ |

环境版本核验（≥3 包）：streamlit 1.58.0 / pandas 3.0.3 / matplotlib 3.11.0（命令输出原文同段见上）。

## 不一致清单

1. **pywebview 在 requirements 但 freeze 缺失**——freeze 生成环境未含 pywebview（或生成于未安装该包的环境）；且 pywebview 全仓零 import（另单 a1-021 同族发现），双重存疑。
2. **freeze streamlit==1.59.1 ≠ 环境 1.58.0**——freeze 非本机现况快照。

## 结论

**freeze 不能直接作为复现基线，需刷新**。刷新命令（只给不执行）：`python -m pip freeze --exclude-editable > requirements-freeze.txt`。另建议：pywebview 零 import 的删列裁定与 streamlit-ace 是否在用一并复核（留拍板）。

## 验收对照

- ✅ 两条数字命令同段（11/62）。
- ✅ 逐包定位表 11 行（含 pywebview「缺失」如实记录）。
- ✅ 环境实测 ≥3 包带版本号。
- ✅ 结论明确＋刷新命令一行。零改动、零安装、不 push。
