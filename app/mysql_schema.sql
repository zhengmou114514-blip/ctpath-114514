CREATE TABLE IF NOT EXISTS doctor_users (
  username VARCHAR(64) PRIMARY KEY,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(64) NOT NULL,
  title VARCHAR(64) NOT NULL,
  department VARCHAR(128) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
  patient_id VARCHAR(32) PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  gender VARCHAR(16) NOT NULL,
  age INT NOT NULL,
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

INSERT INTO doctor_users (username, password_hash, name, title, department)
VALUES
  ('doctor01', 'ctpath123', '郑昌号', '住院医师', '内分泌与慢病管理中心'),
  ('endocrine', 'diabetes123', '林怡雯', '主治医师', '糖尿病专病门诊')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  title = VALUES(title),
  department = VALUES(department);
