-- Drop events if they are present
DROP EVENT IF EXISTS dummy_event_1;
DROP EVENT IF EXISTS dummy_event_2;
DROP EVENT IF EXISTS dummy_event_3;

-- DROP triggers if they are present
DROP TRIGGER IF EXISTS after_project_insert;
DROP TRIGGER IF EXISTS after_employee_insert;

-- Drop procedures if they are present
DROP PROCEDURE IF EXISTS department_summary;
DROP PROCEDURE IF EXISTS employee_project_info;

-- Drop functions if they are present
DROP FUNCTION IF EXISTS dummy_get_department_name;
DROP FUNCTION IF EXISTS dummy_get_project_info;
DROP FUNCTION IF EXISTS dummy_department_project_summary;

-- Drop views if they are present
DROP VIEW IF EXISTS view_employee_departments;
DROP VIEW IF EXISTS view_project_employees;
DROP VIEW IF EXISTS view_department_project_counts;

-- Drop if exists for clean re-run
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
