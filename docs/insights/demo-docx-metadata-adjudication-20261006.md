# demo docx 元数据隐私三案裁决材料（l1004-19；75ea 遗留1，隐私红线域）

> 产线：执行班 l1004-19（2026-10-06）。**隐私红线：本单零修改，落码权留人工**；差异注：k927-65 是 kaoyan docs 匿名化，本单是 demo docx 二进制内元数据。
> 取证纪律：值全部脱敏（只给键名＋值长度/形状），不复制身份串。

## §一 三处元数据现状（zip 列表级只读，值脱敏）

对象：`作业一：方案说明.docx`（学习系统 demo 目录内唯一 docx）。

| 件 | 键 | 值形状（脱敏） |
|---|---|---|
| `docProps/core.xml` | `dc:creator` | 11 字符 ASCII（账号标识形） |
| | `dc:description` | 24 字符（ASCII＋空格） |
| | `cp:lastModifiedBy` | **2 字符 CJK（姓名形）** |
| | `cp:revision` | 1 字符数字 |
| `docProps/app.xml` | Pages/Words/Characters/Lines/Paragraphs/**TotalTime**/CharactersWithSpaces/DocSecurity | 计数与使用时长（TotalTime 泄编辑耗时，低敏） |
| `docProps/custom.xml` | `KSOTemplateDocerSaveRecord`／`KSOProductBuildVer`／`ICV` | WPS 模板账号记录链三键（值形状不展开） |
| `docProps/thumbnail.wmf` | —（112,004 B 首页缩略图，可含内容渲染画面） | 二进制 |

**站点引用面复核（A 案前提）**：`rg "docx|作业一" index.html assets/app.js assets/data.js` → **0 命中**（C9 结论「站点不引用 docx」现值仍成立）；README_部署指南.md:31 现措辞「把本文件夹**所有文件**传上去」＝隐含把 docx 一并外发。

## §二 三案对照（步骤可复制）

| | 案 A 部署面排除（文档 1 行） | 案 B 清洗元数据（zip 内 3 处编辑） | 案 C 登记接受（台账 1 行） |
|---|---|---|---|
| 步骤 | README_部署指南.md:31 改「只传 `index.html`＋`assets/`（`tools/` 按需）」；:23 Netlify/Vercel 段同口径补一句「不要上传 docx」 | ① `python -c` 用 zipfile 重写：删 `docProps/custom.xml` 三键（或整件＋`_rels/.rels` 内 custom.xml 引用）、core.xml 的 creator/lastModifiedBy 置空串、删 `docProps/thumbnail.wmf`（或换白图）；② 正文 `word/` 一字不动；③ 重打包后 `python -c` 校验清单＋打开验证 | 主班台账记「作业一 docx＝已知外发面（含 creator/lastModifiedBy/thumbnail）」；部署照旧 |
| 生效面 | 只护「按文档部署」的路径；本地直接拖拽整个文件夹的人不设防 | **根治**：文件本身干净，任何部署/外发路径都安全 | 零防护，只是知情 |
| 风险 | 极低（1 行文档）；漏网＝手工全文件夹上传 | 中低：OOXML zip 重打包需保持 `[Content_Types].xml` 一致性；core.xml 置空串比删节点安全（schema 兼容）；**重打包前先 VACUUM 级备份原件**（副本留 private 区）；Word/WPS 打开验证一次 | 零技术风险；风险＝遗忘 |
| 断言/回归 | 无 | demo census 若有文件清单断言需同步（现无 docx 断言，零影响） | 无 |
| 建议 | **A 必做**（1 行，立即收窄主路径） | **B 建议同批做**（A 只挡文档跟随者，B 挡所有路径） | C 仅当申报必须交原 docx 时叠加 |

**材料倾向**：A＋B 组合（A 是文档口径、B 是物证清洁；两者正交）。B 落码权留人工（隐私红线），执行时按「tmp 副本演练→字节级校验→原件替换」三步。

## §三 边界

- 本单零修改（docx 未开写句柄；上面 B 案步骤仅为纸面预案）。
- 值脱敏纪律：本材料不含任何身份串/账号串；主班执行 B 案时自然接触原值，无需本档提供。
