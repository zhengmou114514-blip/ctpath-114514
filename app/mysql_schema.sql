CREATE TABLE IF NOT EXISTS doctor_users (
  username VARCHAR(64) PRIMARY KEY,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(64) NOT NULL,
  title VARCHAR(64) NOT NULL,
  department VARCHAR(128) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'doctor',
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

INSERT INTO doctor_users (username, password_hash, name, title, department)
VALUES
  ('demo_clinic', 'demo123456', '系统演示账号', '门诊医生', '慢病管理门诊'),
  ('demo_specialist', 'demo123456', '专科演示账号', '专科医生', '神经内科门诊')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  title = VALUES(title),
  department = VALUES(department);

UPDATE doctor_users
SET password_hash = CASE username
  WHEN 'demo_clinic' THEN 'pbkdf2_sha256$390000$79badd95d6c2d22c6a978f80adbb9644$d3787805ccd62eef54f7df56981df0b4e1c98dab122af4b0589d8b99cb4bfbda'
  WHEN 'demo_specialist' THEN 'pbkdf2_sha256$390000$d654ffecd63ef9b8dd3fae4420da4661$dc689c746b57c7c69f5d71509df96f1eb5dca62c2d3b1fd64fef6673bf301a3f'
  ELSE password_hash
END
WHERE username IN ('demo_clinic', 'demo_specialist');

UPDATE doctor_users
SET role = CASE username
  WHEN 'demo_clinic' THEN 'doctor'
  WHEN 'demo_specialist' THEN 'nurse'
  ELSE role
END
WHERE username IN ('demo_clinic', 'demo_specialist');
