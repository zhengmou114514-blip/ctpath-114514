import type { DoctorUser, PatientCase } from './types'

const doctors: DoctorUser[] = [
  {
    username: 'doctor01',
    password: 'ctpath123',
    name: '胡军',
    title: '主治医师',
    department: '慢病管理中心',
  },
  {
    username: 'endocrine',
    password: 'diabetes123',
    name: '李敏',
    title: '副主任医师',
    department: '内分泌科',
  },
]

const coreCases: PatientCase[] = [
  {
    patientId: 'PID0248',
    name: '张晨',
    age: 44,
    gender: '男',
    primaryDisease: '糖尿病',
    currentStage: 'Late',
    riskLevel: '高风险',
    lastVisit: '2023-10-28',
    summary: '糖尿病晚期患者，合并心血管既往史，近期服药依从性下降，需重点关注并发症风险。',
    stats: [
      { label: '收缩压', value: '133 mmHg', trend: '较上次 +6' },
      { label: '胆固醇', value: '226 mg/dL', trend: '高于目标区间' },
      { label: 'BMI', value: '19.7', trend: '稳定' },
      { label: '服药依从性', value: 'Low', trend: '需强化管理' },
    ],
    timeline: [
      {
        date: '2023-06-14',
        type: 'visit',
        title: '例行复诊',
        detail: '记录血糖控制不稳，存在运动依从性下降。',
      },
      {
        date: '2023-08-05',
        type: 'diagnosis',
        title: '病程阶段进展',
        detail: '病程由 Mid 转为 Late，同时合并心血管既往史。',
      },
      {
        date: '2023-09-12',
        type: 'medication',
        title: '药物剂量调整',
        detail: 'MedicationDose 升高，提示强化干预。',
      },
      {
        date: '2023-10-28',
        type: 'risk',
        title: '当前风险评估',
        detail: '高胆固醇、低依从性与晚期阶段叠加，进入高风险队列。',
      },
    ],
    predictions: [
      {
        label: '并发症风险升高',
        score: 0.83,
        reason: '阶段为 Late，合并 Heart Disease，MedicationAdherence 为 Low。',
      },
      {
        label: '病情维持高风险',
        score: 0.71,
        reason: '连续多次记录显示血压与胆固醇分箱维持在高位。',
      },
      {
        label: '短期波动回落',
        score: 0.42,
        reason: '若依从性改善与运动增加，风险存在回落空间。',
      },
    ],
    pathExplanation: [
      '患者 -> has_disease -> 糖尿病',
      '糖尿病 @ t-2 -> stage -> Late',
      'Late + Heart Disease -> risk -> complication',
    ],
    followUps: [
      { title: '复查空腹血糖与糖化血红蛋白', owner: '内分泌门诊', dueDate: '2023-11-10', priority: 'high' },
      { title: '评估服药依从性干预效果', owner: '慢病管理师', dueDate: '2023-11-03', priority: 'high' },
      { title: '更新运动与饮食计划', owner: '健康教育师', dueDate: '2023-11-05', priority: 'medium' },
    ],
    recommendationMode: 'model',
    dataSupport: 'high',
    careAdvice: [
      '建议 2 周内完成血糖、血压与血脂联合复查。',
      '优先进行服药依从性随访，并结合饮食与运动方案强化管理。',
      '若出现心血管不适症状，应提前安排专科会诊。',
    ],
    similarCases: [
      {
        caseId: 'SC-101',
        disease: '糖尿病 + 心血管病史',
        matchScore: 0.91,
        summary: '相似患者在依从性改善后 1 个随访周期内风险下降。',
        suggestion: '优先采用强化依从性管理与复查提醒机制。',
      },
    ],
  },
  {
    patientId: 'PID0031',
    name: '李雪',
    age: 87,
    gender: '女',
    primaryDisease: '帕金森病',
    currentStage: 'Mid',
    riskLevel: '中风险',
    lastVisit: '2023-03-17',
    summary: '帕金森患者整体病程平稳，近期重点观察认知与情绪波动对生活质量的影响。',
    stats: [
      { label: '心率', value: '70 bpm', trend: '平稳' },
      { label: '睡眠时长', value: '7.9 h', trend: '较前次 -0.6h' },
      { label: '认知评分', value: '17', trend: '轻度下降' },
      { label: '服药依从性', value: 'High', trend: '管理较好' },
    ],
    timeline: [
      {
        date: '2022-11-02',
        type: 'visit',
        title: '神经科随访',
        detail: '记录睡眠时长下降，步数波动明显。',
      },
      {
        date: '2023-01-10',
        type: 'diagnosis',
        title: '阶段维持 Mid',
        detail: '认知评分保持稳定，但情绪评分出现下降。',
      },
      {
        date: '2023-02-21',
        type: 'medication',
        title: '维持药物治疗',
        detail: 'MedicationDose 基本稳定，依从性为 High。',
      },
      {
        date: '2023-03-17',
        type: 'risk',
        title: '中风险提醒',
        detail: '需关注睡眠和压力水平对病程的影响。',
      },
    ],
    predictions: [
      {
        label: '病情稳定维持',
        score: 0.68,
        reason: '当前依从性较高，近期无明显阶段恶化信号。',
      },
      {
        label: '认知评分下降风险',
        score: 0.57,
        reason: 'StressLevel 与 MoodScore 存在持续波动。',
      },
      {
        label: '短期恶化',
        score: 0.29,
        reason: '近期未观察到连续高危路径。',
      },
    ],
    pathExplanation: [
      '患者 -> has_disease -> 帕金森病',
      '帕金森病 @ t-1 -> cognitive_bin -> Q2',
      'Q2 + stress_bin=Q3 -> risk -> decline',
    ],
    followUps: [
      { title: '复查认知与情绪评分', owner: '神经内科', dueDate: '2023-03-28', priority: 'medium' },
      { title: '评估夜间睡眠管理效果', owner: '护理团队', dueDate: '2023-03-25', priority: 'medium' },
      { title: '更新步态训练记录', owner: '康复治疗师', dueDate: '2023-03-23', priority: 'low' },
    ],
    recommendationMode: 'model',
    dataSupport: 'medium',
    careAdvice: [
      '建议继续保持当前用药方案，并加强认知与情绪联合随访。',
      '增加睡眠质量问卷与跌倒风险评估。',
      '安排康复训练记录回访，提升长期趋势观察质量。',
    ],
    similarCases: [
      {
        caseId: 'SC-210',
        disease: '帕金森病',
        matchScore: 0.87,
        summary: '相似病例在连续睡眠干预后认知评分趋于稳定。',
        suggestion: '优先监控睡眠-认知联动指标。',
      },
    ],
  },
  {
    patientId: 'PID0024',
    name: '王建',
    age: 53,
    gender: '男',
    primaryDisease: '阿尔茨海默病',
    currentStage: 'Early',
    riskLevel: '中风险',
    lastVisit: '2022-08-31',
    summary: '阿尔茨海默病早期患者，当前重点在于维持认知功能并强化照护协同。',
    stats: [
      { label: '认知评分', value: '11', trend: '需持续观察' },
      { label: '睡眠时长', value: '4.5 h', trend: '偏低' },
      { label: '支持系统', value: 'Moderate', trend: '有改善空间' },
      { label: '照护人', value: 'No', trend: '建议补充' },
    ],
    timeline: [
      {
        date: '2022-05-12',
        type: 'visit',
        title: '记忆门诊建档',
        detail: '建立患者档案，记录初诊生命体征与生活方式。',
      },
      {
        date: '2022-06-19',
        type: 'diagnosis',
        title: '确认为 Early 阶段',
        detail: '认知评分偏低，但家庭支持度中等。',
      },
      {
        date: '2022-07-27',
        type: 'medication',
        title: '开始干预方案',
        detail: '引入照护人协同管理，监测服药依从性。',
      },
      {
        date: '2022-08-31',
        type: 'risk',
        title: '风险随访',
        detail: '当前仍以中风险为主，建议继续跟踪。',
      },
    ],
    predictions: [
      {
        label: '阶段维持 Early',
        score: 0.64,
        reason: '支持系统和照护条件相对稳定，尚未出现连续恶化路径。',
      },
      {
        label: '认知波动加剧',
        score: 0.49,
        reason: '认知评分与睡眠时长存在轻度下行趋势。',
      },
      {
        label: '快速进展',
        score: 0.21,
        reason: '当前路径权重不足以支撑高危预测。',
      },
    ],
    pathExplanation: [
      '患者 -> has_disease -> 阿尔茨海默病',
      '阿尔茨海默病 @ t-1 -> support_system -> Moderate',
      'Moderate + caregiver=0 -> risk -> fluctuation',
    ],
    followUps: [
      { title: '补充家庭照护方案', owner: '老年医学科', dueDate: '2022-09-09', priority: 'high' },
      { title: '追踪睡眠干预反馈', owner: '护理团队', dueDate: '2022-09-05', priority: 'medium' },
      { title: '更新家庭支持评估', owner: '社工团队', dueDate: '2022-09-12', priority: 'medium' },
    ],
    recommendationMode: 'similar-case',
    dataSupport: 'low',
    careAdvice: [
      '当前患者同类时序样本较少，建议采用相似病例库与规则模板联合辅助。',
      '优先增加认知评分、照护参与度和睡眠质量的连续采集。',
      '在数据积累不足阶段，模型输出仅作为辅助参考，不作为单独决策依据。',
    ],
    similarCases: [
      {
        caseId: 'SC-301',
        disease: '阿尔茨海默病早期',
        matchScore: 0.89,
        summary: '相似病例通过家庭照护介入后，睡眠与情绪指标改善。',
        suggestion: '优先补充照护人介入与睡眠管理方案。',
      },
      {
        caseId: 'SC-318',
        disease: '认知下降伴支持系统不足',
        matchScore: 0.84,
        summary: '相似病例在连续随访 2 周后风险维持稳定。',
        suggestion: '建议缩短复诊周期并增加家庭支持评估。',
      },
    ],
  },
]

const generatedCases: PatientCase[] = Array.from({ length: 18 }, (_, index) => {
  const template = coreCases[index % coreCases.length]
  const suffix = String(index + 1).padStart(2, '0')
  return {
    ...template,
    patientId: `PX${suffix}${template.patientId.slice(-2)}`,
    name: `${template.name}${index + 1}`,
    age: template.age + (index % 4),
    lastVisit: `2023-${String((index % 9) + 1).padStart(2, '0')}-${String((index % 18) + 10).padStart(2, '0')}`,
  }
})

const patientCases: PatientCase[] = [...coreCases, ...generatedCases]

export function loginDoctor(username: string, password: string): DoctorUser | null {
  return doctors.find((doctor) => doctor.username === username && doctor.password === password) ?? null
}

export function getPatients(): PatientCase[] {
  return patientCases
}

export function getPatientCase(patientId: string): PatientCase | undefined {
  return patientCases.find((item) => item.patientId === patientId)
}
