from __future__ import annotations
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = PROJECT_ROOT / 'configs'
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
DATA_INTERIM_DIR = PROJECT_ROOT / 'data' / 'interim'
DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'

DEFAULT_PAYSIM_FILE = 'PS_20174392719_1491204439457_log.csv'
DEFAULT_CHUNK_SIZE = 200_000
DEFAULT_START_DATE = '2023-01-01'
SIMULATION_STEPS = 744
DAYS_PER_STEP = 1.0 / 24.0

VALID_TYPES = {'CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER'}
HIGH_RISK_TYPES = {'TRANSFER', 'CASH_OUT'}

AMOUNT_BANDS = [
    ('XS', 0.0, 1000.0),
    ('S', 1000.0, 10000.0),
    ('M', 10000.0, 100000.0),
    ('L', 100000.0, 1000000.0),
    ('XL', 1000000.0, 10000000.0),
    ('XXL', 10000000.0, None),
]

@dataclass
class DatabaseConfig:
    server: str = os.getenv('FRAUD_DB_SERVER', 'localhost')
    database: str = os.getenv('FRAUD_DB_NAME', 'FraudDW')
    username: str = os.getenv('FRAUD_DB_USER', '')
    password: str = os.getenv('FRAUD_DB_PASSWORD', '')
    driver: str = 'ODBC Driver 17 for SQL Server'
    trusted_connection: bool = True

    def connection_string(self) -> str:
        if self.username and self.password:
            return (
                f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};'
                f'UID={self.username};PWD={self.password};TrustServerCertificate=yes'
            )
        return (
            f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};'
            f'Trusted_Connection=yes;TrustServerCertificate=yes'
        )

@dataclass
class AppConfig:
    paysim_file: Path = DATA_RAW_DIR / DEFAULT_PAYSIM_FILE
    chunk_size: int = DEFAULT_CHUNK_SIZE
    start_date: str = DEFAULT_START_DATE
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    risk_policy: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path | None = None) -> 'AppConfig':
        config_path = config_path or (CONFIGS_DIR / 'app.yaml')
        cfg = cls()
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            cfg.paysim_file = Path(data.get('paysim_file', cfg.paysim_file))
            cfg.chunk_size = int(data.get('chunk_size', cfg.chunk_size))
            cfg.start_date = data.get('start_date', cfg.start_date)
        risk_path = CONFIGS_DIR / 'risk_policy.yaml'
        if risk_path.exists():
            with open(risk_path, 'r', encoding='utf-8') as f:
                cfg.risk_policy = yaml.safe_load(f) or {}
        return cfg

    def risk_levels(self):
        return self.risk_policy.get('risk_levels', [])

    def policy_version(self) -> str:
        return self.risk_policy.get('policy_version', 'v1.0')
