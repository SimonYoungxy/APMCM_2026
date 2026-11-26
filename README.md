# APMCM 2026 Problem C — 非洲企鹅海上声学通信

本仓库是 2026 年亚太地区大学生数学建模竞赛 **C 题**的完整工作区：题目分析、数据核查、可复现流水线、论文源码与成品。

选题依据见 [docs/00-problem-analysis.md](docs/00-problem-analysis.md)：四题横向比较后选择 C 题，理由是数据完整、无外部依赖、方法链清晰且抽象材料最少。

## 目录结构

```
.
├── docs/                     题目分析与过程文档（不进入提交包）
│   ├── 00-problem-analysis.md    四题对比与选题理由
│   ├── 01-selection-advice.md    可直接复制的选题建议
│   ├── 02-data-audit.md          C 题数据核查报告
│   ├── instructions/             v1 / v2 / v3 三版写作指令原文
│   ├── changelog/                每一版的改动与原因
│   └── submission-readme.md      提交包内的 README（由同步脚本写入）
├── data/                     官方提供的原始数据（CSV / R / WAV）
├── code/                     分析脚本，按阶段编号
├── results/                  全部数值结果的唯一来源（JSON）
├── eda/                      数据核查报告
├── figures/                  11 张论文插图
├── tables/                   10 张论文表格，由 results 自动生成
├── paper.tex                 论文正文（官方 apmcmthesis，pdflatex）
├── ControlSheet.tex          控制页
├── apmcmthesis.cls / .cfg    官方模板文件
├── paper.pdf                 论文成品
└── scripts/sync-to-local.ps1 仓库 → 本地提交目录的同步脚本
```

## 复现

环境：Python 3.14，依赖见 `requirements.txt`（直接依赖）与 `env.txt`（`pip freeze` 全量）。

```powershell
python code/00_eda.py      # -> results/eda.json, eda/eda_report.md
python code/01_q1.py       # -> results/q1.json, fig01-fig03
python code/02_q2.py       # -> results/q2.json, fig04-fig06
python code/03_q3.py       # -> results/q3.json, fig07-fig09
python code/04_q4.py       # -> results/q4.json, fig10-fig11
python code/05_tables.py   # -> tables/tab01..tab10.tex
pdflatex paper.tex && pdflatex paper.tex
```

所有随机过程固定 `seed = 42`。在 pandas 2.3.3 与 3.0.3 下分别重跑，5 个 JSON 的哈希完全一致。

## 关键结论

- **Q1**：F02 非缺失当且仅当 CallType 为 tv，是类定义而非特征。只用 6 个完整特征时随机森林交叉验证准确率 0.481（基线 0.407）；3 个工程化比值特征升到 0.639；加回结构标记为 0.944，两者之差即泄漏规模。
- **Q2**：三指标等权保真度（PCA 首成分载荷 0.582/0.582/0.569，解释 96.7%）。AIC 选出 flat 用指数、mod/tv 用逻辑斯蒂衰减。潜在识别半径 87 / 156 / 192 m，并给出模型形式带 [67,95] / [138,206] / [162,438] m。
- **Q3**：自然叫声响应率 64.8% vs 对照 12.9%。全部回归满足 EPV ≥ 10。比例优势被拒（p = 0.027）后改用多项 logit。删失 Cox 给出刺激 HR 4.90（抬头）与 21.66（发声）。
- **Q4**：通信有效性指数半径 96 / 158 / 203 m；严格阈值 0.7 下坍缩至 30 / 54 / 71 m。

## 版本历史

| 版本 | 主要变化 | 文档 |
|---|---|---|
| v1 | 首版写作指令，暴露出泄漏、EPV、页数、模板残留四处致命问题 | [docs/changelog/v1.md](docs/changelog/v1.md) |
| v2 | 补齐上述四条，并加入分阶段落盘、种子、序数模型 | [docs/changelog/v2.md](docs/changelog/v2.md) |
| v3 | 按内容定位模板问题、阈值可达性规则、环境自检与收尾阶段、附件策略 | [docs/changelog/v3.md](docs/changelog/v3.md) |

## 同步到本地提交目录

仓库是唯一数据源，`APMCM2026_C` 是同步出来的成品目录，**不要直接改**：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync-to-local.ps1
```

## 说明

`data/` 下的原始数据版权归 2026 APMCM 组委会所有，仅用于本次竞赛与复现，不随本项目授权。
