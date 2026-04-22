import { computed, reactive, ref } from 'vue'
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
  const task = payload.tasks[0]
  return {
    currentModelVersion: currentVersion?.versionName ?? 'v-demo',
    currentModelName: currentVersion?.modelName ?? 'CTpath Temporal KG',
    recentTrainingTime: task?.finishedAt || task?.createdAt || '--',
    mrr: currentVersion?.metrics?.mrr ?? 0,
    hits1: currentVersion?.metrics?.hits1 ?? 0,
    hits10: currentVersion?.metrics?.hits10 ?? 0,
    datasetCoverage: payload.datasets.length ? 1 : 0,
    recentInferenceCalls: payload.dashboard?.activeDatasetCount ?? 0,
    fallbackRatio: payload.dashboard?.health.model_available ? 0.08 : 0.35,
    recentTrainingTaskStatus: task?.status ?? '无任务',
    source: 'mixed',
  }
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
  const datasetError = ref('')
  const taskError = ref('')
  const versionError = ref('')
  const opsError = ref('')
  const selectedDatasetId = ref('')
  const trainingError = ref('')
  const importError = ref('')
  const importSuccess = ref('')
  const params = ref<ModelTrainingParams>({ ...emptyParams })
  const modelName = ref('CTpath Temporal KG')
  const datasetName = ref('')
  const selectedFile = ref<File | null>(null)

  const isAuthenticated = computed(() => Boolean(currentUser.value))

  async function refreshAll() {
    if (!currentUser.value) return
    loading.value = true
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
    } else {
      await getModelHealth().then((value) => {
        health.value = value
      })
    }
  }

  async function submitLogin() {
    loadingLogin.value = true
    loginError.value = ''
    try {
      const session = await loginModelUser(username.value, password.value)
      saveModelSession(session)
      currentUser.value = session.user
      await refreshAll()
    } catch (error) {
      loginError.value = error instanceof Error ? error.message : '登录失败。'
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
    selectedDatasetId.value = ''
    datasetName.value = ''
    selectedFile.value = null
  }

  async function handleImportDataset() {
    if (!selectedFile.value) {
      importError.value = '请选择一个 CSV 文件。'
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
      importSuccess.value = `已导入 ${record.datasetName}。`
      datasetName.value = ''
      selectedFile.value = null
      await refreshAll()
      selectedDatasetId.value = record.datasetId
    } catch (error) {
      importError.value = error instanceof Error ? error.message : '导入失败。'
    } finally {
      loadingDataset.value = false
    }
  }

  async function handleCreateTask() {
    const selectedDataset = datasets.value.find((item) => item.datasetId === selectedDatasetId.value)
    if (!selectedDataset) {
      taskError.value = '请选择数据集。'
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
      taskError.value = error instanceof Error ? error.message : '创建训练任务失败。'
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
      versionError.value = error instanceof Error ? error.message : '发布失败。'
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
      versionError.value = error instanceof Error ? error.message : '回滚失败。'
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
      opsError.value = error instanceof Error ? error.message : '加载运营信息失败。'
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
    datasetError,
    taskError,
    versionError,
    opsError,
    selectedDatasetId,
    trainingError,
    importError,
    importSuccess,
    params,
    modelName,
    datasetName,
    selectedFile,
    isAuthenticated,
    board,
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

