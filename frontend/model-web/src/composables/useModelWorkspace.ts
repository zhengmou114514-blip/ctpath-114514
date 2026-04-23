import { computed, reactive, ref } from 'vue'
import { AxiosError } from 'axios'
import {
  createTrainingTask,
  deployModelVersion,
  getModelDashboard,
  getModelHealth,
  getModelOperations,
  importModelDataset,
  listModelDatasets,
  listModelVersions,
  listTrainingTasks,
  loginModelUser,
  rollbackModelVersion,
  type ModelBoardSnapshot,
  type ModelDashboardResponse,
  type ModelDatasetRecord,
  type ModelHealthResponse,
  type ModelOperationsResponse,
  type ModelTrainingParams,
  type ModelTrainingTaskRecord,
  type ModelUser,
  type ModelVersionRecord,
} from '../services/modelApi'
import { clearModelSession, readStoredModelSession, saveModelSession } from '../stores/modelSession'

const emptyParams: ModelTrainingParams = {
  epochs: 32,
  batchSize: 128,
  learningRate: 0.001,
  embeddingDim: 200,
  optimizer: 'adamw',
}

function buildBoardSnapshot(payload: {
  dashboard: ModelDashboardResponse | null
  datasets: ModelDatasetRecord[]
  tasks: ModelTrainingTaskRecord[]
  versions: ModelVersionRecord[]
}): ModelBoardSnapshot {
  const currentVersion = payload.versions.find((item) => item.deployed) ?? payload.versions[0]
  const latestTask = payload.tasks[0]
  const totalRows = payload.datasets.reduce((sum, item) => sum + item.rowCount, 0)

  return {
    currentModelVersion: currentVersion?.versionName ?? '未部署',
    currentModelName: currentVersion?.modelName ?? 'CTpath Temporal KG',
    recentTrainingTime: latestTask?.finishedAt || latestTask?.createdAt || '--',
    mrr: currentVersion?.metrics?.mrr ?? 0,
    hits1: currentVersion?.metrics?.hits1 ?? 0,
    hits10: currentVersion?.metrics?.hits10 ?? 0,
    datasetCoverage: totalRows > 0 ? 1 : 0,
    recentInferenceCalls: payload.dashboard?.loginCount ?? 0,
    fallbackRatio: payload.dashboard?.health.model_available ? 0.04 : 0.35,
    recentTrainingTaskStatus: latestTask?.status ?? 'no-task',
    source: 'api',
  }
}

function toErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
    if (error.message) return error.message
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

let singleton: ReturnType<typeof createModelWorkspace> | null = null

function createModelWorkspace() {
  const username = ref('model_admin')
  const password = ref('model123456')
  const loginError = ref('')
  const loadingLogin = ref(false)
  const currentUser = ref<ModelUser | null>(null)
  const health = ref<ModelHealthResponse | null>(null)
  const dashboard = ref<ModelDashboardResponse | null>(null)
  const datasets = ref<ModelDatasetRecord[]>([])
  const tasks = ref<ModelTrainingTaskRecord[]>([])
  const versions = ref<ModelVersionRecord[]>([])
  const operations = ref<ModelOperationsResponse | null>(null)
  const loading = ref(false)
  const loadingDataset = ref(false)
  const loadingTask = ref(false)
  const loadingVersion = ref(false)
  const loadingOps = ref(false)
  const workspaceError = ref('')
  const taskError = ref('')
  const versionError = ref('')
  const opsError = ref('')
  const selectedDatasetId = ref('')
  const importError = ref('')
  const importSuccess = ref('')
  const params = ref<ModelTrainingParams>({ ...emptyParams })
  const modelName = ref('CTpath Temporal KG')
  const datasetName = ref('')
  const selectedFile = ref<File | null>(null)

  const isAuthenticated = computed(() => Boolean(currentUser.value))
  const currentDeployment = computed(() => versions.value.find((item) => item.deployed) ?? versions.value[0] ?? null)

  async function refreshHealthOnly() {
    try {
      health.value = await getModelHealth()
    } catch (error) {
      workspaceError.value = toErrorMessage(error, '无法获取模型服务健康状态。')
    }
  }

  async function refreshAll() {
    if (!currentUser.value) {
      await refreshHealthOnly()
      return
    }

    loading.value = true
    workspaceError.value = ''
    try {
      const [dashboardResp, healthResp, datasetResp, taskResp, versionResp, operationsResp] = await Promise.all([
        getModelDashboard(),
        getModelHealth(),
        listModelDatasets(),
        listTrainingTasks(),
        listModelVersions(),
        getModelOperations(),
      ])
      dashboard.value = dashboardResp
      health.value = healthResp
      datasets.value = datasetResp
      tasks.value = taskResp
      versions.value = versionResp
      operations.value = operationsResp
      if (!selectedDatasetId.value && datasetResp[0]) {
        selectedDatasetId.value = datasetResp[0].datasetId
      }
    } catch (error) {
      workspaceError.value = toErrorMessage(error, '模型中心数据同步失败。')
      if (error instanceof AxiosError && error.response?.status === 401) {
        logout()
      }
    } finally {
      loading.value = false
    }
  }

  async function initialize() {
    const restored = readStoredModelSession()
    if (restored?.user) {
      currentUser.value = restored.user
      username.value = restored.user.username
    }
    if (restored?.token) {
      await refreshAll()
      if (!currentUser.value) {
        await refreshHealthOnly()
      }
      return
    }
    await refreshHealthOnly()
  }

  async function submitLogin() {
    loadingLogin.value = true
    loginError.value = ''
    try {
      const session = await loginModelUser(username.value, password.value)
      saveModelSession(session)
      currentUser.value = session.user
      username.value = session.user.username
      await refreshAll()
    } catch (error) {
      loginError.value = toErrorMessage(error, '模型管理端登录失败。')
    } finally {
      loadingLogin.value = false
    }
  }

  function logout() {
    clearModelSession()
    currentUser.value = null
    dashboard.value = null
    datasets.value = []
    tasks.value = []
    versions.value = []
    operations.value = null
    workspaceError.value = ''
    taskError.value = ''
    versionError.value = ''
    opsError.value = ''
    selectedDatasetId.value = ''
    datasetName.value = ''
    selectedFile.value = null
    importError.value = ''
    importSuccess.value = ''
    params.value = { ...emptyParams }
    modelName.value = 'CTpath Temporal KG'
    void refreshHealthOnly()
  }

  async function handleImportDataset() {
    if (!selectedFile.value) {
      importError.value = '请先选择待导入的训练 CSV 文件。'
      importSuccess.value = ''
      return
    }
    loadingDataset.value = true
    importError.value = ''
    importSuccess.value = ''
    try {
      const content = await selectedFile.value.text()
      const record = await importModelDataset({
        datasetName: datasetName.value.trim(),
        fileName: selectedFile.value.name,
        content,
      })
      importSuccess.value = `已导入训练数据集：${record.datasetName}`
      datasetName.value = ''
      selectedFile.value = null
      await refreshAll()
      selectedDatasetId.value = record.datasetId
    } catch (error) {
      importError.value = toErrorMessage(error, '训练数据集导入失败。')
    } finally {
      loadingDataset.value = false
    }
  }

  async function handleCreateTask() {
    const selectedDataset = datasets.value.find((item) => item.datasetId === selectedDatasetId.value)
    if (!selectedDataset) {
      taskError.value = '请先选择训练数据集。'
      return
    }
    loadingTask.value = true
    taskError.value = ''
    try {
      await createTrainingTask({
        datasetId: selectedDataset.datasetId,
        datasetName: selectedDataset.datasetName,
        modelName: modelName.value.trim() || 'CTpath Temporal KG',
        params: params.value,
      })
      await refreshAll()
    } catch (error) {
      taskError.value = toErrorMessage(error, '训练任务创建失败。')
    } finally {
      loadingTask.value = false
    }
  }

  async function handleDeploy(versionId: string) {
    loadingVersion.value = true
    versionError.value = ''
    try {
      await deployModelVersion(versionId)
      await refreshAll()
    } catch (error) {
      versionError.value = toErrorMessage(error, '模型版本发布失败。')
    } finally {
      loadingVersion.value = false
    }
  }

  async function handleRollback(versionId: string) {
    loadingVersion.value = true
    versionError.value = ''
    try {
      await rollbackModelVersion(versionId)
      await refreshAll()
    } catch (error) {
      versionError.value = toErrorMessage(error, '模型版本回滚失败。')
    } finally {
      loadingVersion.value = false
    }
  }

  async function refreshOperations() {
    loadingOps.value = true
    opsError.value = ''
    try {
      operations.value = await getModelOperations()
    } catch (error) {
      opsError.value = toErrorMessage(error, '模型运营信息获取失败。')
    } finally {
      loadingOps.value = false
    }
  }

  const board = computed(() =>
    buildBoardSnapshot({
      dashboard: dashboard.value,
      datasets: datasets.value,
      tasks: tasks.value,
      versions: versions.value,
    })
  )

  return reactive({
    username,
    password,
    loginError,
    loadingLogin,
    currentUser,
    health,
    dashboard,
    datasets,
    tasks,
    versions,
    operations,
    loading,
    loadingDataset,
    loadingTask,
    loadingVersion,
    loadingOps,
    workspaceError,
    taskError,
    versionError,
    opsError,
    selectedDatasetId,
    importError,
    importSuccess,
    params,
    modelName,
    datasetName,
    selectedFile,
    isAuthenticated,
    board,
    currentDeployment,
    initialize,
    submitLogin,
    logout,
    handleImportDataset,
    handleCreateTask,
    handleDeploy,
    handleRollback,
    refreshAll,
    refreshOperations,
  })
}

export function useModelWorkspace() {
  singleton ??= createModelWorkspace()
  return singleton
}
