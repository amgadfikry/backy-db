-- Drop if exists for clean re-run
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

-- =========================================
-- 1. Departments table (no FK)
-- =========================================
CREATE TABLE departments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE INDEX idx_department_name ON departments(name);

-- =========================================
-- 2. Employees table (FK -> departments)
-- =========================================
CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    department_id INT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE INDEX idx_employee_department_id ON employees(department_id);

-- =========================================
-- 3. Projects table (FK -> employees)
-- =========================================
CREATE TABLE projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    employee_id INT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE INDEX idx_project_employee_id ON projects(employee_id);

-- =========================================
-- Insert data into departments
-- =========================================
INSERT INTO departments (name) VALUES
('Engineering'),
('HR'),
('Marketing');

-- =========================================
-- Insert data into employees
-- =========================================
INSERT INTO employees (name, department_id) VALUES
('Alice', 1),
('Bob', 1),
('Charlie', 2);

-- =========================================
-- Insert data into projects
-- =========================================
INSERT INTO projects (title, employee_id) VALUES
('Platform Refactor', 1),
('Recruitment Drive', 3),
('Ad Campaign Q3', 2);

-- =========================================
-- View 1: Employee with Department Info
-- =========================================
CREATE OR REPLACE VIEW view_employee_departments AS
SELECT 
    e.id AS employee_id,
    e.name AS employee_name,
    d.name AS department_name
FROM employees e
JOIN departments d ON e.department_id = d.id;

-- =========================================
-- View 2: Projects with Employee and Department Info
-- =========================================
CREATE OR REPLACE VIEW view_project_employees AS
SELECT 
    p.id AS project_id,
    p.title AS project_title,
    v.employee_id,
    v.employee_name,
    v.department_name
FROM projects p
JOIN view_employee_departments v ON p.employee_id = v.employee_id;

-- =========================================
-- View 3: Project Count per Department
-- =========================================
CREATE OR REPLACE VIEW view_department_project_counts AS
SELECT 
    department_name,
    COUNT(project_id) AS total_projects
FROM view_project_employees
GROUP BY department_name;


-- ============================================
-- Dummy Function 1: Return fake department name
-- ============================================
DELIMITER //
CREATE FUNCTION dummy_get_department_name(emp_id INT)
RETURNS VARCHAR(100)
DETERMINISTIC
BEGIN
    RETURN CONCAT('DummyDept_', emp_id);
END;
//
DELIMITER ;

-- ============================================
-- Dummy Function 2: Return fake project info using #1
-- ============================================
DELIMITER //
CREATE FUNCTION dummy_get_project_info(project_id INT)
RETURNS VARCHAR(255)
DETERMINISTIC
BEGIN
    DECLARE emp_id INT DEFAULT project_id + 100; -- dummy logic
    DECLARE dept_name VARCHAR(100);
    
    SET dept_name = dummy_get_department_name(emp_id);

    RETURN CONCAT('Project_', project_id, ' handled by Emp_', emp_id, ' in ', dept_name);
END;
//
DELIMITER ;

-- ============================================
-- Dummy Function 3: Summarize 3 fake projects using #2
-- ============================================
DELIMITER //
CREATE FUNCTION dummy_department_project_summary(dept VARCHAR(50))
RETURNS VARCHAR(255)
DETERMINISTIC
BEGIN
    DECLARE summary TEXT DEFAULT '';
    DECLARE i INT DEFAULT 1;

    WHILE i <= 3 DO
        SET summary = CONCAT_WS(' | ', summary, dummy_get_project_info(i));
        SET i = i + 1;
    END WHILE;

    RETURN CONCAT('Summary for ', dept, ': ', summary);
END;//
DELIMITER ;

-- ============================================
-- Dummy Procedure: Print department project summary
-- ============================================
DELIMITER $$
CREATE PROCEDURE department_summary()
BEGIN
    SELECT * FROM departments;
END;
$$
DELIMITER ;

-- ============================================
-- Dummy procedure 2: Print project info for a specific employee
-- ============================================
DELIMITER $$
CREATE PROCEDURE employee_project_info(IN emp_id INT)
BEGIN
    SELECT 
        p.id AS project_id,
        p.title AS project_title,
        d.name AS department_name
    FROM projects p
    JOIN employees e ON p.employee_id = e.id
    JOIN departments d ON e.department_id = d.id
    WHERE e.id = emp_id;
END;
$$
DELIMITER ;

-- ============================================
-- Dummy Trigger: Log project creation (no actual logging, just a placeholder)
-- ============================================
DELIMITER //
CREATE TRIGGER after_project_insert
AFTER INSERT ON projects
FOR EACH ROW
BEGIN
    DECLARE dummy_message VARCHAR(255);
    SET dummy_message = CONCAT('Project ', NEW.id, ' created with title: ', NEW.title);
END;
//
DELIMITER ;

-- ============================================
-- Dummy Trigger 2: Log employee creation (no actual logging, just a placeholder)
-- ============================================
DELIMITER //
CREATE TRIGGER after_employee_insert
AFTER INSERT ON employees
FOR EACH ROW
BEGIN
    DECLARE dummy_message VARCHAR(255);
    SET dummy_message = CONCAT('Employee ', NEW.id, ' created with name: ', NEW.name);
END;
//
DELIMITER ;


-- ============================================
-- Dummy Event: Placeholder for a scheduled task (no actual task)
-- ============================================
DELIMITER $$
CREATE EVENT dummy_event_1
ON SCHEDULE EVERY 1 DAY
ENABLE
DO
BEGIN
    -- Placeholder for scheduled task logic
    SELECT 'Dummy event executed' AS message;
END;
$$
DELIMITER ;
-- ============================================
-- dummy event 2: Placeholder for another scheduled task (no actual task)
-- ============================================
DELIMITER $$
CREATE EVENT dummy_event_2
ON SCHEDULE EVERY 1 WEEK
DISABLE
DO
BEGIN
    -- Placeholder for another scheduled task logic
    SELECT 'Dummy event 2 executed' AS message;
END;
$$
DELIMITER ;
-- ============================================
-- third dummy event: Placeholder for a third scheduled task (no actual task)
-- ============================================
DELIMITER $$
CREATE EVENT dummy_event_3
ON SCHEDULE EVERY 1 MONTH
DO
BEGIN
    -- Placeholder for a third scheduled task logic
    SELECT 'Dummy event 3 executed' AS message;
END;
$$
DELIMITER ;

-- ============================================
-- End of MySQL Seed Script
-- ============================================
