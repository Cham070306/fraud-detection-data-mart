from __future__ import annotations
import logging
import sys
from pathlib import Path
from datetime import datetime
from src.common.config import PROJECT_ROOT

def get_logger(name: str, level: str = 'INFO') -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    log_dir = PROJECT_ROOT / 'logs'
    log_dir.mkdir(exist_ok=True)
    fh = logging.FileHandler(log_dir / f'{name}_{datetime.now():%Y%m%d}.log', encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger
