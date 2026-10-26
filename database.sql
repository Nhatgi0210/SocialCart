-- Face Attendance System — MySQL Schema

CREATE DATABASE IF NOT EXISTS face_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE face_attendance;

-- Bảng phòng ban
CREATE TABLE departments (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    parent_id   BIGINT NULL,  -- phân cấp phòng ban (NULL = cấp gốc)
    manager_id  BIGINT NULL,  -- sẽ update sau khi có nhân viên
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Bảng ca làm việc
CREATE TABLE shifts (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    name                    VARCHAR(100) NOT NULL,
    check_in_time           TIME NOT NULL,
    check_out_time          TIME NOT NULL,
    late_tolerance_minutes  INT DEFAULT 15,  -- trễ bao nhiêu phút thì tính muộn
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Bảng nhân viên
CREATE TABLE employees (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    employee_code   VARCHAR(20) UNIQUE NOT NULL,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) UNIQUE,
    phone           VARCHAR(20),
    avatar_path     VARCHAR(500),
    department_id   BIGINT,
    shift_id        BIGINT,
    face_enrolled   BOOLEAN DEFAULT FALSE,
    active          BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE SET NULL
);

-- Cập nhật manager_id sau khi có nhân viên
ALTER TABLE departments ADD FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL;

-- Bảng lịch sử chấm công
CREATE TABLE attendance_logs (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    employee_id         BIGINT NOT NULL,
    check_type          ENUM('IN', 'OUT') NOT NULL,
    check_time          DATETIME NOT NULL,
    confidence_score    FLOAT,           -- độ chắc chắn nhận diện (0.0 - 1.0)
    snapshot_path       VARCHAR(500),    -- đường dẫn ảnh chụp lúc chấm công
    status              ENUM('ON_TIME', 'LATE', 'EARLY_LEAVE', 'UNKNOWN') DEFAULT 'UNKNOWN',
    note                VARCHAR(255),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Index để query nhanh theo ngày
CREATE INDEX idx_attendance_employee_date ON attendance_logs(employee_id, check_time);
CREATE INDEX idx_attendance_date ON attendance_logs(check_time);

-- Bảng tài khoản admin
CREATE TABLE users (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,  -- bcrypt
    full_name   VARCHAR(150),
    role        ENUM('ADMIN', 'HR', 'VIEWER') DEFAULT 'VIEWER',
    active      BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Dữ liệu mẫu ban đầu

-- Ca làm việc mặc định
INSERT INTO shifts (name, check_in_time, check_out_time, late_tolerance_minutes) VALUES
('Ca hành chính', '08:00:00', '17:00:00', 15),
('Ca sáng', '06:00:00', '14:00:00', 10),
('Ca chiều', '14:00:00', '22:00:00', 10);

-- Phòng ban mẫu
INSERT INTO departments (name, description, parent_id) VALUES
('Ban Giám Đốc', 'Lãnh đạo công ty', NULL),
('Phòng Kỹ Thuật', 'Phát triển phần mềm và hạ tầng', NULL),
('Phòng Nhân Sự', 'Quản lý nhân sự và tuyển dụng', NULL),
('Phòng Kinh Doanh', 'Kinh doanh và marketing', NULL),
('Team Frontend', 'Phát triển giao diện', 2),
('Team Backend', 'Phát triển hệ thống', 2);

-- Tài khoản admin mặc định (password: Admin@123)
-- BCrypt hash của "Admin@123" (rounds=10)
INSERT INTO users (username, password, full_name, role) VALUES
('admin', '$2b$10$oAy/bzu.WEFAwYiZhQthdu7ggKIzDrOb.M50/V3pHSQmDeHLBMfmO', 'System Admin', 'ADMIN');
