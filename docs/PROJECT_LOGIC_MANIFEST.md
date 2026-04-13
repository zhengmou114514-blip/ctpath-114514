# 系统关键信息逻辑清单

> 本文档记录系统关键信息逻辑，避免后续读代码仓库时乱讲。基于当前仓库代码与 README 生成。

---

## 1. 系统定位

**基于时序知识图谱的慢性病辅助诊疗系统**

- **核心模型**：CTpath 时序知识图谱模型
- **应用场景**：慢性病辅助诊疗、风险识别、临床决策支持
- **目标用户**：门诊医生、档案员、护士、技术团队
- **系统模式**：
  - `mysql` 模式：读取 MySQL 中的患者与事件
  - `demo` 模式：使用内置演示数据
  - 模型回退：当患者样本较少时，从模型推理回退到相似病例辅助建议

---

## 2. 四层结构

### 2.1 数据层

**存储介质**：MySQL

**存储内容**：
- 医生账号信息
- 患者基本信息
- 时序事件（诊断、用药、随访等）
- 档案附件元数据
- 用药记录
- 训练任务记录

**关键表**：
- `doctor` - 医生账号
- `patient` - 患者信息
- `patient_event` - 时序事件
- `patient_attachment` - 档案附件
- `current_medication` - 当前用药
- `model_dataset` - 模型数据集
- `training_task` - 训练任务

### 2.2 模型层

**核心模型**：CTpath / CHRONIC 数据集推理

**模型能力**：
- Top-K 预测
- 风险等级评估
- 临床建议生成
- 用药方案推荐

**模型指标**（CHRONIC 数据集）：
- `MRR ≈ 0.345`
- `Hits@1 ≈ 0.232`
- `Hits@10 ≈ 0.515`

**模型回退机制**：
- 模型不可用时：回退到规则引擎
- 数据不足时：回退到相似病例
- 降级策略：规则/相似病例混合

### 2.3 服务层

**技术栈**：FastAPI

**核心接口**：
- `POST /api/login` - 登录认证
- `GET /api/patients` - 患者列表
- `GET /api/patient/{patient_id}` - 患者详情
- `GET /api/timeline/{patient_id}` - 病程时间线
- `POST /api/predict` - 模型预测
- `POST /api/advice/generate` - 临床建议生成
- `GET /api/health` - 系统健康状态
- `POST /api/patient/{patient_id}/medication-plan/generate` - 用药方案生成

**适配器模式**：
- `patientAttachmentAdapter` - 档案附件适配器
- `medicationAssessmentAdapter` - 用药评估适配器
- `modelTrainingAdapter` - 模型训练适配器
- `modelBoardAdapter` - 模型看板适配器

### 2.4 展示层

**技术栈**：Vue 3 + TypeScript

**核心组件**：
- `AppShell` - 应用壳层（侧边栏 + 主内容区）
- `AppSidebar` - 侧边导航
- `WorkspaceTopbar` - 顶部栏
- `RoleWorkspaceBanner` - 角色横幅

**页面组件**：
- `DoctorDashboardPage` - 医生首页
- `PatientArchivePage` - 患者档案页
- `ArchiveDetailPage` - 患者详情页
- `FollowupWorkbenchPage` - 随访工作台
- `GovernancePage` - 治理看板
- `ModelDashboardPage` - 模型看板
- `ModelInsightPage` - 模型洞察

---

## 3. 当前已有核心接口

### 3.1 认证接口

- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册
- `POST /api/logout` - 用户登出

### 3.2 患者接口

- `GET /api/patients` - 患者列表
- `GET /api/patient/{patient_id}` - 患者详情
- `POST /api/patient` - 创建患者
- `PUT /api/patient/{patient_id}` - 更新患者
- `GET /api/timeline/{patient_id}` - 病程时间线
- `POST /api/patient/{patient_id}/event` - 添加事件

### 3.3 预测接口

- `POST /api/predict` - 模型预测
- `POST /api/advice/generate` - 临床建议生成
- `POST /api/patient/{patient_id}/medication-plan/generate` - 用药方案生成

### 3.4 健康状态接口

- `GET /api/health` - 系统健康状态
  - 返回：`{ status, service, mode, model_available, model_error }`

### 3.5 档案附件接口（TODO）

- `GET /api/patient/{patient_id}/attachments` - 附件列表
- `POST /api/patient/{patient_id}/attachment` - 上传附件
- `GET /api/attachment/{attachment_id}` - 下载附件

**当前实现**：使用 `patientAttachmentAdapter` mock

### 3.6 用药评估接口（TODO）

- `GET /api/patient/{patient_id}/medications` - 当前用药列表
- `POST /api/patient/{patient_id}/medication` - 添加用药
- `GET /api/patient/{patient_id}/medication-assessment` - 用药充分性评估

**当前实现**：使用 `medicationAssessmentAdapter` mock

### 3.7 模型训练接口（TODO）

- `GET /api/model/datasets` - 数据集列表
- `POST /api/model/dataset` - 导入数据集
- `GET /api/model/training-tasks` - 训练任务列表
- `POST /api/model/training-task` - 创建训练任务
- `GET /api/model/training-task/{task_id}` - 训练任务详情

**当前实现**：使用 `modelTrainingAdapter` mock

---

## 4. 模块划分

### 4.1 医生首页（DoctorDashboardPage）

**职责**：
- 患者队列展示
- 患者搜索与筛选
- 风险等级标识
- 快速操作入口

**不包含**：
- ❌ 完整的治理看板
- ❌ 模型训练功能
- ❌ CSV 导入功能
- ❌ 患者详情编辑

**关键组件**：
- 患者列表表格
- 搜索筛选栏
- 风险等级徽章
- 操作按钮组

### 4.2 模型洞察（ModelInsightPage）

**职责**：
- 当前患者预测结果
- Top-K 风险事件
- 证据摘要
- 建议来源
- 模型可用/降级状态

**不包含**：
- ❌ 治理看板内容
- ❌ 数据质量概览
- ❌ 档案治理
- ❌ 训练任务

**关键组件**：
- 预测结果卡片
- 风险事件列表
- 证据摘要展示
- 建议来源追溯

### 4.3 模型看板（ModelDashboardPage）

**职责**：
- 模型版本信息
- 最近训练时间
- 性能指标（MRR / Hits@1 / Hits@10）
- 运行指标（推理调用量、回退比例）
- 模型状态监控

**不包含**：
- ❌ 当前患者建议卡片
- ❌ 治理看板内容
- ❌ 数据质量概览

**关键组件**：
- 模型状态卡片
- 性能指标网格
- 运行指标展示

### 4.4 治理看板（GovernancePage）

**职责**：
- 数据质量概览
- 缺失字段统计
- 异常时间线检测
- 待补全档案队列
- 冲突记录管理
- 最近治理动作
- 模型服务治理
- 档案治理
- 操作痕迹追溯

**不包含**：
- ❌ 当前患者预测结果
- ❌ 模型训练功能
- ❌ CSV 导入功能

**关键组件**：
- 数据质量卡片
- 模型服务治理卡片
- 档案治理表格
- 操作痕迹列表

### 4.5 患者档案（PatientArchivePage）

**职责**：
- 患者列表管理
- 档案创建
- 档案导入（JSON/Excel，非 CSV 训练数据）
- 档案导出
- 数据完整性检查

**不包含**：
- ❌ CSV 训练数据导入
- ❌ 模型训练功能
- ❌ 治理看板内容

**关键组件**：
- 档案列表表格
- 创建档案表单
- 导入导出功能
- 数据质量检查

### 4.6 患者详情（ArchiveDetailPage）

**职责**：
- 患者基本信息展示
- 病程时间线
- 事件补录
- 档案附件管理
- 当前用药管理
- 用药充分性评估

**不包含**：
- ❌ CSV 训练数据导入
- ❌ 模型训练功能
- ❌ 治理看板内容

**关键组件**：
- 患者信息卡片
- 病程时间线
- 事件编辑表单
- `PatientAttachmentPanel` - 档案附件面板
- `MedicationAdequacyPanel` - 用药评估面板

### 4.7 随访工作台（FollowupWorkbenchPage）

**职责**：
- 随访任务管理
- 患者联络记录
- 流转看板
- 任务状态更新

**不包含**：
- ❌ CSV 训练数据导入
- ❌ 模型训练功能
- ❌ 治理看板内容

**关键组件**：
- 任务列表
- 联络记录表单
- 流转状态看板

---

## 5. 每个模块的职责边界

### 5.1 医生首页

**输入**：
- 患者列表
- 搜索条件
- 风险筛选

**输出**：
- 筛选后的患者列表
- 患者详情入口
- 预测操作入口

**边界**：
- 只负责患者队列展示和快速操作
- 不承载完整的治理或模型功能

### 5.2 模型洞察

**输入**：
- 选中的患者
- 模型预测请求

**输出**：
- 预测结果
- 风险事件
- 证据摘要
- 建议来源

**边界**：
- 只负责当前患者的模型洞察
- 不包含模型训练或治理功能

### 5.3 模型看板

**输入**：
- 模型指标数据
- 系统健康状态

**输出**：
- 模型版本信息
- 性能指标
- 运行指标
- 模型状态

**边界**：
- 只负责模型运行状态和指标展示
- 不包含训练任务管理

### 5.4 治理看板

**输入**：
- 数据质量数据
- 治理模块状态
- 操作痕迹

**输出**：
- 数据质量概览
- 治理动作列表
- 操作痕迹追溯

**边界**：
- 只负责数据质量和治理监控
- 不包含模型训练功能

### 5.5 患者档案

**输入**：
- 患者列表
- 档案表单数据
- 导入文件（JSON/Excel）

**输出**：
- 档案列表
- 创建/更新结果
- 导出文件

**边界**：
- 只负责档案管理
- 不包含 CSV 训练数据导入

### 5.6 患者详情

**输入**：
- 患者ID
- 事件表单数据
- 附件文件
- 用药信息

**输出**：
- 患者详情
- 时间线
- 附件列表
- 用药评估结果

**边界**：
- 只负责单个患者的详细信息管理
- 不包含模型训练功能

### 5.7 随访工作台

**输入**：
- 随访任务列表
- 联络记录表单

**输出**：
- 任务状态
- 联络记录
- 流转状态

**边界**：
- 只负责随访任务管理
- 不包含模型训练功能

---

## 6. 新增功能应该放在哪里

### 6.1 患者照片/证件附件

**位置**：患者详情页（ArchiveDetailPage）

**组件**：`PatientAttachmentPanel`

**理由**：
- 附件是患者档案的一部分
- 应该在患者详情页中管理
- 不应放在医生首页或治理页

**已实现**：
- ✅ 患者照片上传
- ✅ 身份证照片
- ✅ 医保卡照片
- ✅ 转诊单/检查单附件
- ✅ 缩略图预览
- ✅ 大图查看
- ✅ 附件登记清单

### 6.2 当前用药/用药充分性

**位置**：患者详情页（ArchiveDetailPage）

**组件**：`MedicationAdequacyPanel`

**理由**：
- 用药信息是患者诊疗的一部分
- 应该在患者详情页中管理
- 用于医生核对模型建议后的临床用药覆盖情况

**已实现**：
- ✅ 当前用药清单
- ✅ 用药充分性评估
- ✅ 补录当前用药
- ✅ 刷新评估

### 6.3 CSV/训练中心

**位置**：治理看板（GovernancePage）- 离线训练标签

**理由**：
- 模型训练是技术团队的工作
- 不应放在医生首页、档案页或随访页
- 医生和档案员不需要关心模型训练细节

**已实现**：
- ✅ 数据集导入（CSV）
- ✅ 训练任务创建
- ✅ 训练参数配置
- ✅ 任务状态监控
- ✅ 训练日志查看

**明确说明**：
- 第283行："仅在模型中心进行 CSV 数据集导入，不在前台诊疗流程出现。"
- 第385行："本页将'数据集导入、训练任务、参数配置、训练日志'统一收纳到模型中心，医生/档案员主流程不再承载训练入口。"

---

## 7. 当前系统不允许出现的错误设计

### 7.1 模型页出现治理内容

**错误示例**：
- ❌ ModelInsightPage 中显示数据质量概览
- ❌ ModelDashboardPage 中显示档案治理表格
- ❌ 模型洞察页中显示操作痕迹

**正确设计**：
- ✅ ModelInsightPage 只显示当前患者的预测结果
- ✅ ModelDashboardPage 只显示模型运行状态和指标
- ✅ GovernancePage 才显示数据质量和治理内容

### 7.2 首页承载完整治理页

**错误示例**：
- ❌ DoctorDashboardPage 中嵌入完整的 GovernancePage
- ❌ 医生首页显示数据质量概览
- ❌ 医生首页显示档案治理表格

**正确设计**：
- ✅ DoctorDashboardPage 只显示患者队列和快速操作
- ✅ 治理看板是独立的页面
- ✅ 通过侧边导航切换，不堆叠在同一页面

### 7.3 CSV 作为前台建档主入口

**错误示例**：
- ❌ 患者档案页使用 CSV 导入作为主要建档方式
- ❌ 医生首页显示 CSV 导入按钮
- ❌ 随访页显示 CSV 导入功能

**正确设计**：
- ✅ 患者档案页使用 JSON/Excel 导入（档案数据）
- ✅ CSV 导入只在治理看板的离线训练标签中
- ✅ CSV 导入用于模型训练数据，不是档案数据

### 7.4 模块内容粘连

**错误示例**：
- ❌ 点击"模型洞察"后，页面中同时显示治理看板内容
- ❌ 点击"治理看板"后，页面中同时显示模型洞察内容
- ❌ 多个模块同时渲染在同一页面

**正确设计**：
- ✅ 使用 `v-if` / `v-else-if` 实现互斥渲染
- ✅ 每个导航项对应独立的页面组件
- ✅ 切换模块时清理上一个模块的状态

### 7.5 业务流程与技术流程混淆

**错误示例**：
- ❌ 医生在诊疗流程中看到模型训练参数
- ❌ 档案员在档案管理中看到训练任务状态
- ❌ 护士在随访任务中看到数据集导入功能

**正确设计**：
- ✅ 医生/档案员/护士只看到业务相关功能
- ✅ 技术团队在治理看板中管理模型训练
- ✅ 业务流程与技术流程分离

---

## 8. 后续给 Codex 写提示词时应遵守的规则

### 8.1 模块职责规则

**规则 1**：每个模块只负责自己的核心职责
```
医生首页 → 患者队列 + 快速操作
模型洞察 → 当前患者预测结果
模型看板 → 模型运行状态 + 指标
治理看板 → 数据质量 + 治理监控
患者档案 → 档案管理
患者详情 → 单个患者详细信息
随访工作台 → 随访任务管理
```

**规则 2**：不要跨模块堆叠功能
```
❌ 不要在医生首页嵌入完整治理看板
❌ 不要在模型洞察页显示数据质量
❌ 不要在患者档案页显示训练任务
```

### 8.2 功能放置规则

**规则 3**：患者相关功能放在患者详情页
```
✅ 患者照片/证件附件 → PatientAttachmentPanel → ArchiveDetailPage
✅ 当前用药/用药评估 → MedicationAdequacyPanel → ArchiveDetailPage
✅ 病程时间线 → ArchiveDetailPage
```

**规则 4**：模型训练功能放在治理看板
```
✅ CSV 数据集导入 → GovernancePage（离线训练标签）
✅ 训练任务创建 → GovernancePage（离线训练标签）
✅ 训练参数配置 → GovernancePage（离线训练标签）
```

**规则 5**：治理功能放在治理看板
```
✅ 数据质量概览 → GovernancePage
✅ 档案治理 → GovernancePage
✅ 操作痕迹 → GovernancePage
```

### 8.3 接口设计规则

**规则 6**：使用适配器模式 mock 缺失接口
```
✅ patientAttachmentAdapter - 档案附件适配器
✅ medicationAssessmentAdapter - 用药评估适配器
✅ modelTrainingAdapter - 模型训练适配器
```

**规则 7**：标注 TODO 说明接口状态
```
✅ TODO(api): 替换为后端对象存储与数据集注册服务
✅ TODO(api): 替换为后端用药评估服务
✅ TODO(api): 替换为后端模型训练服务
```

### 8.4 页面渲染规则

**规则 8**：使用互斥渲染，不允许多模块同时显示
```
✅ 使用 v-if / v-else-if 实现互斥
✅ 切换模块时清理状态
✅ 滚动位置重置到顶部
```

**规则 9**：不使用 display:none 假隐藏
```
❌ 不要用 display:none 隐藏模块
✅ 使用 v-if 条件渲染
✅ 确保未激活的模块不挂载
```

### 8.5 业务流程规则

**规则 10**：业务流程与技术流程分离
```
业务流程：医生诊疗、档案管理、随访任务
技术流程：模型训练、数据集管理、参数调优

✅ 医生/档案员/护士只看到业务流程
✅ 技术团队在治理看板管理技术流程
```

**规则 11**：CSV 导入不放在前台业务流程
```
❌ 不要在医生首页显示 CSV 导入
❌ 不要在患者档案页显示 CSV 导入
❌ 不要在随访页显示 CSV 导入

✅ CSV 导入只在治理看板的离线训练标签中
✅ CSV 用于模型训练数据，不是档案数据
```

### 8.6 类型定义规则

**规则 12**：使用 TypeScript 类型定义
```
✅ PatientAttachmentRecord - 附件记录类型
✅ CurrentMedicationItem - 当前用药类型
✅ MedicationAdequacyAssessment - 用药评估类型
✅ ModelTrainingTaskRecord - 训练任务类型
```

**规则 13**：不修改现有 API 字段名
```
❌ 不要修改已有的接口字段名
✅ 可以新增字段
✅ 可以使用适配器转换
```

### 8.7 验收规则

**规则 14**：每次修改后验证
```
✅ 编译成功
✅ 模块互斥渲染
✅ 功能放置正确
✅ 不出现错误设计
```

**规则 15**：输出验收清单
```
✅ 列出所有修改的文件
✅ 列出所有新增的功能
✅ 列出所有验证的项目
✅ 确认不违反错误设计规则
```

---

## 9. 附录：关键文件路径

### 9.1 页面组件

```
frontend/src/pages/
├── DoctorDashboardPage.vue       # 医生首页
├── PatientArchivePage.vue        # 患者档案页
├── ArchivePage.vue               # 档案路由页
├── archive/
│   ├── ArchiveDetailPage.vue     # 患者详情页
│   ├── ArchiveCreatePage.vue     # 创建档案页
│   ├── ArchiveImportPage.vue     # 导入档案页
│   └── ArchiveListPage.vue       # 档案列表页
├── FollowupWorkbenchPage.vue     # 随访工作台
├── GovernancePage.vue            # 治理看板（含模型中心）
├── ModelDashboardPage.vue        # 模型看板
└── ModelInsightPage.vue          # 模型洞察
```

### 9.2 核心组件

```
frontend/src/components/
├── AppSidebar.vue                # 侧边导航
├── RoleWorkspaceBanner.vue       # 角色横幅
├── WorkspaceTopbar.vue           # 顶部栏
├── archive/
│   └── PatientAttachmentPanel.vue # 档案附件面板
├── patient-workstation/
│   ├── MedicationAdequacyPanel.vue # 用药评估面板
│   └── PatientWorkstationBottomPanel.vue # 患者工作站底部面板
└── clinical/
    └── ClinicalAdviceCardBoard.vue # 临床建议卡片
```

### 9.3 适配器

```
frontend/src/services/
├── patientAttachmentAdapter.ts   # 档案附件适配器
├── medicationAssessmentAdapter.ts # 用药评估适配器
├── modelTrainingAdapter.ts       # 模型训练适配器
├── modelBoardAdapter.ts          # 模型看板适配器
└── types.ts                      # 类型定义
```

### 9.4 布局组件

```
frontend/src/layouts/
└── AppShell.vue                  # 应用壳层
```

### 9.5 状态管理

```
frontend/src/composables/
└── useWorkspaceController.ts     # 工作区状态控制器
```

---

## 10. 附录：系统健康状态说明

### 10.1 健康状态字段

```typescript
interface HealthResponse {
  status: string           // 系统状态
  service: string          // 服务名称
  mode: 'mysql' | 'demo'   // 运行模式
  model_available: boolean // 模型是否可用
  model_error: string | null // 模型错误信息
}
```

### 10.2 模式说明

**mysql 模式**：
- 读取 MySQL 中的患者与事件
- 需要配置数据库连接
- 适用于生产环境

**demo 模式**：
- 使用内置演示数据
- 不需要数据库
- 适用于演示和测试

### 10.3 模型回退机制

**模型可用**：
- 使用 CTpath 模型进行预测
- 返回 Top-K 预测结果

**模型不可用**：
- 回退到规则引擎
- 使用相似病例推荐
- 显示降级状态

**数据不足**：
- 回退到相似病例
- 显示数据支持度
- 建议补充数据

---

**文档版本**：v1.0  
**生成时间**：2026-04-13  
**基于代码**：当前仓库主分支
