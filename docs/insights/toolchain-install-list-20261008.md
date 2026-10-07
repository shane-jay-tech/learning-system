# Rscript/MinGW 装机清单（2026-10-08，l1007-09 遗留——条件触发「不可用」分支）

> 零环境变更（未安装任何东西）。三重探测（where / PowerShell Get-Command / 常见安装位 C:\Program Files\R、C:\mingw64、C:\msys64）**Rscript 与 g++ 均不可用**——与 l1007-09（10-07）探测结论一致，装机未发生。

## 装机清单（winget 包名已核验在源，交主班执行）

| 工具链 | winget 命令（草案） | 装后验证 | 解锁 |
|---|---|---|---|
| R（Rscript） | `winget install RProject.R`（源内 4.6.1） | `Rscript --version`；Rscript 需装后重开 shell 让 PATH 生效（安装器默认注册） | r_runner 通道＋沙盒 R 行补测 |
| MinGW g++ | `winget install BrechtSanders.WinLibs.POSIX.UCRT.LLVM`（14.2.0-19.1.1）——自带 POSIX threads（runner 无 pthread 依赖风险） | `g++ --version`；cpp_runner 探测序含 `D:\tools\mingw64\bin\g++.exe`/`C:\msys64\mingw64\bin\g++.exe` 等路径（cpp_runner.py:28-40）——WinLibs 默认装 `%LOCALAPPDATA%\Programs\WinLibs\`，**不在探测序**，装后需设 PATH 或把实际 bin 路径加入探测序首 | cpp_runner 通道＋沙盒 cpp 行补测 |

**装机后补行流程**（l1007-09 沙盒 tmp 用毕即弃，补行时重建）：按 l1007-09 result §证据形态重建隔离 tmp 沙盒（题面自造不入题库）→ r-hello（Rscript 路径）＋cpp-hello（g++ 编译+运行两段墙钟）两行补入基线表（对照参数 512MB/5s/8 进程）。

## rg 复现

$ where Rscript / where g++ → 均无
$ powershell Get-Command Rscript, g++ → 空
$ winget search RProject.R → R for Windows 4.6.1（在源）
$ winget search WinLibs → BrechtSanders.WinLibs.POSIX.UCRT.LLVM（在源）
