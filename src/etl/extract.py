from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Iterator
from src.common.config import AppConfig
from src.common.logger import get_logger

logger = get_logger('etl.extract')

EXPECTED_COLUMNS = [
    'step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig',
    'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud',
]

def validate_header(columns) -> None:
    missing = [c for c in EXPECTED_COLUMNS if c not in columns]
    if missing:
        raise ValueError(f'CSV thieu cot: {missing}')

def extract_chunks(cfg: AppConfig | None = None) -> Iterator[pd.DataFrame]:
    cfg = cfg or AppConfig.load()
    path = Path(cfg.paysim_file)
    if not path.exists():
        raise FileNotFoundError(f'Khong tim thay file CSV: {path}')
    logger.info(f'Bat dau doc {path} theo chunk size={cfg.chunk_size}')
    reader = pd.read_csv(path, chunksize=cfg.chunk_size)
    for i, chunk in enumerate(reader):
        if i == 0:
            validate_header(chunk.columns)
        logger.info(f'Chunk {i}: {len(chunk)} dong')
        yield chunk
