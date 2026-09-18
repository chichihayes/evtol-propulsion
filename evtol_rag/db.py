import os

import pymysql

from . import config


def _load_env():
    env_path = config.PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "evtol_compliance_rag")

SCHEMA = """
CREATE TABLE IF NOT EXISTS document_chunks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chunk_key VARCHAR(255) NOT NULL UNIQUE,
    doc_type VARCHAR(50) NOT NULL,
    source_document VARCHAR(255) NOT NULL,
    page_start INT,
    page_end INT,
    section_ref VARCHAR(100),
    chunk_index INT NOT NULL,
    text MEDIUMTEXT NOT NULL,
    char_count INT NOT NULL,
    embedding JSON NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_doc_type (doc_type),
    INDEX idx_source_document (source_document)
);
"""


def get_connection(with_database=True):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if with_database else None,
        autocommit=True,
    )


def init_db():
    conn = get_connection(with_database=False)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.close()

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
    conn.close()
