from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

STAGE_RAW_DIRS = {
    "stage1_regulatory": DATA_DIR / "stage1_regulatory" / "raw",
    "stage2_technical": DATA_DIR / "stage2_technical" / "raw",
    "stage3_feasibility": DATA_DIR / "stage3_feasibility" / "raw",
}

# Which stages each source folder's documents belong to for retrieval.
# stage1_regulatory feeds both stage1 (regulatory check) and stage2
# (requirements integration, which needs the regulations + the technical
# docs) -- enforced via a WHERE doc_type IN (...) at query time, not by
# duplicating rows.
SOURCE_TO_STAGES = {
    "stage1_regulatory": ["stage1", "stage2"],
    "stage2_technical": ["stage2"],
    "stage3_feasibility": ["stage3"],
}

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MAX_TOKENS = 256

CHUNK_SIZE_CHARS = 1_200
CHUNK_OVERLAP_CHARS = 200
