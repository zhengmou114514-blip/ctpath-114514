INSERT INTO patients (
  patient_id, name, gender, age, avatar_url, phone, emergency_contact_name, emergency_contact_relation, emergency_contact_phone,
  primary_disease, current_stage, risk_level, last_visit, summary, data_support
) VALUES
  ('PID0025', '周建华', '男', 72, 'https://api.dicebear.com/9.x/initials/svg?seed=%E5%91%A8%E5%BB%BA%E5%8D%8E', '13800010025', '周敏', '女儿', '13800020025', 'Parkinson''s', 'Mid', '高风险', '2025-03-18', '来源于 CHRONIC 的帕金森病中期病例模式，重点关注步态波动、依从性与复诊节奏。', 'high'),
  ('PID0078', '刘淑琴', '女', 79, 'https://api.dicebear.com/9.x/initials/svg?seed=%E5%88%98%E6%B7%91%E7%90%B4', '13800010078', '陈立', '儿子', '13800020078', 'Alzheimer''s', 'Late', '高风险', '2025-03-16', '来源于 CHRONIC 的阿尔茨海默病晚期病例模式，需重点关注照护支持和连续随访。', 'high'),
  ('PID0217', '张美兰', '女', 75, 'https://api.dicebear.com/9.x/initials/svg?seed=%E5%BC%A0%E7%BE%8E%E5%85%B0', '13800010217', '李芳', '女儿', '13800020217', 'Alzheimer''s', 'Mid', '中风险', '2025-03-12', '来源于 CHRONIC 的阿尔茨海默病中期病例模式，建议继续跟踪情绪与睡眠。', 'high'),
  ('PID0191', '王海峰', '男', 61, 'https://api.dicebear.com/9.x/initials/svg?seed=%E7%8E%8B%E6%B5%B7%E5%B3%B0', '13800010191', '王琳', '配偶', '13800020191', 'Diabetes', 'Mid', '中风险', '2025-03-20', '来源于 CHRONIC 的糖尿病中期病例模式，需要持续跟进血糖与血压监测。', 'high'),
  ('PID0313', '陈素梅', '女', 57, 'https://api.dicebear.com/9.x/initials/svg?seed=%E9%99%88%E7%B4%A0%E6%A2%85', '13800010313', '赵辉', '配偶', '13800020313', 'Diabetes', 'Mid', '中风险', '2025-03-08', '来源于 CHRONIC 的低样本糖尿病病例模式，适合作为小样本辅助示例。', 'low'),
  ('PID0144', '马惠春', '男', 70, 'https://api.dicebear.com/9.x/initials/svg?seed=%E9%A9%AC%E6%83%A0%E6%98%A5', '13800010144', '马强', '儿子', '13800020144', 'Parkinson''s', 'Late', '高风险', '2025-03-06', '来源于 CHRONIC 的帕金森病晚期病例模式，需要重点处理跌倒风险和用药依从性。', 'high')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  gender = VALUES(gender),
  age = VALUES(age),
  avatar_url = VALUES(avatar_url),
  phone = VALUES(phone),
  emergency_contact_name = VALUES(emergency_contact_name),
  emergency_contact_relation = VALUES(emergency_contact_relation),
  emergency_contact_phone = VALUES(emergency_contact_phone),
  primary_disease = VALUES(primary_disease),
  current_stage = VALUES(current_stage),
  risk_level = VALUES(risk_level),
  last_visit = VALUES(last_visit),
  summary = VALUES(summary),
  data_support = VALUES(data_support);

UPDATE patients
SET
  identity_masked = CASE patient_id
    WHEN 'PID0025' THEN '3203********1025'
    WHEN 'PID0078' THEN '3203********1078'
    WHEN 'PID0217' THEN '3203********1217'
    WHEN 'PID0191' THEN '3203********1191'
    WHEN 'PID0313' THEN '3203********1313'
    WHEN 'PID0144' THEN '3203********1144'
    ELSE identity_masked
  END,
  insurance_type = '城镇职工',
  department = '慢病管理门诊',
  primary_doctor = '周医生',
  case_manager = '张护士',
  allergy_history = CASE patient_id
    WHEN 'PID0191' THEN '青霉素过敏'
    ELSE '无'
  END,
  family_history = CASE patient_id
    WHEN 'PID0191' THEN '父亲有卒中病史'
    WHEN 'PID0313' THEN '母亲有糖尿病病史'
    ELSE '无特殊家族史'
  END
WHERE patient_id IN ('PID0025', 'PID0078', 'PID0217', 'PID0191', 'PID0313', 'PID0144');

UPDATE doctor_users
SET role = CASE username
  WHEN 'demo_clinic' THEN 'doctor'
  WHEN 'demo_specialist' THEN 'nurse'
  ELSE role
END
WHERE username IN ('demo_clinic', 'demo_specialist');

UPDATE patients
SET
  medical_record_number = CASE patient_id
    WHEN 'PID0025' THEN 'MRN0025'
    WHEN 'PID0078' THEN 'MRN0078'
    WHEN 'PID0217' THEN 'MRN0217'
    WHEN 'PID0191' THEN 'MRN0191'
    WHEN 'PID0313' THEN 'MRN0313'
    WHEN 'PID0144' THEN 'MRN0144'
    ELSE medical_record_number
  END,
  archive_source = CASE patient_id
    WHEN 'PID0078' THEN 'discharge_followup'
    WHEN 'PID0217' THEN 'community_referral'
    ELSE 'outpatient'
  END,
  archive_status = 'active',
  consent_status = CASE patient_id
    WHEN 'PID0078' THEN 'family_authorized'
    ELSE 'signed'
  END
WHERE patient_id IN ('PID0025', 'PID0078', 'PID0217', 'PID0191', 'PID0313', 'PID0144');

INSERT INTO patient_events (patient_id, event_time, relation, object_value, note, source) VALUES
  ('PID0025', '2024-12-12 09:00:00', 'has_disease', 'Parkinson''s', '门诊首次建档，明确帕金森病诊断。', 'seed'),
  ('PID0025', '2025-01-18 10:20:00', 'stage', 'Mid', '症状评估提示疾病进入中期阶段。', 'seed'),
  ('PID0025', '2025-02-09 08:30:00', 'med_adherence', 'High', '近一月依从性较好。', 'seed'),
  ('PID0025', '2025-02-26 15:00:00', 'support_system', 'Moderate', '家属可陪同复诊，但日常照护仍有缺口。', 'seed'),
  ('PID0025', '2025-03-18 09:10:00', 'medical_history', 'Heart_Disease', '既往合并心脏病史。', 'seed'),

  ('PID0078', '2024-11-05 14:00:00', 'has_disease', 'Alzheimer''s', '记忆门诊复评，诊断明确。', 'seed'),
  ('PID0078', '2025-01-08 09:15:00', 'stage', 'Late', '认知评估提示疾病进入晚期。', 'seed'),
  ('PID0078', '2025-02-02 11:40:00', 'support_system', 'Strong', '家属轮班陪护，照护支持较强。', 'seed'),
  ('PID0078', '2025-02-20 08:00:00', 'med_adherence', 'Low', '近期服药记录不完整。', 'seed'),
  ('PID0078', '2025-03-16 10:10:00', 'sleep_hours_bin', 'Q1', '夜间睡眠不足，需要干预。', 'seed'),

  ('PID0217', '2024-12-18 10:00:00', 'has_disease', 'Alzheimer''s', '神经内科随访确认病程延续。', 'seed'),
  ('PID0217', '2025-01-26 09:30:00', 'stage', 'Mid', '综合量表评估为中期。', 'seed'),
  ('PID0217', '2025-02-17 13:40:00', 'support_system', 'Strong', '家庭照护支持充足。', 'seed'),
  ('PID0217', '2025-02-28 08:20:00', 'med_adherence', 'Low', '存在漏服现象。', 'seed'),
  ('PID0217', '2025-03-12 09:00:00', 'medical_history', 'Asthma', '既往合并哮喘病史。', 'seed'),

  ('PID0191', '2024-12-10 08:40:00', 'has_disease', 'Diabetes', '确认为 2 型糖尿病持续管理对象。', 'seed'),
  ('PID0191', '2025-01-14 09:10:00', 'stage', 'Mid', '综合评估为中期慢病管理阶段。', 'seed'),
  ('PID0191', '2025-02-11 08:20:00', 'med_adherence', 'Medium', '依从性一般。', 'seed'),
  ('PID0191', '2025-03-03 14:30:00', 'bp_sys_bin', 'Q3', '收缩压分层偏高。', 'seed'),
  ('PID0191', '2025-03-20 09:15:00', 'medical_history', 'Stroke', '既往卒中史。', 'seed'),

  ('PID0313', '2025-01-06 10:00:00', 'has_disease', 'Diabetes', '首次录入门诊慢病台账。', 'seed'),
  ('PID0313', '2025-02-01 09:50:00', 'stage', 'Mid', '当前阶段评估为中期。', 'seed'),
  ('PID0313', '2025-03-08 08:40:00', 'support_system', 'Weak', '家庭支持较弱，建议加强随访。', 'seed'),

  ('PID0144', '2024-10-28 08:10:00', 'has_disease', 'Parkinson''s', '专病门诊确诊并纳入随访。', 'seed'),
  ('PID0144', '2025-01-12 09:30:00', 'stage', 'Late', '病程进展至晚期。', 'seed'),
  ('PID0144', '2025-02-05 14:20:00', 'support_system', 'Strong', '家属陪护稳定。', 'seed'),
  ('PID0144', '2025-02-22 08:15:00', 'med_adherence', 'High', '依从性良好。', 'seed'),
  ('PID0144', '2025-03-06 11:00:00', 'medical_history', 'Heart_Disease', '合并心脏病史。', 'seed');

INSERT INTO patient_contact_logs (
  log_id, patient_id, contact_time, contact_type, contact_target, contact_result, operator_username, operator_name, note, next_contact_date
) VALUES
  ('clog-0025-01', 'PID0025', '2025-03-19 10:00:00', 'phone', 'patient', 'reached', 'demo_clinic', '系统演示账号', '电话随访已接通，患者反馈步态波动较前一周略有增加，已提醒按时复诊。', '2025-03-26'),
  ('clog-0078-01', 'PID0078', '2025-03-17 15:20:00', 'family', 'emergency_contact', 'scheduled', 'demo_specialist', '专科演示账号', '与家属沟通后确认本周内陪同复诊，并补充夜间照护观察记录。', '2025-03-24'),
  ('clog-0191-01', 'PID0191', '2025-03-21 09:10:00', 'phone', 'patient', 'reached', 'demo_clinic', '系统演示账号', '电话回访已接通，提醒继续监测血糖和血压，并准备下次门诊检查结果。', '2025-03-28')
ON DUPLICATE KEY UPDATE
  note = VALUES(note),
  next_contact_date = VALUES(next_contact_date),
  operator_username = VALUES(operator_username),
  operator_name = VALUES(operator_name);

INSERT INTO patient_audit_logs (
  log_id, patient_id, action, operator_username, operator_name, detail, created_at
) VALUES
  ('alog-0025-01', 'PID0025', 'archive_created', 'demo_clinic', 'ç»¯è¤ç²ºå©•æ—‚ãšç’ï¹€å½¿', 'Archive created for chronic disease management intake.', '2025-03-18 08:30:00'),
  ('alog-0078-01', 'PID0078', 'archive_created', 'demo_specialist', 'æ¶“æ’¶î–å©•æ—‚ãšç’ï¹€å½¿', 'Archive created from discharge follow-up referral.', '2025-03-16 09:00:00'),
  ('alog-0191-01', 'PID0191', 'event_added', 'demo_clinic', 'ç»¯è¤ç²ºå©•æ—‚ãšç’ï¹€å½¿', 'Structured event added: bp_sys_bin -> Q3', '2025-03-20 09:20:00')
ON DUPLICATE KEY UPDATE
  action = VALUES(action),
  operator_username = VALUES(operator_username),
  operator_name = VALUES(operator_name),
  detail = VALUES(detail),
  created_at = VALUES(created_at);
