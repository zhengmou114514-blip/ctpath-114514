# CTpath 慢病辅助诊疗业务系统

最后更新：2026-04-21

本仓库是一个“慢病辅助诊疗业务系统”，不是完整 HIS、完整 EMR、收费系统、住院系统、医保结算系统或药房库存系统。

项目目标是在慢病管理场景中，把业务工作台、患者档案、病程时间线、模型辅助建议、随访闭环、药品权限与治理能力组合成一个可运行、可演示、可继续扩展的医疗信息化原型。

## 给 AI 和开发者的快速结论

请优先阅读：

1. `AGENTS.md`
2. `README.md`
3. `docs/PROJECT_LOGIC_MANIFEST.md`
4. `frontend/src/router/index.ts`
5. `frontend/src/pages/AppWorkspacePage.vue`
6. `backend/app/main.py`

当前系统已经明确分为：

- 前端业务工作台：`frontend/`
- FastAPI 后端：`app/`
- 项目说明文档：`docs/`
- 本地 AI 协作规则：`AGENTS.md`

当前 canonical 前端入口是 Vue Router 中注册的页面。不要把历史 simple、legacy、backup、unused 页面当作主入口。

## 当前系统定位

系统聚焦慢病辅助诊疗，核心业务对象是慢病患者和其连续病程数据。

系统当前覆盖：

- 医生工作台
- 护士随访工作台
- 患者详情 / 电子档案
- 患者附件
- 药品管理
- 药品权限管理
- 模型洞察
- 模型看板
- 治理中心
- 登录认证、审计、限流、trace_id、异常处理等后端治理能力

系统当前不覆盖：

- 收费、结算、医保全流程
- 住院、床位、医嘱全流程
- 药房库存、采购、出入库
- 完整 HIS 或完整 EMR
- 正式训练中心和 CSV 数据导入工作流
- 完整处方流

## 当前前端技术栈

- Vue 3
- TypeScript
- Vue Router
- Pinia
- Element Plus
- ECharts
- Vite

前端启动：

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

前端最小闭环测试：

```powershell
cd E:\CTpath-master\frontend
npm test -- src/pages/__tests__/PatientDetailPage.spec.ts src/pages/__tests__/AppWorkspacePage.spec.ts
```

## 当前后端技术栈

- FastAPI
- Pydantic
- demo store / MySQL 双模式
- CTpath / CHRONIC 数据加载能力
- 慢病预测与建议服务
- SlowAPI 限流
- JWT 认证
- RBAC 权限能力
- TraceId 中间件
- 全局异常处理中间件
- 审计日志
- CORS

后端启动：

```powershell
cd E:\CTpath-master\backend
conda activate ctpath
uvicorn app.main:app --reload
```

默认访问：

- API: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- 前端开发服务: `http://127.0.0.1:5173`
- 模型 API: `http://127.0.0.1:8001`
- 模型前端开发服务: `http://127.0.0.1:5173`（`npm run dev:model`）

## demo / mysql 模式

系统根据 `CTPATH_DB_URL` 判断数据源模式。

- 未配置 `CTPATH_DB_URL` 时，后端会直接报错，除非显式开启 `CTPATH_ALLOW_DEMO_FALLBACK`
- 配置 MySQL 连接后，后端使用 MySQL，`/api/health` 返回 `mode=mysql`

MySQL 示例：

```powershell
$env:CTPATH_DB_URL="mysql+pymysql://root:your_password@127.0.0.1:3306/ctpath?charset=utf8mb4"
cd E:\CTpath-master\backend
uvicorn app.main:app --reload
```

初始化示例：

```powershell
Get-Content .\app\mysql_schema.sql | mysql -u root -p ctpath
Get-Content .\app\mysql_seed_demo.sql | mysql -u root -p ctpath
```

## 当前前端路由

`/login` 是独立登录页，`/` 是业务工作台壳层。两者已经分离。

当前主要路由：

- `/login`
- `/`
- `/patient-detail/:patientId?`
- `/nurse-followups`
- `/model-insight`
- `/model-dashboard`
- `/governance`
- `/drug-management`
- `/drug-permission-management`

主路由定义在：

- `frontend/src/router/index.ts`

业务壳层定义在：

- `frontend/src/pages/AppWorkspacePage.vue`
- `frontend/src/layouts/AppShell.vue`
- `frontend/src/components/AppSidebar.vue`
- `frontend/src/components/WorkspaceTopbar.vue`

## 当前前端界面状态

前端已按医疗工作台风格重构：

- 左侧稳定导航
- 顶部状态栏
- 单一主内容区
- 页面头部统一
- 蓝灰工作台色彩体系
- 字号、间距、卡片内边距统一
- loading、empty、error、degraded、no permission 状态有统一样式基础
- `/login` 与 `/` 业务壳层分离

核心页面当前职责：

| 页面 | 当前职责 | 主要文件 |
| --- | --- | --- |
| 登录页 | 账号登录、注册入口、健康状态展示 | `frontend/src/pages/LoginPage.vue`, `frontend/src/components/LoginScreen.vue` |
| 业务壳层 | 左导航、顶部状态栏、当前患者上下文、单一内容区 | `frontend/src/pages/AppWorkspacePage.vue`, `frontend/src/layouts/AppShell.vue` |
| 医生工作台 | 待处理患者、当前患者摘要、主动作入口 | `frontend/src/pages/DoctorDashboardPage.vue` |
| 患者详情 | 三栏布局：左档案/附件，中时间线/证据，右用药/建议/动作 | `frontend/src/pages/PatientDetailPage.vue` |
| 护士随访工作台 | 今日随访、未接通联系、医生复核、联系记录 | `frontend/src/pages/NurseFollowupsPage.vue` |
| 药品管理 | 药品目录、剂型规格、处方药、管制药、状态维护 | `frontend/src/pages/medication/DrugCatalogPage.vue` |
| 药品权限管理 | 角色级药品权限矩阵 | `frontend/src/pages/medication/permissions/DrugPermissionManagementPage.vue` |
| 模型洞察 | 当前患者预测、Top-K 风险、证据摘要、建议来源 | `frontend/src/pages/ModelInsightPage.vue` |
| 模型看板 | 模型版本、训练时间、MRR、Hits、调用量、回退比例、健康状态 | `frontend/src/pages/ModelDashboardPage.vue` |
| 治理中心 | 数据质量、异常时间线、冲突、待补全档案、治理动作 | `frontend/src/pages/GovernancePage.vue` |

## 当前后端模块

后端入口：

- `backend/app/main.py`

当前挂载的 API router：

- `app/api/analytics.py`
- `app/api/attachments.py`
- `app/api/audit.py`
- `app/api/auth.py`
- `app/api/authz.py`
- `app/api/drug_permissions.py`
- `app/api/drugs.py`
- `app/api/governance.py`
- `app/api/patient_medications.py`
- `app/api/patients.py`
- `app/api/predictions.py`
- `app/api/worklists.py`

当前主要服务：

- `app/services/drug_catalog_service.py`
- `app/services/drug_permission_service.py`
- `app/services/governance_service.py`
- `app/services/patient_attachment_service.py`
- `app/services/patient_medication_service.py`
- `app/services/medication_assessment_service.py`
- `app/services/suggestion_service.py`
- `app/services/llm_advice_service.py`
- `app/model_service.py`

当前中间件：

- `TraceIdMiddleware`
- `GlobalExceptionMiddleware`
- `JWTAuthMiddleware`
- `CORSMiddleware`
- SlowAPI rate limit handler

认证与权限相关：

- `app/api/auth.py`
- `app/api/authz.py`
- `app/auth/*`
- `app/middleware/jwt_auth.py`
- `app/auth/rbac_middleware.py`
- `app/auth/permission_registry.py`

## 当前完成状态

已完成或基本可用：

- 登录认证与 session 恢复
- 医生工作台
- 患者详情三栏布局
- 患者档案与附件能力
- 护士随访工作台基础视图
- 药品目录管理
- 药品权限矩阵
- 患者当前用药与用药充分性评估
- 模型洞察
- 模型看板
- 治理中心基础视图
- demo/mysql 模式
- JWT、trace_id、全局异常、限流、审计基础能力

## 当前最小业务闭环状态

当前仓库已经补通并验证了最小主闭环：

- 登录：`/login` 登录成功后进入工作台
- 工作台：从医生工作台打开患者详情
- 患者详情：在 `frontend/src/pages/PatientDetailPage.vue` 内点击 `Run Prediction` 或 `Refresh Prediction`
- 真实预测：前端通过 `workspace.runPrediction()` 调用真实 `POST /api/predict`
- 结果展示：页面优先展示 `workspace.predictionResult`，未触发前仅展示预置摘要
- 退出登录：从业务壳层退出后立即 `router.replace('/login')`

当前患者预测的真实行为说明：

- 页面初始可能显示 `Preloaded Summary`
- 这表示当前展示的是 `selectedPatient.predictions / careAdvice` 预置摘要
- 只有点击 `Run Prediction` 后，页面才会切到 `Latest Prediction`
- 若接口失败，页面会显示 `Prediction Failed`

当前测试与验收现状：

- 前端构建已通过：`cd frontend && npm run build`
- 后端合同测试已通过：`python E:\CTpath-master\test_closure_contract.py`
- 前端 P0 用例已可执行：
  - `src/pages/__tests__/PatientDetailPage.spec.ts`
  - `src/pages/__tests__/AppWorkspacePage.spec.ts`

本轮明确未处理：

- `/api/me`
- 未挂载的 `AuthStateMiddleware` / `RBACMiddleware` dead code
- 与系统中心相关的额外链路

部分完成 / 正在收口：

- 护士随访闭环的状态操作和细粒度权限体验
- 治理动作的闭环处理
- 药品权限与业务操作的前端提示细化
- LLM 建议服务的健康检查、降级和审计体验
- 模型看板与真实训练任务的后续衔接
- RBAC 权限覆盖的完整一致性

规划中 / 待完善：

- 模型调试台
- 导入暂存区
- CSV 校验、映射和问题查看
- 正式模型训练中心
- 更完整的数据脱敏策略
- 文件上传安全校验增强
- 更细粒度审计查询

## 开发约束

后续修改必须遵守：

- 不要把本项目扩展成完整 HIS
- 不要新增收费、住院、库存、医保结算模块
- 不要把 CSV 导入放进医生主流程
- 不要把模型训练功能塞进医生首页
- 不要把治理看板、模型看板、患者详情混在一个长页面里
- 不要修改后端接口字段名，除非同步更新前后端和文档
- 不要删除仍被 router、AppWorkspacePage、service、测试或文档显式引用的文件
- 不确定是否废弃的文件先保留

## 推荐 AI 接手顺序

新的 AI 接手本仓库时建议按这个顺序理解：

1. 读 `AGENTS.md`，确认项目边界和禁止事项
2. 读本 README，确认真实当前状态
3. 读 `docs/PROJECT_LOGIC_MANIFEST.md`，确认模块职责和 canonical 文件
4. 看 `frontend/src/router/index.ts`，确认前端入口
5. 看 `frontend/src/pages/AppWorkspacePage.vue` 和 `frontend/src/layouts/AppShell.vue`，确认壳层
6. 看 `backend/app/main.py`，确认后端路由和中间件
7. 再按具体任务进入对应页面或 API
## 2026-04-21 前端界面收口记录

本次前端界面收口只涉及前端工作台结构与视觉状态记录，不修改后端接口语义、不新增数据库结构、不新增训练中心、库存、收费、住院等模块。

关键结论：

- `/login` 已确认使用独立 `frontend/src/pages/LoginPage.vue`，不再复用业务工作台壳层。
- `/` 保持为业务工作台壳层，入口文件为 `frontend/src/pages/AppWorkspacePage.vue`，壳层布局由 `frontend/src/layouts/AppShell.vue` 承载。
- 当前业务主路由仍以 `frontend/src/router/index.ts` 为准，包含 `patient-detail`、`nurse-followups`、`model-insight`、`model-dashboard`、`governance`、`drug-management`、`drug-permission-management`。
- 医生工作台 `frontend/src/pages/DoctorDashboardPage.vue` 只保留待处理患者、当前患者摘要、风险提示和主要动作入口，不承载完整患者详情、完整模型看板或完整治理看板。
- 患者详情 `frontend/src/pages/PatientDetailPage.vue` 已按三栏工作站结构组织：左侧患者信息/电子档案/附件摘要，中间病程时间线/预测证据，右侧当前用药/用药评估/模型建议。
- 药品管理 `frontend/src/pages/medication/DrugCatalogPage.vue` 是标准后台表格页，围绕药品目录、剂型规格、处方药/管制药、状态和编辑表单组织。
- 药品权限管理 `frontend/src/pages/medication/permissions/DrugPermissionManagementPage.vue` 是角色权限矩阵页，围绕 doctor、nurse、pharmacist、archivist、admin 的查看、开立、审核、执行、管制药权限组织。
- 统一视觉规范集中在 `frontend/src/styles/workstation-theme.css`：页面标题 24px，区块标题 18px，卡片标题 16px，正文 14px，次级说明 12px，区块间距 24px，卡片内边距 16px，圆角不超过 8px。
- 色彩收敛为蓝灰医疗工作台主色，加 success / warning / danger / info 状态色，不使用大面积渐变或营销式视觉。
- 最近一次前端验收命令为 `cd frontend && npm run build`，结果通过；Vite 仅提示 chunk size warning，非构建失败。

后续 AI 接手时应注意：

- 判断前端当前有效页面时，以 `frontend/src/router/index.ts`、`frontend/src/pages/AppWorkspacePage.vue` 和各 canonical 页面为准。
- 不要重新新增 Simple / Center / Legacy / Backup 类重复页面。
- 不要把模型训练、CSV 导入、库存、收费、住院或完整处方流塞回医生工作台。
- 如果只做界面调整，不应修改 `app/*`、接口字段名、模型接口语义或数据库结构。
