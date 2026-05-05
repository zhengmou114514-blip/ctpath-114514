CREATE TABLE IF NOT EXISTS doctor_users (
  username VARCHAR(64) PRIMARY KEY,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(64) NOT NULL,
  title VARCHAR(64) NOT NULL,
  department VARCHAR(128) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'doctor',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
  role_key VARCHAR(32) PRIMARY KEY,
  role_name VARCHAR(64) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
  patient_id VARCHAR(32) PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  gender VARCHAR(16) NOT NULL,
  age INT NOT NULL,
  avatar_url VARCHAR(512) DEFAULT '',
  phone VARCHAR(32) DEFAULT '',
  emergency_contact_name VARCHAR(64) DEFAULT '',
  emergency_contact_relation VARCHAR(32) DEFAULT '',
  emergency_contact_phone VARCHAR(32) DEFAULT '',
  identity_masked VARCHAR(32) DEFAULT '',
  insurance_type VARCHAR(64) DEFAULT '',
  department VARCHAR(128) DEFAULT '',
  primary_doctor VARCHAR(64) DEFAULT '',
  case_manager VARCHAR(64) DEFAULT '',
  medical_record_number VARCHAR(64) DEFAULT '',
  archive_source VARCHAR(32) DEFAULT 'outpatient',
  archive_status VARCHAR(32) DEFAULT 'active',
  consent_status VARCHAR(32) DEFAULT 'signed',
  allergy_history TEXT,
  family_history TEXT,
  primary_disease VARCHAR(128) NOT NULL,
  current_stage VARCHAR(32) NOT NULL,
  risk_level VARCHAR(32) NOT NULL,
  last_visit DATE NOT NULL,
  summary TEXT,
  data_support VARCHAR(16) NOT NULL DEFAULT 'medium',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patient_events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id VARCHAR(32) NOT NULL,
  event_time DATETIME NOT NULL,
  relation VARCHAR(64) NOT NULL,
  object_value VARCHAR(128) NOT NULL,
  note TEXT,
  source VARCHAR(64) DEFAULT 'ehr',
  confidence DECIMAL(6,4) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_patient_events_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE INDEX idx_patient_events_patient_time ON patient_events(patient_id, event_time);
CREATE INDEX idx_patient_events_relation ON patient_events(relation);

CREATE TABLE IF NOT EXISTS patient_encounter_state (
  patient_id VARCHAR(32) PRIMARY KEY,
  encounter_status VARCHAR(32) NOT NULL DEFAULT 'waiting',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_patient_encounter_state_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS outpatient_tasks (
  task_id VARCHAR(32) PRIMARY KEY,
  patient_id VARCHAR(32) NOT NULL,
  category VARCHAR(16) NOT NULL,
  title VARCHAR(128) NOT NULL,
  owner VARCHAR(64) NOT NULL,
  due_date DATE NOT NULL,
  priority VARCHAR(16) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT '待执行',
  note TEXT,
  source VARCHAR(64) DEFAULT 'manual',
  updated_by VARCHAR(128) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_outpatient_tasks_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE INDEX idx_outpatient_tasks_patient_due ON outpatient_tasks(patient_id, due_date);

CREATE TABLE IF NOT EXISTS outpatient_task_logs (
  log_id VARCHAR(32) PRIMARY KEY,
  task_id VARCHAR(32) NOT NULL,
  patient_id VARCHAR(32) NOT NULL,
  action VARCHAR(32) NOT NULL,
  actor_username VARCHAR(64) DEFAULT NULL,
  actor_name VARCHAR(64) DEFAULT NULL,
  note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_outpatient_task_logs_task
    FOREIGN KEY (task_id) REFERENCES outpatient_tasks(task_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_outpatient_task_logs_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE INDEX idx_outpatient_task_logs_task_time ON outpatient_task_logs(task_id, created_at);

CREATE TABLE IF NOT EXISTS patient_contact_logs (
  log_id VARCHAR(32) PRIMARY KEY,
  patient_id VARCHAR(32) NOT NULL,
  contact_time DATETIME NOT NULL,
  contact_type VARCHAR(16) NOT NULL,
  contact_target VARCHAR(32) NOT NULL DEFAULT 'patient',
  contact_result VARCHAR(16) NOT NULL,
  operator_username VARCHAR(64) DEFAULT NULL,
  operator_name VARCHAR(64) DEFAULT NULL,
  note TEXT,
  next_contact_date DATE DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_patient_contact_logs_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE INDEX idx_patient_contact_logs_patient_time ON patient_contact_logs(patient_id, contact_time DESC);

CREATE TABLE IF NOT EXISTS patient_audit_logs (
  log_id VARCHAR(32) PRIMARY KEY,
  patient_id VARCHAR(32) NOT NULL,
  action VARCHAR(32) NOT NULL,
  operator_username VARCHAR(64) DEFAULT NULL,
  operator_name VARCHAR(64) DEFAULT NULL,
  detail TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_patient_audit_logs_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE INDEX idx_patient_audit_logs_patient_time ON patient_audit_logs(patient_id, created_at DESC);

CREATE TABLE IF NOT EXISTS patient_attachments (
  attachment_id VARCHAR(40) PRIMARY KEY,
  patient_id VARCHAR(32) NOT NULL,
  attachment_type VARCHAR(32) NOT NULL,
  type_label VARCHAR(64) NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  mime_type VARCHAR(128) NOT NULL,
  file_size BIGINT NOT NULL,
  storage_file_name VARCHAR(255) NOT NULL,
  preview_url VARCHAR(512) NOT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  uploaded_by VARCHAR(64) NOT NULL,
  source VARCHAR(32) NOT NULL DEFAULT 'local-file',
  CONSTRAINT fk_patient_attachments_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE INDEX idx_patient_attachments_patient_time ON patient_attachments(patient_id, uploaded_at DESC);

CREATE TABLE IF NOT EXISTS drug_catalog (
  drug_id VARCHAR(64) PRIMARY KEY,
  generic_name VARCHAR(128) NOT NULL,
  brand_name VARCHAR(128) DEFAULT '',
  dosage_form VARCHAR(64) NOT NULL,
  specification VARCHAR(128) NOT NULL,
  unit VARCHAR(32) NOT NULL,
  is_prescription TINYINT(1) NOT NULL DEFAULT 1,
  is_controlled TINYINT(1) NOT NULL DEFAULT 0,
  status VARCHAR(16) NOT NULL DEFAULT 'active',
  indication TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  updated_by VARCHAR(64) DEFAULT ''
);

CREATE TABLE IF NOT EXISTS drug_permissions (
  role VARCHAR(32) PRIMARY KEY,
  allow_view TINYINT(1) NOT NULL DEFAULT 0,
  allow_prescribe TINYINT(1) NOT NULL DEFAULT 0,
  allow_review TINYINT(1) NOT NULL DEFAULT 0,
  allow_execute TINYINT(1) NOT NULL DEFAULT 0,
  allow_controlled_drug TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS patient_medications (
  medication_id VARCHAR(64) PRIMARY KEY,
  patient_id VARCHAR(32) NOT NULL,
  drug_id VARCHAR(64) NOT NULL,
  drug_name_snapshot VARCHAR(255) NOT NULL,
  dosage VARCHAR(64) NOT NULL,
  frequency VARCHAR(64) NOT NULL,
  route VARCHAR(64) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'active',
  prescribed_by VARCHAR(64) NOT NULL,
  review_status VARCHAR(16) NOT NULL DEFAULT 'pending',
  note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_patient_medications_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_patient_medications_drug
    FOREIGN KEY (drug_id) REFERENCES drug_catalog(drug_id)
    ON DELETE RESTRICT
);

CREATE INDEX idx_patient_medications_patient_status ON patient_medications(patient_id, status, start_date DESC);

CREATE TABLE IF NOT EXISTS prediction_results (
  result_id VARCHAR(40) PRIMARY KEY,
  patient_id VARCHAR(32) NOT NULL,
  mode VARCHAR(32) NOT NULL,
  strategy VARCHAR(32) NOT NULL,
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  support_summary TEXT NOT NULL,
  event_count INT NOT NULL DEFAULT 0,
  timepoint_count INT NOT NULL DEFAULT 0,
  relation_count INT NOT NULL DEFAULT 0,
  support_level VARCHAR(16) NOT NULL,
  proxy_patient_id VARCHAR(32) DEFAULT NULL,
  topk_json JSON NOT NULL,
  advice_json JSON NOT NULL,
  path_explanation_json JSON NOT NULL,
  similar_cases_json JSON NOT NULL,
  source VARCHAR(32) NOT NULL DEFAULT 'model-service',
  CONSTRAINT fk_prediction_results_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE CASCADE
);

CREATE INDEX idx_prediction_results_patient_time ON prediction_results(patient_id, generated_at DESC);

CREATE TABLE IF NOT EXISTS governance_records (
  record_id VARCHAR(40) PRIMARY KEY,
  patient_id VARCHAR(32) DEFAULT NULL,
  category VARCHAR(32) NOT NULL,
  severity VARCHAR(16) NOT NULL DEFAULT 'normal',
  title VARCHAR(128) NOT NULL,
  detail TEXT NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'open',
  created_by VARCHAR(64) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resolved_at TIMESTAMP NULL DEFAULT NULL,
  CONSTRAINT fk_governance_records_patient
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    ON DELETE SET NULL
);

CREATE INDEX idx_governance_records_status_time ON governance_records(status, created_at DESC);

CREATE TABLE IF NOT EXISTS system_audit_logs (
  log_id VARCHAR(40) PRIMARY KEY,
  action VARCHAR(64) NOT NULL,
  result VARCHAR(32) NOT NULL,
  role VARCHAR(32) DEFAULT NULL,
  username VARCHAR(64) DEFAULT NULL,
  path VARCHAR(255) NOT NULL,
  method VARCHAR(16) NOT NULL,
  detail TEXT,
  client_ip VARCHAR(64) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_audit_logs_time ON system_audit_logs(created_at DESC);

INSERT INTO roles (role_key, role_name, description)
VALUES
  ('doctor', '医生', '负责患者诊疗、病程查看与辅助决策。'),
  ('nurse', '护士', '负责随访任务、联系记录与护理协同。'),
  ('pharmacist', '药师', '负责药品目录、审核与药品权限管理。'),
  ('archivist', '档案员', '负责患者档案、附件与数据质量治理。'),
  ('admin', '管理员', '负责系统治理、权限与全局管理。')
ON DUPLICATE KEY UPDATE
  role_name = VALUES(role_name),
  description = VALUES(description);

INSERT INTO doctor_users (username, password_hash, name, title, department)
VALUES
  ('demo_clinic', 'demo123456', '林医生', '门诊医生', '慢病管理门诊'),
  ('demo_nurse', 'demo123456', '陈护士', '主管护士', '慢病管理门诊'),
  ('demo_pharmacist', 'demo123456', '周药师', '主管药师', '药房药库'),
  ('demo_archivist', 'demo123456', '王档案员', '档案管理员', '病案室'),
  ('demo_admin', 'demo123456', '系统管理员', '系统管理员', '系统管理中心'),
  ('demo_specialist', 'demo123456', '赵医生', '专科医生', '神经内科门诊')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  title = VALUES(title),
  department = VALUES(department);

UPDATE doctor_users
SET password_hash = CASE username
  WHEN 'demo_clinic' THEN 'pbkdf2_sha256$390000$79badd95d6c2d22c6a978f80adbb9644$d3787805ccd62eef54f7df56981df0b4e1c98dab122af4b0589d8b99cb4bfbda'
  WHEN 'demo_nurse' THEN 'pbkdf2_sha256$390000$79badd95d6c2d22c6a978f80adbb9644$d3787805ccd62eef54f7df56981df0b4e1c98dab122af4b0589d8b99cb4bfbda'
  WHEN 'demo_pharmacist' THEN 'pbkdf2_sha256$390000$79badd95d6c2d22c6a978f80adbb9644$d3787805ccd62eef54f7df56981df0b4e1c98dab122af4b0589d8b99cb4bfbda'
  WHEN 'demo_archivist' THEN 'pbkdf2_sha256$390000$79badd95d6c2d22c6a978f80adbb9644$d3787805ccd62eef54f7df56981df0b4e1c98dab122af4b0589d8b99cb4bfbda'
  WHEN 'demo_admin' THEN 'pbkdf2_sha256$390000$79badd95d6c2d22c6a978f80adbb9644$d3787805ccd62eef54f7df56981df0b4e1c98dab122af4b0589d8b99cb4bfbda'
  WHEN 'demo_specialist' THEN 'pbkdf2_sha256$390000$d654ffecd63ef9b8dd3fae4420da4661$dc689c746b57c7c69f5d71509df96f1eb5dca62c2d3b1fd64fef6673bf301a3f'
  ELSE password_hash
END
WHERE username IN ('demo_clinic', 'demo_nurse', 'demo_pharmacist', 'demo_archivist', 'demo_admin', 'demo_specialist');

UPDATE doctor_users
SET role = CASE username
  WHEN 'demo_clinic' THEN 'doctor'
  WHEN 'demo_nurse' THEN 'nurse'
  WHEN 'demo_pharmacist' THEN 'pharmacist'
  WHEN 'demo_archivist' THEN 'archivist'
  WHEN 'demo_admin' THEN 'admin'
  WHEN 'demo_specialist' THEN 'doctor'
  ELSE role
END
WHERE username IN ('demo_clinic', 'demo_nurse', 'demo_pharmacist', 'demo_archivist', 'demo_admin', 'demo_specialist');
