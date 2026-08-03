-- Crear schema
CREATE SCHEMA IF NOT EXISTS deco_chat;

-- Tabla: usuarios y sesiones
CREATE TABLE deco_chat.users_sessions (
    id SERIAL PRIMARY KEY,
    glpi_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    store_code VARCHAR(10),
    role VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_ip VARCHAR(50)
);

-- Tabla: mensajes de chat
CREATE TABLE deco_chat.chat_messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    response TEXT,
    glpi_tickets_referenced INTEGER[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    server_id INT,
    FOREIGN KEY (user_id) REFERENCES deco_chat.users_sessions(glpi_user_id)
);

-- Tabla: tickets creados desde agente
CREATE TABLE deco_chat.agent_tickets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    glpi_ticket_id INT,
    title VARCHAR(500),
    description TEXT,
    category VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES deco_chat.users_sessions(glpi_user_id)
);

-- Tabla: cache de soluciones GLPI
CREATE TABLE deco_chat.glpi_solutions_cache (
    id SERIAL PRIMARY KEY,
    glpi_ticket_id INT UNIQUE,
    title VARCHAR(500),
    problem_keywords TEXT,
    solution TEXT,
    category VARCHAR(100),
    attachments JSONB,
    steps JSONB,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '6 hours')
);

-- Tabla: audit log
CREATE TABLE deco_chat.audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action VARCHAR(100),
    resource VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    result VARCHAR(50)
);

-- Crear índices
CREATE INDEX idx_users_glpi_id ON deco_chat.users_sessions(glpi_user_id);
CREATE INDEX idx_chat_user_id ON deco_chat.chat_messages(user_id);
CREATE INDEX idx_chat_created ON deco_chat.chat_messages(created_at);
CREATE INDEX idx_audit_user ON deco_chat.audit_log(user_id);
CREATE INDEX idx_audit_time ON deco_chat.audit_log(timestamp);

-- Insertar usuario de prueba
INSERT INTO deco_chat.users_sessions (glpi_user_id, email, store_code, role)
VALUES 
    ('glpi_tech_001', 'tech@deco.com.pe', '045', 'technician'),
    ('glpi_admin_001', 'admin@deco.com.pe', 'central', 'admin');
