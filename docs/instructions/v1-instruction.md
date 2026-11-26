# 任务：2026 APMCM 亚太地区大学生数学建模竞赛 · Problem C 完整论文与配套材料生成

## 一、你的角色

你是一名集三种能力于一身的专家，请用最高标准独立完成本任务：

1. **数学建模竞赛专家**：熟悉 APMCM / MCM 的评分标准与论文规范。
2. **应用统计与生态统计专家**：精通假设检验、非参数方法、广义线性模型(GLM)、生存分析、Bootstrap、分类器。
3. **LaTeX 排版专家**：能用官方模板产出可直接编译的成品。

你的产出必须是**可预提交（submission-ready）的完整参赛论文 + 全部配套材料**，不是提纲、不是思路、不是半成品。

## 二、输入材料（全部在本地，请逐一读取，不要凭记忆）

1. **题目 PDF**：`D:\Grade 2\数学建模\2026 APMCM Problems\2026 APMCM Problems\2026 APMCM Problem C\2026 APMCM Problem C.pdf`
2. **数据目录**：`D:\Grade 2\数学建模\2026 APMCM Problems\2026 APMCM Problems\2026 APMCM Problem C\date\`
3. **官方 LaTeX 模板目录**：`D:\Grade 2\数学建模\2026 APMCM Problems\2026 APMCM Problems\2026 APMCM 论文提交规范、论文模板、承诺书\APMCM LaTeX 模板\`（含 `main.tex`、`apmcmthesis.cls`、`apmcmthesis.cfg`）
4. **官方参考 R 代码**（数据目录内）：`Code1_AfricanPenguins_playbacks_analyses.R`、`Code2_AfricanPenguins_signal_degradation.R`

> 若上述绝对路径在你的运行环境中不存在，请在 `D:\Grade 2\数学建模\` 下用文件名（含 "Problem C"、"APMCM LaTeX 模板" 等关键字）递归查找后使用。**开始前先 `ls` 确认每个文件真实存在。**

## 三、数据清单（我已核对，请仍以你实际读取的列名/行数为准）

| 文件 | 规模 | 关键列 |
|---|---|---|
| `Data01_AfricanPenguins_seasurface_calls_acoustics.csv` | 108 行 | `Date, Location, CallType(flat/mod/tv), Duration, F01, F02, Fpeak, Q25, Q50, Q75, PulseRate` |
| `Data02_AfricanPenguins_playbacks_data.csv` | 278 行 | `Date, expID, Context, Type, CallType, PlaybackTrack, Distance, Npenguins, ResponseYesNo, HeadsUpYesNo, HeadsUpLatency, HeadsUpDuration, ApproachYesNo, ApproachLatency, ApproachDuration, ApproachRelDist, VocalYesNo, VocalLatency, VocalNcallsBefore, VocalNcalls, VocalRelNCalls, VR1..VR19` |
| `Data03`~`Data11` | 各 300×7 | 列 = `4m,8m,16m,32m,64m,128m,256m`；覆盖 3 种 call × 3 种指标(spectrogram / amplitude_spectrum / amplitude_envelope) 的"1m 处 vs 更远距离"相关系数 |
| `Supplementary5_*.wav` ×3 | 各约 1 秒 | **仅参考样本，不参与建模** |

## 四、全局硬性要求（违反任何一条即不合格）

1. **语言**：论文正文、摘要、图表标题、参考文献全部用**英文**；代码注释可用中文。
2. **模板**：必须用官方 `apmcmthesis.cls` 模板，用 **pdflatex** 编译，**跑两遍**，最终 **0 个 error、0 个 undefined reference**（我已验证该模板可用 pdflatex 编译成功）。
3. **禁止编造**：论文里每一个数字都必须能追溯到数据或可复现的计算，禁止凭空生成任何数值、表格、图表。
4. **检验规范**：每个统计检验必须同时给出——检验名称、检验统计量、p 值、效应量、置信区间（缺一项即为不规范）。
5. **图表**：8–15 张图，全部被正文引用，编号连续，分辨率 ≥300dpi，配英文 caption。
6. **可复现**：交付完整代码，任何人按 README 能一键复现论文中每个数字和图。

## 五、四问的严谨解法（至少达到以下深度，可更深入，禁止更浅）

### Q1 声学特征与三种 call 的分类

- **描述统计**：按 `CallType` 分组给出 Duration、F01、F02、Fpeak、Q25、Q50、Q75、PulseRate 的 mean/SD/median/IQR；出箱线图 + 小提琴图 + 散点图对比三类。
- **检验方法选择**：先做 Shapiro-Wilk 正态性检验，据此决定用参数还是非参数方法（在论文里写清判断过程）。
- **非参数检验（至少 2 种）**：Kruskal-Wallis 检验三类整体差异 + Dunn 事后两两比较；并用 Mann-Whitney U 检验做三组两两对比，报告多重比较校正（如 Bonferroni/FDR）。
- **分类器**：主模型用**随机森林**（输出特征重要性 = 主要影响因素），并至少搭 1 个基线（LDA 或 SVM 或 KNN）；用 5 折交叉验证，报告准确率、混淆矩阵、每类 F1；对特征重要性排序做生态学解释。
- **收尾**：结合传播与回放数据，讨论三种 call 在信息功能与传输鲁棒性上的差异，选出后续 Q2/Q3 要用的关键声学量并说明理由。

### Q2 声信号传播衰减与有效通信距离

- 用三种相关系数（spectrogram / amplitude-spectrum / envelope）构造一个**声学保真度测度**，明确写出合成公式（如加权平均或 PCA 第一主成分）并解释选择。
- 对三种 call 分别拟合"保真度随距离的单调衰减"模型（指数 / 逻辑斯蒂 / 幂律，用 **AIC 选模**），给出参数与置信区间。
- **分层阈值方案**：设计 potential recognition / recognition / reliable recognition 多档；重点报告"潜在识别最低相似度阈值"与"可靠识别严格阈值"两个判据。
- 反解各 call 的**有效通信距离**，用 **Bootstrap** 给出不确定区间；做敏感性分析；比较三种 call 远距离鲁棒性并明确排序（哪种更适合海上远距离传递信息）。

### Q3 海洋回放实验的行为响应建模

- 总体响应率 natural vs control：卡方 / Fisher 精确检验。
- 分 `Context / CallType / Distance / Npenguins` 分析响应差异：**logistic 回归（GLM，binomial 族）**。
- 三种行为（head raising / vocalizing / approaching）各自建模。
- 响应组合概率分布：**多项 logit 或对数线性模型**，比较 natural 与 control 是否改变组合分布。
- 响应潜伏期模型：**把"无响应"显式当作右删失（right-censored）**，用 Kaplan-Meier 曲线 + Cox 比例风险（或 AFT 加速失效时间）模型比较不同回放条件——这是拉开差距的关键点，务必做实。
- 出**预测数值表**：`Npenguins`=中位数，`Distance`=50/100/150 m，各 CallType 的响应潜伏期；某条件下无响应则记 "no response"。

### Q4 通信有效性评估与保护情景分析

- 整合 Q2 保真度估计、Q3 响应组合概率与企鹅情境，构造**海上声学通信有效性指数**，明确写出函数形式与每个权重的**生态学含义**。
- 用该指数估计典型群体规模下各 call 的通信半径，或单次回放刺激的期望响应个体数。
- **敏感性分析**：响应个体比例假设；噪声使识别阈值 0.5→0.6/0.7；全距离相关系数整体下降 5%–20%。
- 提出未来回放实验改进方案；从控制声学干扰角度给出觅食栖息地**具体保护建议**，并说明适用条件与局限。

## 六、交付物清单（按此目录组织）

```
产出/
├── paper.tex               # 英文正文，官方模板，pdflatex 可直接编译
├── main.pdf                # 编译好的成品（含摘要页、目录、正文、参考文献、附录）
├── figures/                # 所有图（PNG 或 PDF，≥300dpi）
├── code/                   # 完整可复现代码 + requirements.txt / 依赖说明
├── ControlSheet + Summary Sheet  # Problem Chosen=C，Team Number 留 apmcm263XXXXX 占位
└── README.md               # 如何复现每个数字、如何编译论文
```

## 七、论文结构要求（用官方模板骨架填写）

摘要页（Summary Sheet，≤1 页，含 problem/approach/key results/conclusions）→ 目录 → Introduction → Assumptions（逐条列出并简述合理性）→ Notation 符号表 → 逐问 Model 与 Solution（Q1–Q4）→ Model Evaluation（模型检验与误差）→ Strengths & Weaknesses → Conclusions → References → Appendix（代码）。

## 八、交付前自检（逐项打勾，全通过才算完成）

- [ ] pdflatex 编译 0 error、0 undefined reference（可接受少量 warning）
- [ ] 全文无编造数字，每个结果在 code/ 中可复现
- [ ] 每个检验三要素齐全（统计量 / p 值 / CI）
- [ ] 假设清晰、符号表完整
- [ ] 图 8–15 张，全部被正文引用，英文 caption
- [ ] 摘要 ≤1 页，涵盖问题-方法-关键结果-结论
- [ ] README 写清"如何一键复现"与"如何编译"
