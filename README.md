# 基于时序知识图谱的慢性病辅助诊疗系统

本项目在 CTpath 时序知识图谱模型基础上，扩展出一个可演示的慢病辅助诊疗系统，当前包含四层能力：

- 数据层：MySQL 存储医生账号、患者信息与时序事件
- 模型层：CTpath / CHRONIC 数据集推理，支持 Top-K 预测
- 服务层：FastAPI 提供登录、患者、时间线、预测接口
- 展示层：Vue 医生工作台，展示患者检索、病程时间线和辅助诊疗建议

## 快速开始

### 1. 激活环境

```powershell
conda activate ctpath
cd E:\CTpath-master
```

### 2. 可选：配置 MySQL

```powershell
$env:CTPATH_DB_URL="mysql+pymysql://root:你的密码@127.0.0.1:3306/ctpath?charset=utf8mb4"
```

导入表结构：

```powershell
Get-Content .\app\mysql_schema.sql | mysql -u root -p ctpath
Get-Content .\app\mysql_seed_demo.sql | mysql -u root -p ctpath
```

### 3. 启动后端

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. 启动前端

```powershell
cd E:\CTpath-master\frontend
cmd /c npm run dev
```

### 5. 演示地址

- 前端：http://127.0.0.1:5173
- 后端文档：http://127.0.0.1:8000/docs
- 演示账号：`doctor01 / ctpath123`

### 6. 可选：使用脚本快速启动

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

数据库演示模式：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1 `
  -DbUrl "mysql+pymysql://root:你的密码@127.0.0.1:3306/ctpath?charset=utf8mb4"
```

接口联调自检：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-demo.ps1
```

## 关键接口

- `POST /api/login`
- `GET /api/patients`
- `GET /api/patient/{patient_id}`
- `GET /api/timeline/{patient_id}`
- `POST /api/predict`
- `GET /api/health`

## 当前实验结果

`CHRONIC` 数据集上已有指标：

- `MRR ≈ 0.345`
- `Hits@1 ≈ 0.232`
- `Hits@10 ≈ 0.515`

## 说明

- 当 `/api/health` 返回 `mode=mysql` 时，系统读取 MySQL 中的患者与事件
- 当 `/api/health` 返回 `mode=demo` 时，系统自动回退到内置演示数据
- 当患者样本较少时，系统会从模型推理回退到相似病例辅助建议

详细说明见：

- [启动与演示说明](docs/启动与演示说明.md)
- [系统设计说明](docs/系统设计说明.md)
- [复试项目介绍](docs/复试项目介绍.md)
