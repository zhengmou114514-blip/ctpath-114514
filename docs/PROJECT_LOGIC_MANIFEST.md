# PROJECT_LOGIC_MANIFEST.md

最后更新：2026-04-21

本文档用于让其他 AI 或开发者快速理解本仓库的真实结构、模块边界和当前完成状态。它不是产品宣传文档，而是代码协作入口。

## 1. 项目定位

本项目是慢病辅助诊疗业务系统，不是完整 HIS。

核心目标：

- 提供接近真实医院工作站的慢病业务工作台
- 支持患者档案、电子档案、病程时间线和随访闭环
- 支持模型预测、建议生成、模型状态展示和模型治理
- 支持药品目录、当前用药、用药充分性评估和药品权限
- 支持数据质量、冲突、审计和治理中心能力

明确不做：

- 收费系统
- 住院系统
- 药房库存系统
- 医保结算系统
- 完整 HIS / 完整 EMR
- 完整处方流
- 医生主流程中的 CSV 导入
- 医生主流程中的模型训练中心

## 2. 当前技术栈

### 前端

目录：`frontend/`

- Vue 3
- TypeScript
- Vue Router
- Pinia
- Element Plus
- ECharts
- Vite

关键入口：

- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/router/index.ts`
- `frontend/src/pages/LoginPage.vue`
- `frontend/src/pages/AppWorkspacePage.vue`
- `frontend/src/layouts/AppShell.vue`
- `frontend/src/styles/workstation-theme.css`

### 后端

目录：`app/`

- FastAPI
- Pydantic
- demo store / MySQL 双模式
- CTpath / CHRONIC 数据加载
- 慢病预测服务
- LLM 建议服务
- JWT 认证
- RBAC 权限能力
- trace_id
- 全局异常处理
- 审计日志
- SlowAPI 限流

关键入口：

- `backend/app/main.py`
- `app/schemas.py`
- `app/store.py`
- `app/demo_store.py`
- `app/model_service.py`

## 3. 当前 canonical 前端结构

### 路由

当前 canonical 路由定义在 `frontend/src/router/index.ts`。

主路由：

- `/login`
- `/`
- `/patient-detail/:patientId?`
- `/nurse-followups`
- `/model-insight`
- `/model-dashboard`
- `/governance`
- `/drug-management`
- `/drug-permission-management`

规则：

- `/login` 只渲染独立登录页
- `/` 只渲染业务工作台壳层
- 子路由进入业务主内容区
- 不通过 `display:none` 假隐藏多个工作区
- 一个导航项只对应一个主内容区

### 壳层

当前业务壳层：

- `frontend/src/pages/AppWorkspacePage.vue`
- `frontend/src/layouts/AppShell.vue`
- `frontend/src/components/AppSidebar.vue`
- `frontend/src/components/WorkspaceTopbar.vue`
- `frontend/src/components/RoleWorkspaceBanner.vue`
- `frontend/src/components/PatientContextBar.vue`

壳层职责：

- 左侧稳定导航
- 顶部状态栏
- 当前患者上下文条
- 统一消息状态
- 单一主内容区
- 角色可访问模块切换

### 统一样式

当前工作台主题：

- `frontend/src/styles/workstation-theme.css`

已统一：

- 页面标题 24px
- 区块标题 18px
- 卡片标题 16px
- 正文 14px
- 次级说明 12px
- 区块间距 24px
- 卡片内边距 16px
- 卡片和按钮圆角 8px
- 蓝灰医疗工作台色彩
- success / warning / danger / info 状态色
- Element Plus 基础覆盖

## 4. 前端模块边界

### 登录页

文件：

- `frontend/src/pages/LoginPage.vue`
- `frontend/src/components/LoginScreen.vue`

职责：

- 登录
- 注册入口
- 展示后端健康状态、运行模式和模型可用状态
- 登录后重定向到业务工作台

禁止：

- 承载业务工作台内容
- 作为营销页
- 展示完整业务模块

### 医生工作台

文件：

- `frontend/src/pages/DoctorDashboardPage.vue`

职责：

- 待处理患者队列
- 当前患者摘要
- 风险提示
- 打开患者详情、档案和随访的主动作入口

禁止：

- 展示完整患者详情
- 展示完整模型看板
- 展示完整治理中心
- 堆叠所有业务页

### 患者详情 / 电子档案

文件：

- `frontend/src/pages/PatientDetailPage.vue`
- `frontend/src/components/patient/PatientAttachmentPanel.vue`
- `frontend/src/components/medication/PatientMedicationClosurePanel.vue`

当前布局：

- 左栏：患者主信息、档案状态、附件
- 中栏：预测摘要、病程时间线、证据摘要
- 右栏：当前用药、用药评估、建议摘要、下一步动作

职责：

- 当前患者核心工作区
- 患者主信息
- 病程时间线
- 当前用药
- 模型预测摘要
- 建议摘要
- 随访入口
- 附件预览

禁止：

- 展示全局模型训练指标
- 展示全局治理看板
- 承载 CSV 导入或训练中心

### 护士随访工作台

文件：

- `frontend/src/pages/NurseFollowupsPage.vue`
- `frontend/src/pages/FollowupWorkbenchPage.vue`

职责：

- 今日待随访
- 未接通联系
- 医生复核队列
- 联系记录
- 随访状态和下一次计划

状态：

- 基础工作台已存在
- 更完整的状态操作、关闭任务和细粒度权限体验仍在收口

### 药品管理

文件：

- `frontend/src/pages/medication/DrugCatalogPage.vue`
- `app/api/drugs.py`
- `app/services/drug_catalog_service.py`

职责：

- 药品目录
- 通用名
- 品牌名
- 剂型规格
- 单位
- 是否处方药
- 是否管制药
- 启用/停用状态
- 适应症

禁止：

- 做库存
- 做采购
- 做药房出入库
- 做完整处方流

### 药品权限管理

文件：

- `frontend/src/pages/medication/permissions/DrugPermissionManagementPage.vue`
- `app/api/drug_permissions.py`
- `app/services/drug_permission_service.py`

职责：

- 角色级药品权限矩阵
- 查看权限
- 开立权限
- 审核权限
- 执行权限
- 管制药权限

当前角色：

- doctor
- nurse
- pharmacist
- archivist
- admin

注意：

- 前端登录用户目前主要是 doctor / nurse / archivist
- drug permission service 已为更完整业务角色预留权限矩阵

### 模型洞察

文件：

- `frontend/src/pages/ModelInsightPage.vue`
- `app/api/predictions.py`
- `app/model_service.py`

职责：

- 当前患者预测结果
- Top-K 风险事件
- 证据摘要
- 建议来源
- 模型降级状态
- 当前患者下一步动作

禁止：

- 全局模型版本总览
- 全局训练指标
- 训练任务列表
- CSV 数据集导入

### 模型看板

文件：

- `frontend/src/pages/ModelDashboardPage.vue`
- `frontend/src/services/modelBoardAdapter.ts`
- `app/api/analytics.py`

职责：

- 模型版本
- 最近训练时间
- MRR
- Hits@1
- Hits@10
- 调用量
- 回退比例
- 模型健康状态

禁止：

- 当前患者详情
- 当前患者建议卡片
- 治理中心的数据质量列表

### 治理中心

文件：

- `frontend/src/pages/GovernancePage.vue`
- `app/api/governance.py`
- `app/api/audit.py`
- `app/services/governance_service.py`

职责：

- 数据质量概览
- 缺失字段
- 异常时间线
- 待补全档案
- 冲突记录
- 治理动作记录

禁止：

- 当前患者预测结果
- 模型训练指标总览
- 医生首页摘要卡

## 5. 后端 API 和中间件状态

### 当前挂载 router

在 `backend/app/main.py` 中挂载：

- `analytics`
- `attachments`
- `audit`
- `auth`
- `authz`
- `drug_permissions`
- `drugs`
- `governance`
- `patient_medications`
- `patients`
- `predictions`
- `worklists`

### 当前中间件链路

`backend/app/main.py` 中实际加入：

- `CORSMiddleware`
- `JWTAuthMiddleware`
- `GlobalExceptionMiddleware`
- `TraceIdMiddleware`

注释中说明请求经过顺序：

```text
TraceIdMiddleware -> GlobalExceptionMiddleware -> JWTAuthMiddleware -> CORSMiddleware
```

限流能力：

- `app/middleware/rate_limit.py`
- `slowapi`
- `RateLimitExceeded` handler

异常处理：

- `app/errors.py`
- `app/middleware/exception.py`

审计：

- `app/api/audit.py`
- `app/audit/operation_audit.py`
- `app/audit/system_audit.py`

权限：

- `app/auth/*`
- `app/api/authz.py`
- `app/middleware/jwt_auth.py`

## 6. 数据源和运行模式

系统必须区分三类概念：

1. 业务数据源：`demo` / `mysql`
2. 模型状态：available / degraded / unavailable
3. 训练数据来源：dataset / csv / staging import

当前实际状态：

- demo 模式可运行
- MySQL 模式通过 `CTPATH_DB_URL` 启用
- `/api/health` 返回服务状态、运行模式和模型可用状态
- CTpath / CHRONIC 数据可在启动时加载到 demo 数据中
- CSV 正式导入暂存区仍未完成
- 正式训练中心仍未完成

## 7. 当前完成状态

### 已完成或基本可用

- 独立登录页
- 业务工作台壳层
- 左侧导航、顶部状态栏、当前患者上下文
- 医生工作台
- 患者详情三栏布局
- 患者附件面板
- 当前用药与用药充分性评估
- 护士随访工作台基础视图
- 药品目录管理
- 药品权限矩阵
- 模型洞察
- 模型看板
- 治理中心基础视图
- demo/mysql 运行模式
- JWT、trace_id、全局异常、限流、审计基础能力

### 部分完成 / 正在收口

- 护士随访任务状态的完整闭环体验
- 治理动作的可操作闭环
- 药品权限与实际业务按钮的前端提示联动
- LLM 建议服务的稳定性、降级说明和审计体验
- RBAC 权限覆盖一致性
- 模型看板与真实训练任务的更深衔接

### 规划中 / 待完善

- 模型调试台
- 导入暂存区
- CSV 校验、映射、问题查看
- 正式模型训练中心
- 文件上传安全校验增强
- 数据脱敏策略增强
- 更细粒度审计查询
- 更完整的权限管理 UI

## 8. 当前不应误判的历史内容

仓库历史中可能出现过 simple、legacy、backup、unused 或被替代页面。判断当前页面是否有效时，以 `frontend/src/router/index.ts` 和 `frontend/src/pages/AppWorkspacePage.vue` 为准。

不要把以下内容当作当前目标：

- 完整 HIS 模块地图
- 大型医院全流程页面
- 营销型首页
- 医生首页里的模型训练或 CSV 导入
- 一个长页面堆叠多个模块
- 被 router 移除或无引用的旧页面

## 9. 建议 AI 修改流程

其他 AI 接手后请按以下流程：

1. 先读 `AGENTS.md`
2. 再读 `README.md`
3. 再读本 manifest
4. 用 `rg` 确认目标文件是否被引用
5. 先判断属于哪个模块
6. 只修改该模块相关文件
7. 不改后端字段名，除非任务明确要求并同步前后端
8. 不新增收费、住院、库存、完整处方流
9. 不确定是否废弃的文件不要删除
10. 修改后至少运行对应构建或验证命令

## 10. 常用命令

后端：

```powershell
cd E:\CTpath-master
conda activate ctpath
cd E:\\CTpath-master\\backend
cd E:\CTpath-master\backend
uvicorn app.main:app --reload
```

前端：

```powershell
cd E:\CTpath-master\frontend
npm install
npm run dev
```

前端构建：

```powershell
cd E:\CTpath-master\frontend
npm run build
```

后端导入检查：

```powershell
cd E:\CTpath-master
conda activate ctpath
python -c "import app.main; print('backend import ok')"
```
# 2026-04-21 Frontend Closure Notes

This section records the current frontend closure state for future AI agents and developers. It is intentionally narrow: it documents the current canonical frontend structure and visual constraints, and does not imply backend API, database, training-center, inventory, billing, inpatient, or prescription-flow changes.

## Current Canonical Frontend Entry Points

- `/login` is an independent login route. It uses `frontend/src/pages/LoginPage.vue` and `frontend/src/components/LoginScreen.vue`.
- `/` is the authenticated business workspace shell. It uses `frontend/src/pages/AppWorkspacePage.vue`.
- The shell layout is implemented by `frontend/src/layouts/AppShell.vue`, with sidebar, top status bar, role banner, patient context bar, and one main content region.
- The canonical route list is defined in `frontend/src/router/index.ts`.

## Current Business Routes

- `/patient-detail/:patientId?`
- `/nurse-followups`
- `/model-insight`
- `/model-dashboard`
- `/governance`
- `/drug-management`
- `/drug-permission-management`

Do not treat old simple, legacy, backup, unused, or center-style pages as canonical unless they are explicitly mounted by `frontend/src/router/index.ts` or by the current workspace shell.

## Current Page Boundaries

- Doctor dashboard: `frontend/src/pages/DoctorDashboardPage.vue`
  - Entry summary only.
  - Shows pending patients, current patient summary, risk hints, and two to three primary actions.
  - Must not host full patient detail, full model dashboard, full governance dashboard, long stacked tables, training import, inventory, billing, or inpatient flows.
- Patient detail: `frontend/src/pages/PatientDetailPage.vue`
  - Three-column clinical layout.
  - Left: patient profile, electronic archive, attachment summary.
  - Center: disease timeline, prediction summary, evidence summary.
  - Right: current medication, medication assessment, model advice, next actions.
- Drug management: `frontend/src/pages/medication/DrugCatalogPage.vue`
  - Standard admin table page for drug catalog maintenance.
  - Covers generic name, brand name, dosage form, specification, unit, prescription flag, controlled-drug flag, status, and indication.
- Drug permission management: `frontend/src/pages/medication/permissions/DrugPermissionManagementPage.vue`
  - Permission matrix page.
  - Covers doctor, nurse, pharmacist, archivist, admin role mappings for view, prescribe, review, execute, and controlled-drug permissions.
- Model insight: `frontend/src/pages/ModelInsightPage.vue`
  - Current-patient model insight only.
- Model dashboard: `frontend/src/pages/ModelDashboardPage.vue`
  - Model-level monitoring and governance metrics only.
- Governance center: `frontend/src/pages/GovernancePage.vue`
  - Data quality, conflict, audit, and governance action status only.

## Current Visual Contract

The shared workstation visual contract lives in `frontend/src/styles/workstation-theme.css`.

- Page title: 24px.
- Section title: 18px.
- Card title: 16px.
- Body text: 14px.
- Secondary text: 12px.
- Section spacing: 24px.
- Card padding: 16px.
- Card and button radius: 8px or less.
- Main palette: blue-gray medical workstation colors.
- Status colors: success, warning, danger, info.
- Avoid large gradients, marketing-style hero layouts, decorative blobs, and generic admin-template visual noise.

## Recent Verification

After the frontend closure pass, `cd frontend && npm run build` completed successfully. Vite reported a chunk size warning only; this is not a build failure.


