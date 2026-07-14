# Git 救命包

## 为什么这是你最该先学的

Agent 时代用工具开发个人项目，**最常发生的灾难**是：

> Agent 改了一通，原来能跑的现在不行了，记不清改了啥，改回去找不回。

Git 是你的"时光机"——任何时候 commit 一次就是一个还原点，agent 改坏了 `git checkout` 一秒回到能跑的状态。**这一条能力就值学费**。

## 4 个救命命令（学会就够初期用）

```bash
# 1. 初始化（每个项目只做一次）
git init

# 2. 把当前所有改动暂存 + 提交（最常用）
git add .
git commit -m "描述这次改了啥"

# 3. 看历史（找还原点）
git log --oneline

# 4. 退到某个还原点（不丢未提交的工作）
git checkout <commit-hash> -- .
# 或者完全回到那个状态
git reset --hard <commit-hash>
```

## 工作流：让 Agent 改代码前的 SOP

每次让 Agent 干活之前：

```bash
git status        # 看现在干净不干净
git add .
git commit -m "before agent edits feature X"
```

然后让 agent 改。改完测一下：
- **成功**：`git add . && git commit -m "feat: X"` 留下还原点
- **失败**：`git checkout .` 全部丢弃，回到 commit 那一刻

## 看变化：git diff

```bash
git diff             # 看未暂存的改动
git diff HEAD        # 看相对最近一次 commit 的全部改动
git log -p           # 看每次 commit 改了啥
```

**审 Agent 代码用这个**——agent 说"我只改了 X"，你 `git diff` 一看，发现它顺手改了 Y 和 Z。

## 分支：试错不破坏主线

```bash
git checkout -b feature-x        # 新建并切到分支
# 做实验...
git checkout main                 # 回到主线（实验在分支上不动）
git merge feature-x               # 觉得好就合并；不好就 git branch -D feature-x 删
```

99% 用法：**主线 main 永远是能跑的；试新功能开分支**。

## .gitignore：别什么都 commit

```
__pycache__/
*.pyc
.env.local
data/*.db
node_modules/
.DS_Store
```

新项目第一件事就是写 `.gitignore`——**永远不要 commit 密钥、缓存、大文件**。

## 提交消息怎么写

```
feat: 加入用户登录功能      ← 新功能
fix: 修复登录页面崩溃        ← bug 修复
docs: 更新 README           ← 文档
refactor: 拆分 main.py 模块   ← 重构
test: 加入单元测试           ← 测试
```

格式叫 **Conventional Commits**——一行写清楚"什么类型 + 干了啥"。

## 给 Agent 用 Git 的提示

让 agent 帮你 commit 时给清晰指令：

> "这次改完测试通过，请 git add 涉及的文件并 commit，commit message 写清楚改了啥"

Agent 比你更会写好的 commit message——但你要让它**用 commit 而不是把所有改动堆成一坨**。

## 常见坑

1. **不写 .gitignore 直接 add .**：commit 进 .env / 大文件 / 缓存
2. **commit 太久没做**：积累 200 个文件改动一次性 commit，回退颗粒度太粗
3. **不看 git diff 就 commit**：commit 进 agent 顺手乱改的代码
4. **`git push --force` 滥用**：覆盖远程历史；除非你确定没人在用，否则别用

## 现在做练习

5 道题：写出对应命令。这些题让你**用 Python 字符串 print 出 Git 命令**——熟悉命令的形状（实战靠回去自己跑）。
