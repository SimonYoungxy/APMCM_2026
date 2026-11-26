# 2026 APMCM Problem C 论文与材料生成指令 · v3

> v3 相对 v2 的改动：①模板清理改为按内容匹配定位（不再写死行号）；②工作目录改为工作区内 ASCII 子目录并修正原因；③Q1 取消"两阶段判别模型"，改为机理解释；④补 Q2 阈值不可达的报告规则；⑤新增阶段 −1 环境自检与阶段 6 最终收尾；⑥补序数模型 Brant 检验、Data03–11 缺失值说明、ControlSheet 交付说明；⑦新增〇节附件策略。

## 〇、附件策略（零号要求，优先于下文所有条目）

**本任务不依赖任何聊天附件。** 题目 PDF、数据文件、官方模板一律按下节给出的绝对路径，用本地文件工具直接读取。不要在请求里附带题目 PDF 或其它文档作为内嵌附件。

**若运行环境不能直接读取本地文件**：先向用户说明，并请其通过 Files API 上传后以 `file_id` 引用；**不得**把 PDF / Office 文档以 base64 内联或 `url` 直链的形式塞进消息。

- 允许的文档源：`source.type = "text"`（纯文本内嵌）、`source.type = "file"`（Files API 上传后引用 `file_id`，纯文本用 purpose `user_data`，PDF/Office 用 `text_recognition` 或 `rich_layout_recognition`）。
- 禁止的文档源：`base64`、`url` 等内联形式。违反会直接触发
  `API Error 400 messages.N.content.M.source: only 'file' and 'text' document sources are supported`。
- 遇到该错误时的处理：移除该附件块，改为在 prompt 中给出文件路径；或改用 Files API 上传后再引用。**不要靠重试同一条请求解决。**
- 若必须把 PDF 内容交给模型，且环境只支持纯文本：先用 `PyMuPDF` 抽取文本落盘，再以 text 形式提供。

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

> **模板状态不可假设**：官方 `main.tex` 可能已被他人修改过，任何"第 N 行"的描述都可能失效。开工第一步必须 `grep` 实地确认（见第五节），不得凭行号直接删除。

## 三、数据清单与已核实的缺失结构（本任务最高风险点，务必先读透）

### Data01（声学特征，108 行 × 11 列）

列：`Date, Location, CallType, Duration, F01, F02, Fpeak, Q25, Q50, Q75, PulseRate`；CallType 分布 **flat=44 / mod=40 / tv=24**。

**已核实的缺失模式（官方数据自带，不是缺陷）：**

| 特征 | flat | mod | tv | 含义 |
|---|---|---|---|---|
| F02（第二基频） | 44/44 全缺 | 40/40 全缺 | 0/24 缺（24 个全有） | **"有无第二基频"就是 two-voice 的定义** |
| PulseRate（脉冲率） | 44/44 全缺 | 缺 6 | 缺 4 | flat 是连续音，本无脉冲率概念 |
| 其余 6 个（Duration, F01, Fpeak, Q25, Q50, Q75） | 全有 | 全有 | 全有 | 唯一可公平比较的完整特征集 |

**强制要求：**

- 分类器**只允许用 6 个完整特征**（Duration, F01, Fpeak, Q25, Q50, Q75）做三分类基线，禁止把 F02 / PulseRate 直接喂进模型——否则模型只是在学"缺失与否 = 标签"，是 100% 数据泄漏。
- **不构建"两阶段判别模型"**。F02 非缺失 ⟺ tv、PulseRate 缺失 ⟺ flat，这是查表不是判别；若强行训练并报告"准确率 1.00"，属于凑数。
- 正确做法：在 Discussion / Model Evaluation 中，用发声机理（单声连续音 / 调制音 / 双声含两个基频）解释这一结构性缺失，明确 F02 与 PulseRate 是**类定义性变量、适用域不同**，因此从公平比较中剔除；并说明"缺失模式本身反映三类叫声的物理属性"。这段处理本身就是方法论贡献，必须写。

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
| Distance 水平 | 13 个（5, 10, 20, 30, 40, 50, 60, 70, 80, 100, 120, 150, 200） |
| Context 水平 | 3（commuting / searching / after） |
| CallType 水平 | 4（flat / mod / tv / control） |
| Type 水平 | 2（call / control） |

注意：`Distance × CallType` 存在大量空格（如 mod 在 5 / 10 / 70 / 120 / 200 m 为 0），因此**禁止把 Distance×CallType 交互项放进任何模型**。`VR1..VR19` 是响应呼叫类型，属于结果变量，**不得作为预测特征**。

### Data03–11（传播相关系数，各 300 行 × 7 列）

列 = `4m, 8m, 16m, 32m, 64m, 128m, 256m`；覆盖 3 种 call × 3 种指标（spectrogram / amplitude_spectrum / amplitude_envelope）的"1 m vs 远距离"相关系数。

**已核实**：9 个文件共 **1350 个 NaN**（单文件 70–240 个，占 3%–11%），且数量随 call 类型不同而不同（tv 最多）。Q2 拟合时必须显式处理（逐距离取可用样本，或按 call × 指标分别建模），**不得直接 `dropna()` 把整行删掉**，也不得静默忽略。

**量级参考**（用于判断阈值是否可达）：4 m 处 spectrogram / amplitude_spectrum 的中位数约 0.83–0.93，而 **amplitude_envelope 在 4 m 处中位数只有 0.63–0.68（最低 0.20）**。这意味着对 envelope 类指标而言，高于 ~0.7 的阈值在观测范围内无解。

### WAV ×3

约 1 秒样本，**仅参考，不建模**。

## 四、全局硬性要求

1. **语言**：正文 / 摘要 / 图表 / 参考文献全英文；代码注释可用中文。图中坐标轴、图例、标注一律英文。
2. **页数**：**正文（Summary Sheet 与目录之后）≤ 25 页**，附录不限；超出的内容一律移入附录。
3. **页眉**：只允许出现队号 + 页码，**严禁出现学校名、姓名**。
4. **编译**：官方 `apmcmthesis.cls`，`pdflatex` 跑两遍，最终 0 error、0 undefined reference。
5. **禁止编造**：每个数字可追溯到数据或 `results/*.json` 中可复现的计算，禁止凭空生成数值 / 表 / 图。
6. **检验规范**：每个检验给出检验名 + 统计量 + p 值；**效应量与置信区间在"该方法有公认实现时"给出，不适用时明确说明原因**（不得为凑数而编造）。
7. **可复现契约**：固定随机种子 `random_state=42`（R 用 `set.seed(42)`），并在 README 写明 Python / R 与关键包的确切版本号。
8. **图**：8–15 张，全部被正文引用，编号连续，**PNG ≥300 dpi 或矢量 PDF**，英文 caption。
9. **术语一致**：全文统一使用 `call type` / `playback` / `response latency` 等术语，不得中英混排或同义混用。

## 五、模板预处理（开工第一步，顺序不可颠倒）

**工作目录**：在**当前工作区内**新建 ASCII 命名的子目录，例如

```
D:\Grade 2\数学建模\APMCM2026_C\
```

目录名用 ASCII，父路径保持在工作区内（便于产物管理与权限）。**说明**：直接 `pdflatex main.tex` 在含中文与空格的路径下其实是可成功的；真正的风险来自带路径参数的工具链——`-output-directory`、synctex、bibtex、minted 在中文路径下可能报 `Emergency stop`。因此这里只是"稳妥做法"，不要理解成"中文路径一定编译不了"。

把 `apmcmthesis.cls` 与 `apmcmthesis.cfg` **复制**进该目录，然后清理模板。**清理必须按内容定位，不得按行号删除**：

```bash
# 1) 先探明当前状态
grep -n 'includegraphics' main.tex
grep -n 'CJK{UTF8}'        main.tex
grep -n '\\tihao'          main.tex
grep -n 'bibitem'          main.tex
```

然后逐项处理：

1. **删除推广图**：任何引用 `\includegraphics{cat}`、`\includegraphics{gongzhonghao}` 的 figure 环境（含其中带 `\CJK` 的中文 caption）。这两个图片文件在官方包里**根本不存在**，不删会持续报 `File not found`。
2. **删除中文参考文献条目**：所有含 `\CJK{UTF8}{gbsn}{...}` 的 `\bibitem`（通常 3 条），改为英文占位或直接删除。规范规定参考文献出现中文即违规。
3. **修复重复标签**：模板中 `\bibitem{bib:two}` 出现两次，会把后一条改为 `bib:three`，否则报 `Label multiply defined`。
4. **改选题**：`\tihao{A}` → `\tihao{C}`；`\baominghao{...}` 填队号（未定则留 `apmcm263XXXXX` 占位）。
5. **清空示例正文**，保留骨架（abstract / toc / section 结构），得到的文件另存为 `paper.tex`。
6. **编译验证**：`pdflatex` 连跑两遍，确认 0 error 后再开始写正文。
7. **可选**：若页眉报警 `\headheight is too small`，在导言区加 `\setlength{\headheight}{15pt}`。

> 教训：官方模板原版 figure 引用缺图、参考文献含中文；直接编译会报错。用 `pdflatex` 而非 `xelatex`（原版参考文献用 `\CJK`，xelatex 下该宏未定义）。

## 六、四问解法（含降级规则，禁止比这更浅）

### Q1 声学特征与分类

- **描述统计**：按 CallType 分组给 6 个完整特征的 mean / SD / median / IQR，出箱线图 + 小提琴图。
- **方法选择**：先做 Shapiro-Wilk，**但必须写明 n=24–44 时正态性检验功效低**、且题目本就要求非参数方法。
- **非参数检验**：**Kruskal-Wallis + Dunn 事后（FDR 校正）为主**；Mann-Whitney U 仅作**敏感性复核**，不得当作第二套独立的两两比较重复报告同一组对比。
- **分类器**：**基线只含 6 个完整特征**；主模型随机森林（输出特征重要性 = 主要影响因素），另加 1 个基线（LDA / SVM / KNN）；5 折交叉验证（固定 seed），报准确率 / 混淆矩阵 / 每类 F1；对特征重要性做生态学解释。
- **缺失结构处理**：按第三节要求，用**机理解释**而非判别模型处理 F02 / PulseRate 的结构性缺失，并明确其对"主要影响因素"结论的影响（剔除后影响因素应以 F01、Fpeak、Q50 等为主）。
- **收尾**：结合传播 / 回放数据讨论三种 call 的生态功能与传输鲁棒性差异，选出 Q2 / Q3 要用的关键声学量并说明理由。

### Q2 传播衰减与有效通信距离

- 用三种相关系数构造**声学保真度**测度（加权平均或 PCA 第一主成分，写清公式与理由）；处理 NaN 时按 call × 指标逐距离取可用样本。
- 三种 call 分别拟合"保真度随距离单调衰减"模型（指数 / 逻辑斯蒂 / 幂律，**AIC 选模**），给参数与 CI。
- 分层阈值：potential recognition / recognition / reliable recognition；重点报告"潜在识别最低阈值"与"可靠识别严格阈值"。
- 反解通信半径，**Bootstrap 给不确定区间**；敏感性分析；比较三种 call 远距离鲁棒性并给出明确排序。
- **阈值可达性规则（必须遵守）**：若某阈值高于该 call × 该指标在最近观测距离（4 m）处的保真度分位数，则反解**无解**，这属于数据事实而非模型缺陷。处理方式：
  - 报告为"≤ 4 m，低于观测下限"，不给出具体数值；
  - 用外推区间 + 敏感性说明该结论的不确定性；
  - **严禁为了"让半径可解"而人为抬高或压低阈值**。envelope 指标尤其容易触发（4 m 中位数仅 0.63–0.68）。

### Q3 回放行为响应（**严格按 EPV ≥ 10 控制协变量数**）

- 总体响应率 natural vs control：卡方 / Fisher 精确检验。
- 分因素：logistic 回归（GLM binomial），**单因素先行**；多因素时协变量数 ≤ 事件数 / 10：
  - Approach（23 事件）→ **至多 2 个协变量**，或仅单因素 + KM / log-rank 分层；
  - HeadsUp（68）、Vocal（81）→ 最多 3–4 个协变量。
- **Distance 必须降维**：连续化，或分箱 ≤50 / 50–100 / >100（13 个水平直接进 GLM 会参数爆炸）。禁用 Distance × CallType 交互项。
- 事件不足时降级：**Firth 惩罚 logistic** 或 **KM + log-rank 分层**；禁止硬拟合不收敛的多因素模型。
- 响应组合：**不用 8 类多项 logit（样本撑不住）**，改用**响应个数 0–3 的序数模型（proportional odds）**比较 natural 与 control；**必须报告 Brant 检验（或等价检验）结果**，若比例优势假设不成立则改用偏比例优势或多项模型并说明。
- 响应潜伏期：把"无响应"当**右删失**，KM 曲线 + Cox（或 AFT），协变量同样受 EPV 约束；报告 PH 假设检验（Schoenfeld 残差）结果。
- 数值表：Npenguins = 中位数，Distance = 50 / 100 / 150 m，各 CallType 的响应潜伏期；无响应记 `no response`。

### Q4 通信有效性指数与保护情景

- 整合 Q2 保真度 + Q3 响应组合概率 + 情境，构造**通信有效性指数**，写清函数形式与每个权重的**生态学含义**。
- 估计典型群体规模下各 call 的通信半径 / 期望响应个体数。
- 敏感性：响应个体比例假设；识别阈值 0.5 → 0.6 / 0.7；全距离相关系数整体降 5%–20%。
- 提出回放实验改进方案 + 觅食栖息地具体保护建议（含适用条件与局限）。

## 七、分阶段交付流程（必须逐阶段落盘，禁止一次性写全文）

**原因：四问完整建模 + 图表 + LaTeX 全文超出单次上下文容量，一次生成会中途丢上下文、后半段质量断崖。且只有落盘 `results/*.json`，才能真正确保"不编造"可核对。**

| 阶段 | 产出落盘 | 验收标准 |
|---|---|---|
| −1 | `env.txt`（`pip freeze`）+ 可用性自检 | 下列包全部可 import：`pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, lifelines, scikit-posthocs`（Dunn 检验）、`pingouin` 或等价效应量实现。缺则安装；`lifelines` 不可用时改用 `statsmodels.duration.hazard_regression.PHReg` 并在 README 记录 |
| 0 | `eda/` 数据核查报告：缺失模式、样本量、因子水平编码、是否存在泄漏 | 确认 F02 / PulseRate 泄漏被识别；确认可用特征集；确认 Data03–11 的 NaN 分布 |
| 1 | `results/q1.json` + Q1 图 | 三分类基线**不含** F02 / PulseRate；缺失结构已按机理写入结论 |
| 2 | `results/q2.json`（拟合参数 + Bootstrap CI） | 每个 call × 指标都给出**可达性判定**；不可达者按"≤4 m"规则报告 |
| 3 | `results/q3.json`（含降级判定记录） | 记录每模型的协变量数与事件数，EPV ≥ 10；Brant 检验、PH 假设检验结果齐全 |
| 4 | `results/q4.json` + 敏感性表 | 指数函数与权重已定义并给出生态学解释 |
| 5 | 由 `results/*.json` **回填** `paper.tex` 正文 + 附录 | **论文每个数字与 json 逐一对齐，禁止出现 json 之外的数值** |
| 6 | 最终成品 | `pdflatex` 连跑两遍 → 0 error → 核查正文 ≤ 25 页 → 核查页眉无身份信息 → 复制为 `C<报名号>.pdf` → 跑完第九节自检清单 |

每一阶段结束先自检、再进入下一阶段；发现矛盾回到上一阶段修正，不得跳过。

## 八、交付物与命名规范

```
D:\Grade 2\数学建模\APMCM2026_C\
├── paper.tex                 # 英文正文（官方模板清理后另存，pdflatex 可编译）
├── apmcmthesis.cls / .cfg    # 已复制进来，与 paper.tex 同目录
├── ControlSheet.tex          # 填好选题/队号/学校/队员/教练，单独编译
├── ControlSheet.pdf          # 供打印签字用
├── figures/                  # PNG ≥300dpi 或矢量 PDF
├── code/                     # 可复现代码 + requirements.txt（含版本）
├── results/                  # q1..q4.json + eda/
├── env.txt                   # pip freeze 输出
└── README.md                 # 复现步骤 + 编译步骤
```

**最终提交命名（区别于工作文件名）：**

- 论文：`C<报名号>.pdf`（不是 `main.pdf` 或 `paper.tex` 的产物名，提交前重命名）。
- 承诺书 Control Sheet：`ControlSheet.tex` 编译出的 PDF **打印 → 人工手写签字 → 扫描**成 `C<报名号>cns.pdf`（或拍照成 `.jpg`）。**签字与扫描必须由人完成，agent 不得代签，也不得直接提交 LaTeX 生成的未签字 PDF。**
- 支撑材料：`C<报名号>fj.rar` 或 `.zip`（非题目明确要求则可不交）。

## 九、交付前自检（逐项打勾）

- [ ] 模板已清理：无 `includegraphics{cat}` / `{gongzhonghao}`，无 `\CJK{UTF8}`，`\tihao{C}`，无重复 `bib:two`
- [ ] `pdflatex` 跑两遍，0 error、0 undefined reference
- [ ] 正文 ≤ 25 页，页眉仅队号 + 页码，无学校 / 姓名
- [ ] 摘要 ≤ 1 页，涵盖问题–方法–关键结果–结论
- [ ] Q1 基线不含 F02 / PulseRate，缺失结构以机理解释，未构建查表式"两阶段分类器"
- [ ] Q2 每个 call × 指标均给出可达性判定，不可达按"≤ 4 m"报告，未调阈值凑可解
- [ ] Q3 每模型记录事件数 / 协变量数，EPV ≥ 10；Brant 与 PH 检验已报告
- [ ] 论文每个数字可在 `results/*.json` 或 `code/` 中复现
- [ ] 每个检验三要素齐全；效应量 / CI"能给则给，否则说明原因"
- [ ] `random_state=42` + 包版本号 + `env.txt` 已就位
- [ ] 图 8–15 张，全部被正文引用，编号连续，英文 caption，≥300 dpi 或矢量
- [ ] 术语全文一致，无中英混排
- [ ] `ControlSheet.pdf` 已生成待人工签字，最终文件已重命名为 `C<报名号>.pdf` / `C<报名号>cns.pdf`
