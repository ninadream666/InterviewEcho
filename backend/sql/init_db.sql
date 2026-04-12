-- Initialize Database for InterviewEcho MVP

CREATE DATABASE IF NOT EXISTS interview_echo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE interview_echo;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions table (Roles: Java, Web, Python. Types: Knowledge, Scenario, Behavior)
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    reference_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'in_progress', -- 'in_progress', 'completed'
    difficulty VARCHAR(20),
    knowledge_points TEXT,
    total_rounds INT DEFAULT 5,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Messages table (Sender: 'user', 'ai')
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL,
    sender VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NULL,
    audio_path VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL UNIQUE,
    content_score FLOAT DEFAULT 0.0,
    expression_score FLOAT DEFAULT 0.0,
    business_scenario_score FLOAT DEFAULT 0.0,
    problem_solving_score FLOAT DEFAULT 0.0,
    total_score FLOAT DEFAULT 0.0,
    report_json TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
);

-- Insert dummy questions for testing
INSERT IGNORE INTO questions (role, type, content, reference_answer) VALUES
('Java后端开发工程师', 'Knowledge', '请简述Java中HashMap的工作原理。', 'HashMap基于数组和链表/红黑树实现，通过特征哈希定位数组索引，发生哈希冲突时采用链表，链表长度超过8转化为红黑树。'),
('Web前端开发工程师', 'Knowledge', 'Vue3中的Composition API相比Options API有哪些优势？', '更好的逻辑复用（Hooks）、更好的类型推导、代码组织更灵活。'),
('Python算法工程师', 'Scenario', '如果你的模型在训练集上表现很好，但在测试集上表现很差，你会怎么排查？', '这属于过拟合。可以通过增加数据量、使用正则化、增加Dropout、提前停止（Early Stopping）等方式解决。');
