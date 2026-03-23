INSERT INTO patients (
  patient_id, name, gender, age, primary_disease, current_stage, risk_level, last_visit, summary, data_support
) VALUES
  ('PID9001', '测试患者A', '女', 58, '2型糖尿病', 'Mid', '中风险', '2025-03-15', '近3个月血糖波动，需要继续随访观察。', 'high'),
  ('PID9002', '测试患者B', '男', 66, '慢性肾病', 'Mid', '中风险', '2025-03-12', '肾功能指标缓慢恶化，近期睡眠质量下降。', 'medium'),
  ('PID9003', '测试患者C', '女', 62, '阿尔茨海默病', 'Early', '中风险', '2025-03-10', '当前结构化样本偏少，以案例辅助模式为主。', 'low')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  gender = VALUES(gender),
  age = VALUES(age),
  primary_disease = VALUES(primary_disease),
  current_stage = VALUES(current_stage),
  risk_level = VALUES(risk_level),
  last_visit = VALUES(last_visit),
  summary = VALUES(summary),
  data_support = VALUES(data_support);

INSERT INTO patient_events (patient_id, event_time, relation, object_value, note, source) VALUES
  ('PID9001', '2025-02-10 09:00:00', 'has_disease', 'Diabetes', '门诊确认为 2 型糖尿病，纳入慢病管理。', 'seed'),
  ('PID9001', '2025-03-01 10:00:00', 'stage', 'Mid', '阶段评估为 Mid，建议缩短复诊间隔。', 'seed'),
  ('PID9001', '2025-03-15 08:30:00', 'med_adherence', 'Low', '近期存在漏服药情况，依从性下降。', 'seed'),
  ('PID9002', '2025-02-14 14:00:00', 'has_disease', 'CKD', '门诊随访记录慢性肾病病程。', 'seed'),
  ('PID9002', '2025-03-02 08:00:00', 'stage', 'Mid', '当前阶段保持 Mid。', 'seed'),
  ('PID9002', '2025-03-12 09:20:00', 'mood_bin', 'Q2', '情绪评分下降，需要继续观察。', 'seed'),
  ('PID9003', '2025-01-20 15:00:00', 'has_disease', 'Alzheimer''s', '记忆门诊完成首诊评估。', 'seed'),
  ('PID9003', '2025-02-18 09:10:00', 'support_system', 'Moderate', '家庭支持一般，需要增加随访提醒。', 'seed'),
  ('PID9003', '2025-03-10 10:10:00', 'sleep_hours_bin', 'Q1', '近期睡眠时间减少，进入案例辅助模式。', 'seed');
