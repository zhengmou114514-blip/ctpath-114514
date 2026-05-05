INSERT INTO patients (
  patient_id, name, gender, age, avatar_url, phone, emergency_contact_name, emergency_contact_relation, emergency_contact_phone,
  primary_disease, current_stage, risk_level, last_visit, summary, data_support
) VALUES
  ('PID1001', '李国强', '男', 66, 'https://api.dicebear.com/9.x/initials/svg?seed=%E6%9D%8E%E5%9B%BD%E5%BC%BA', '13800111001', '李倩', '女儿', '13800121001', 'Hypertension', 'Mid', '中风险', '2026-04-10', '高血压中期患者，近期晨间血压波动明显，需要复核家庭血压记录和用药依从性。', 'high'),
  ('PID1002', '赵秀英', '女', 69, 'https://api.dicebear.com/9.x/initials/svg?seed=%E8%B5%B5%E7%A7%80%E8%8B%B1', '13800111002', '赵明', '儿子', '13800121002', 'Diabetes', 'Late', '高风险', '2026-04-12', '糖尿病晚期患者，合并周围神经症状，需重点跟进足部护理、血糖监测和药师复核。', 'high'),
  ('PID1003', '孙建军', '男', 58, 'https://api.dicebear.com/9.x/initials/svg?seed=%E5%AD%99%E5%BB%BA%E5%86%9B', '13800111003', '孙悦', '配偶', '13800121003', 'COPD', 'Mid', '中风险', '2026-04-09', '慢阻肺中期患者，近期活动耐量下降，建议补齐肺功能检查并安排随访。', 'medium'),
  ('PID1004', '钱桂芳', '女', 73, 'https://api.dicebear.com/9.x/initials/svg?seed=%E9%92%B1%E6%A1%82%E8%8A%B3', '13800111004', '钱伟', '儿子', '13800121004', 'Alzheimer''s', 'Mid', '高风险', '2026-04-08', '阿尔茨海默病中期患者，夜间睡眠变差，需加强家属照护记录和复诊提醒。', 'high'),
  ('PID1005', '周海燕', '女', 62, 'https://api.dicebear.com/9.x/initials/svg?seed=%E5%91%A8%E6%B5%B7%E7%87%95', '13800111005', '王磊', '配偶', '13800121005', 'Diabetes', 'Mid', '中风险', '2026-04-14', '糖尿病中期患者，餐后血糖控制一般，需调整饮食记录并复核用药方案。', 'medium'),
  ('PID1006', '吴志明', '男', 71, 'https://api.dicebear.com/9.x/initials/svg?seed=%E5%90%B4%E5%BF%97%E6%98%8E', '13800111006', '吴昊', '儿子', '13800121006', 'Parkinson''s', 'Late', '高风险', '2026-04-11', '帕金森病晚期患者，近期跌倒风险升高，需要随访步态、睡眠和照护安排。', 'high'),
  ('PID1007', '郑丽华', '女', 55, 'https://api.dicebear.com/9.x/initials/svg?seed=%E9%83%91%E4%B8%BD%E5%8D%8E', '13800111007', '郑鹏', '弟弟', '13800121007', 'Hypertension', 'Early', '低风险', '2026-04-15', '高血压早期患者，门诊建档后需建立家庭血压记录和下次复诊计划。', 'medium'),
  ('PID1008', '冯树仁', '男', 76, 'https://api.dicebear.com/9.x/initials/svg?seed=%E5%86%AF%E6%A0%91%E4%BB%81', '13800111008', '冯琳', '女儿', '13800121008', 'Coronary Heart Disease', 'Mid', '高风险', '2026-04-07', '冠心病中期患者，合并血脂异常，需关注胸闷记录、用药依从性和复查结果。', 'high'),
  ('PID1009', '陈雪梅', '女', 60, 'https://api.dicebear.com/9.x/initials/svg?seed=%E9%99%88%E9%9B%AA%E6%A2%85', '13800111009', '陈涛', '儿子', '13800121009', 'Diabetes', 'Early', '低风险', '2026-04-13', '糖尿病早期患者，资料较完整，需继续跟进血糖记录和生活方式干预。', 'medium'),
  ('PID1010', '蒋文斌', '男', 68, 'https://api.dicebear.com/9.x/initials/svg?seed=%E8%92%8B%E6%96%87%E6%96%8C', '13800111010', '蒋婷', '女儿', '13800121010', 'Stroke Follow-up', 'Mid', '高风险', '2026-04-06', '卒中后随访患者，近期肢体康复进展缓慢，需要康复计划和血压控制联合跟进。', 'high')
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
  identity_masked = CONCAT('5001********', RIGHT(patient_id, 4)),
  insurance_type = '城镇职工医保',
  department = '慢病管理门诊',
  primary_doctor = '林医生',
  case_manager = '陈护士',
  archive_source = 'outpatient',
  archive_status = 'active',
  consent_status = 'signed',
  allergy_history = CASE patient_id WHEN 'PID1002' THEN '磺胺类药物过敏' ELSE '无' END,
  family_history = CASE
    WHEN patient_id IN ('PID1001', 'PID1007') THEN '父亲有高血压病史'
    WHEN patient_id IN ('PID1002', 'PID1005', 'PID1009') THEN '母亲有糖尿病病史'
    ELSE '无特殊家族史'
  END
WHERE patient_id BETWEEN 'PID1001' AND 'PID1010';

INSERT INTO patient_events (patient_id, event_time, relation, object_value, note, source) VALUES
  ('PID1001', '2026-03-10 09:00:00', 'has_disease', 'Hypertension', '门诊建档，明确高血压持续管理。', 'ehr'),
  ('PID1001', '2026-04-10 09:15:00', 'bp_sys_bin', 'Q3', '晨间收缩压偏高。', 'ehr'),
  ('PID1002', '2026-03-12 10:00:00', 'has_disease', 'Diabetes', '纳入糖尿病专病随访。', 'ehr'),
  ('PID1002', '2026-04-12 10:20:00', 'med_adherence', 'Medium', '近期用药记录不完整。', 'ehr'),
  ('PID1003', '2026-03-09 08:40:00', 'has_disease', 'COPD', '慢阻肺门诊复核。', 'ehr'),
  ('PID1003', '2026-04-09 08:55:00', 'support_system', 'Moderate', '家属可陪同复诊。', 'ehr'),
  ('PID1004', '2026-03-08 11:00:00', 'has_disease', 'Alzheimer''s', '记忆门诊复诊。', 'ehr'),
  ('PID1004', '2026-04-08 11:10:00', 'sleep_hours_bin', 'Q1', '夜间睡眠不足。', 'ehr'),
  ('PID1005', '2026-03-14 09:30:00', 'has_disease', 'Diabetes', '糖尿病中期管理对象。', 'ehr'),
  ('PID1005', '2026-04-14 09:50:00', 'med_adherence', 'High', '按医嘱规律服药。', 'ehr'),
  ('PID1006', '2026-03-11 15:00:00', 'has_disease', 'Parkinson''s', '专病门诊复核。', 'ehr'),
  ('PID1006', '2026-04-11 15:30:00', 'medical_history', 'Fall_Risk', '近期跌倒风险升高。', 'ehr'),
  ('PID1007', '2026-04-15 10:00:00', 'has_disease', 'Hypertension', '早期高血压建档。', 'ehr'),
  ('PID1008', '2026-04-07 08:30:00', 'has_disease', 'Coronary Heart Disease', '冠心病随访复核。', 'ehr'),
  ('PID1009', '2026-04-13 09:20:00', 'has_disease', 'Diabetes', '早期糖尿病建档。', 'ehr'),
  ('PID1010', '2026-04-06 14:20:00', 'has_disease', 'Stroke Follow-up', '卒中后随访建档。', 'ehr');

INSERT INTO outpatient_tasks (task_id, patient_id, category, title, owner, due_date, priority, status, note)
VALUES
  ('task-PID1001-bp', 'PID1001', 'recheck', '复核家庭血压记录', '陈护士', '2026-05-04', 'high', '待执行', '确认晨间血压和服药时间。'),
  ('task-PID1002-foot', 'PID1002', 'recheck', '糖尿病足风险随访', '陈护士', '2026-05-04', 'high', '待执行', '询问足部感觉和皮肤破损情况。'),
  ('task-PID1004-care', 'PID1004', 'recheck', '家属照护记录核对', '陈护士', '2026-05-04', 'medium', '待执行', '补充夜间睡眠和照护安排。'),
  ('task-PID1006-fall', 'PID1006', 'recheck', '跌倒风险复查', '陈护士', '2026-05-04', 'high', '待执行', '复核步态、睡眠和居家环境。'),
  ('task-PID1010-rehab', 'PID1010', 'recheck', '康复计划跟进', '陈护士', '2026-05-04', 'medium', '待执行', '确认康复训练频率和血压记录。')
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  owner = VALUES(owner),
  due_date = VALUES(due_date),
  priority = VALUES(priority),
  status = VALUES(status),
  note = VALUES(note);
