# 2026 APMCM Problem C 论文与材料生成指令 · v2

## 一、你的角色

你是集三种能力于一身的专家，独立完成本任务：

1. **数学建模竞赛专家**：熟悉 APMCM/MCM 评分与提交规范（页数、命名、页眉、摘要页）。
2. **应用统计与生态统计专家**：精通非参数检验、GLM、生存分析、Bootstrap、分类器，并懂得**模型可估性（EPV）与数据泄漏**的边界。
3. **LaTeX 排版专家**：能用官方模板产出可复现编译的成品。

产出是**可预提交（submission-ready）的完整论文 + 全部材料**，不是提纲。

## 二、输入材料（先逐一确认存在，再开始）

1. 题目：`D:\Grade 2\数学建模\2026 APMCM Problems\2026 APMCM Problems\2026 APMCM Problem C\2026 APMCM Problem C.pdf`
2. 数据目录：`D:\Grade 2\数学建模\2026 APMCM Problems\2026 APMCM Problems\2026 APMCM Problem C\date\`
3. 官方模板目录：`D:\Grade 2\数学建模\2026 APMCM Problems\2026 APMCM Problems\2026 APMCM 论文提交规范、论文模板、承诺书\APMCM LaTeX 模板\`
4. 提交规范 PDF：`...\论文提交规范、论文模板、承诺书\2026 APMCM Essay format and submission specifications.pdf`（**先读它，确认页数/命名/摘要页/承诺书要求**）

> 若路径不存在，在 `D:\Grade 2\数学建模\` 下按文件名递归查找。开始前必须 `ls` 确认每个文件真实存在。

## 三、数据清单与已核实的缺失结构（这是本任务的最高风险点，务必先读透）

### Data01（声学特征，108 行 × 11 列）
列：`Date, Location, CallType, Duration, F01, F02, Fpeak, Q25, Q50, Q75, PulseRate`；CallType 分布 **flat=44 / mod=40 / tv=24**。

**已核实的缺失模式（官方数据自带，不是缺陷）：**

| 特征 | flat | mod | tv | 含义 |
|---|---|---|---|---|
| F02（第二基频） | 44/44 全缺 | 40/40 全缺 | 0/24 全有 | **"有无第二基频"就是 two-voice 的定义** |
| PulseRate（脉冲率） | 44/44 全缺 | 缺6 | 缺4 | flat 是连续音，本无脉冲率概念 |
| 其余 6 个（Duration, F01, Fpeak, Q25, Q50, Q75） | 全有 | 全有 | 全有 | 唯一可公平比较的完整特征集 |

**强制要求：**
- 分类器**只允许用 6 个完整特征**（Duration, F01, Fpeak, Q25, Q50, Q75）做三分类基线，禁止把 F02/PulseRate 直接喂进模型——否则模型只是在学"缺失与否=标签"，是 100% 数据泄漏。
- 另设**两阶段判别**：① flat vs non-flat（PulseRate 是否可用）→ ② mod vs tv（F02 是否存在）。在论文里**明确说明这是定义性/物理性差异，不是统计发现**，并把"结构性缺失反映三类叫声物理属性"写成一段结论，反而成为亮点。

### Data02（回放实验，278 行 × 40 列）
列含 `Date, expID, Context, Type, CallType, PlaybackTrack, Distance, Npenguins, ResponseYesNo, HeadsUpYesNo, HeadsUpLatency, HeadsUpDuration, ApproachYesNo, ApproachLatency, ApproachDuration, ApproachRelDist, VocalYesNo, VocalLatency, VocalNcallsBefore, VocalNcalls, VocalRelNCalls, VR1..VR19`。

**已核实的样本量与事件数（决定模型能放多少协变量）：**

| 量 | 值 |
|---|---|
| 总行数 | 278 |
| Response 事件 | 108 |
| HeadsUp 事件 | 68 |
| Vocal 事件 | 81 |
| **Approach 事件** | **23（极少，务必降级建模）** |
| Distance 水平 | 13 个（5,10,20,30,40,50,60,70,80,100,120,150,200） |
| Context 水平 | 3（commuting/searching/after） |
| CallType 水平 | 4（flat/mod/tv/control） |
| Type 水平 | 2（call/control） |

### Data03–11（传播相关系数，各 300 行 × 7 列）
列 = `4m,8m,16m,32m,64m,128m,256m`；覆盖 3 种 call × 3 种指标(spectrogram / amplitude_spectrum / amplitude_envelope) 的"1m vs 远距离"相关系数。

### WAV ×3
约 1 秒样本，**仅参考，不建模**。

## 四、全局硬性要求

1. **语言**：正文/摘要/图表/参考文献全英文；代码注释可用中文。
2. **页数**：**正文（Summary Sheet 与目录之后）≤ 25 页**，附录不限；超出的内容一律移入附录。
3. **页眉**：只允许出现队号 + 页码，**严禁出现学校名、姓名**。
4. **编译**：官方 `apmcmthesis.cls`，`pdflatex` 跑两遍，最终 0 error、0 undefined reference。
5. **禁止编造**：每个数字可追溯到数据或 `results/*.json` 中可复现的计算，禁止凭空生成数值/表/图。
6. **检验规范**：每个检验给出检验名 + 统计量 + p 值；**效应量与置信区间在"该方法有公认实现时"给出，不适用时明确说明原因**（不得为凑数而编造）。
7. **可复现契约**：固定随机种子 `random_state=42`（以及 R 的 `set.seed(42)`），并在 README 写明 Python/R 与关键包的确切版本号。
8. **图**：8–15 张，全部被正文引用，编号连续，**PNG ≥300dpi 或矢量 PDF**，英文 caption。

## 五、模板预处理（开工第一步，顺序不可颠倒）

在**不带头、不含中文和空格的路径**下新建工作目录（如 `D:\Grade2_APMCM_C\`），并把 `apmcmthesis.cls` 与 `apmcmthesis.cfg` **复制**进该目录。然后对模板 `main.tex` 做以下清理（**每一条都做，否则编译必挂或违规**）：

1. 删除第 116–117 行那幅推广图（`\includegraphics{cat}` / `{gongzhonghao}` 及含 `\CJK` 的中文 `\caption`）——这两个图片文件不存在，直接报 `File not found`。
2. 删除参考文献里所有含 `\CJK{UTF8}{gbsn}{...}` 的中文条目（198–200 行）。
3. `\tihao{A}` 改为 `\tihao{C}`；`\baominghao{...}` 填队号（未定则留 `apmcm263XXXXX` 占位）。
4. 清空模板示例正文，保留骨架（abstract / toc / section 结构）。
5. 编译验证：`pdflatex` 连跑两遍，确认 0 error 后再开始写正文。

> 教训：本模板原版 figure 与参考文献带中文/缺图，直接编译会报错；务必先清理。用 `pdflatex` 而非 `xelatex`（原版参考文献用 `\CJK`，xelatex 会 undefined）。

## 六、四问解法（含降级规则，禁止比这更浅）

### Q1 声学特征与分类
- 描述统计：按 CallType 分组给 6 个完整特征的 mean/SD/median/IQR，箱线图+小提琴图。
- 方法选择：先 Shapiro-Wilk，**但写明 n=24–44 时正态性检验功效低的局限**；题目本就要求非参数。
- 非参数检验：**Kruskal-Wallis + Dunn 事后（FDR 校正）为主**；Mann-Whitney U 仅作为**敏感性复核**，不要当作第二套独立两两比较重复报告。
- 分类器：**基线只含 6 个完整特征**，随机森林（特征重要性）+ 一个基线(LDA/SVM/KNN)，5 折交叉验证（固定 seed），报准确率/混淆矩阵/每类 F1；再补**两阶段判别**（§三 的 flat vs non-flat → mod vs tv），并明确其"定义性"属性。
- 收尾：结合传播/回放数据讨论三种 call 的生态功能与传输鲁棒性差异，选出 Q2/Q3 关键声学量。

### Q2 传播衰减与有效通信距离
- 用三种相关系数构造**声学保真度**测度（加权平均或 PCA 第一主成分，写清公式与理由）。
- 三种 call 分别拟合"保真度随距离单调衰减"（指数/逻辑斯蒂/幂律，**AIC 选模**），给参数与 CI。
- 分层阈值：potential / recognition / reliable recognition；重点报告"潜在识别最低阈值"与"可靠识别严格阈值"。
- 反解通信半径，**Bootstrap 给不确定区间**；敏感性分析；比较三种 call 远距离鲁棒性并排序。

### Q3 回放行为响应（**严格按 EPV≥10 控制协变量数**）
- 总体响应率 natural vs control：卡方 / Fisher 精确检验。
- 分因素：logistic 回归（GLM binomial），**单因素先行，多因素时协变量数 ≤ 事件数/10**：
  - Approach（23 事件）→ **至多 2 个协变量**，或仅单因素 + KM/log-rank 分层；
  - HeadsUp（68）、Vocal（81）→ 最多 3–4 个协变量。
- **Distance 必须降维**：连续化，或分箱 ≤50 / 50–100 / >100（13 水平放 GLM 会爆参数）。
- 事件不足时降级：**Firth 惩罚 logistic** 或 **KM + log-rank 分层**，禁止硬拟合不收敛的多因素模型。
- 响应组合：**不用 8 类多项 logit（样本撑不住）**，改用**响应个数 0–3 的序数模型（proportional odds）**，比较 natural vs control。
- 响应潜伏期：把"无响应"当**右删失**，KM 曲线 + Cox（或 AFT），协变量同样受 EPV 约束。
- 数值表：Npenguins=中位数，Distance=50/100/150 m，各 CallType 响应潜伏期；无响应记 "no response"。

### Q4 通信有效性指数与保护情景
- 整合 Q2 保真度 + Q3 响应组合概率 + 情境，构造**通信有效性指数**，写清函数与每个权重的**生态学含义**。
- 估计典型群体规模下各 call 通信半径 / 期望响应个体数。
- 敏感性：响应个体比例假设；阈值 0.5→0.6/0.7；全距离相关系数降 5%–20%。
- 提出回放实验改进方案 + 觅食栖息地具体保护建议（含适用条件与局限）。

## 七、分阶段交付流程（必须逐阶段落盘，禁止一次性写全文）

**原因：四问完整建模 + 图表 + LaTeX 全文超出单次上下文容量，一次生成会中途丢上下文、后半段质量断崖。且只有落盘 `results/*.json`，才能真正确保"不编造"可核对。**

| 阶段 | 产出落盘 | 验收标准 |
|---|---|---|
| 0 | `eda/` 数据核查报告：缺失模式、样本量、因子水平编码、是否存在泄漏 | 确认 F02/PulseRate 泄漏被识别；确认可用特征集 |
| 1 | `results/q1.json` + Q1 图 | 三分类基线不含 F02/PulseRate；两阶段判别已建模 |
| 2 | `results/q2.json`（拟合参数 + Bootstrap CI） | 阈值可达性检查通过（所有 call 的半径可反解） |
| 3 | `results/q3.json`（含降级判定记录） | 记录每模型协变量数与事件数，EPV≥10 |
| 4 | `results/q4.json` + 敏感性表 | 指数函数与权重已定义 |
| 5 | 由 `results/*.json` **回填** LaTeX 正文 + 附录 | **论文每个数字与 json 逐一对齐，禁止出现 json 之外的数值** |

每一阶段结束先自检、再进入下一阶段；发现矛盾回到上一阶段修正，不得跳过。

## 八、交付物与命名规范

```
D:\Grade2_APMCM_C\
├── paper.tex                 # 英文正文（官方模板，pdflatex 可编译）
├── apmcmthesis.cls / .cfg    # 已复制进来，与 paper.tex 同目录
├── figures/                  # PNG ≥300dpi 或矢量 PDF
├── code/                     # 可复现代码 + requirements.txt（含版本）
├── results/                  # q1..q4.json + eda/
└── README.md                 # 复现步骤 + 编译步骤
```

**最终提交命名（区别于工作文件名）：**
- 论文：`C<报名号>.pdf`（不是 `main.pdf`，提交前重命名）。
- 承诺书 Control Sheet：**打印→签字→扫描**成 `C<报名号>cns.pdf`（不是 LaTeX 直接出的 PDF），按提交规范 PDF 的要求核对。

## 九、交付前自检（逐项打勾）

- [ ] 模板已清理（无 cat/gongzhonghao、无 \CJK 中文、\tihao=C）
- [ ] pdflatex 跑两遍，0 error、0 undefined reference
- [ ] 正文 ≤ 25 页，页眉仅队号+页码
- [ ] Q1 基线不含 F02/PulseRate，两阶段判别已写
- [ ] Q3 每模型记录事件数/协变量数，EPV≥10，无硬拟合不收敛模型
- [ ] 论文每个数字可在 results/*.json 或 code/ 中复现
- [ ] 每个检验三要素齐全；效应量/CI"能给则给，否则说明原因"
- [ ] random_state=42 + 版本号已写入 README
- [ ] 图 8–15 张全部被引用，英文 caption
- [ ] 摘要 ≤1 页，涵盖问题-方法-关键结果-结论
