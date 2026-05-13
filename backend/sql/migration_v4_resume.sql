-- v4 增量迁移：简历 Persona 注入功能（W3.2.8 / FT2.1.3.2）
-- 用途：已有 v1/v2/v3 数据库的同学执行此脚本升级，无需清库
-- 适用：拉取本分支后各自跑一次
--
-- 新增列：interviews.resume_persona TEXT NULL
-- 内容：候选人简历的结构化 JSON（skills/projects/work_years/education/summary）
-- 由 /resume/parse 端点解析，start_interview 时一并落库
--
-- MySQL 8.0 的 ADD COLUMN 不支持 IF NOT EXISTS，这里用 procedure 判断后再加

USE interview_echo;

DROP PROCEDURE IF EXISTS interview_echo_v4_add_columns;

DELIMITER $$
CREATE PROCEDURE interview_echo_v4_add_columns()
BEGIN
    -- resume_persona
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'interviews'
          AND COLUMN_NAME = 'resume_persona'
    ) THEN
        ALTER TABLE interviews ADD COLUMN resume_persona TEXT NULL;
    END IF;
END$$
DELIMITER ;

CALL interview_echo_v4_add_columns();
DROP PROCEDURE interview_echo_v4_add_columns;

-- 回滚（如需）：
--   ALTER TABLE interviews DROP COLUMN resume_persona;
