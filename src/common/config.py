from __future__ import annotations
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any
try:
    from dotenv import load_dotenv
except ImportError:  # Allows lightweight checks before dependencies are installed.
    def load_dotenv(*_args, **_kwargs):
        return False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / '.env')
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
    driver: str = os.getenv('FRAUD_DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    trusted_connection: bool = os.getenv('FRAUD_DB_TRUSTED_CONNECTION', 'true').lower() in {
        '1', 'true', 'yes', 'on'
    }

    def connection_string(self) -> str:
        if self.username and self.password:
            return (
                f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};'
                f'UID={self.username};PWD={self.password};TrustServerCertificate=yes'
            )
        auth = 'Trusted_Connection=yes;' if self.trusted_connection else ''
        return (
            f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};'
            f'{auth}TrustServerCertificate=yes'
        )

@dataclass
class AppConfig:
    paysim_file: Path = DATA_RAW_DIR / DEFAULT_PAYSIM_FILE
    chunk_size: int = DEFAULT_CHUNK_SIZE
    start_date: str = DEFAULT_START_DATE
    max_step: int | None = SIMULATION_STEPS
    max_validation_error_rate: float = 0.001
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    risk_policy: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path | None = None) -> 'AppConfig':
        config_path = config_path or (CONFIGS_DIR / 'app.yaml')
        cfg = cls()
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            configured_file = Path(data.get('paysim_file', cfg.paysim_file))
            cfg.paysim_file = (
                configured_file if configured_file.is_absolute()
                else PROJECT_ROOT / configured_file
            )
            cfg.chunk_size = int(data.get('chunk_size', cfg.chunk_size))
            cfg.start_date = data.get('start_date', cfg.start_date)
            configured_max_step = data.get('max_step', cfg.max_step)
            cfg.max_step = None if configured_max_step is None else int(configured_max_step)
            cfg.max_validation_error_rate = float(
                data.get('max_validation_error_rate', cfg.max_validation_error_rate)
            )
            db_data = data.get('database') or {}
            if not os.getenv('FRAUD_DB_SERVER') and db_data.get('server'):
                cfg.db.server = str(db_data['server'])
            if not os.getenv('FRAUD_DB_NAME') and (db_data.get('name') or db_data.get('database')):
                cfg.db.database = str(db_data.get('name') or db_data.get('database'))
            if not os.getenv('FRAUD_DB_DRIVER') and db_data.get('driver'):
                cfg.db.driver = str(db_data['driver'])
            if 'trusted_connection' in db_data and not os.getenv('FRAUD_DB_TRUSTED_CONNECTION'):
                cfg.db.trusted_connection = bool(db_data['trusted_connection'])
        risk_path = CONFIGS_DIR / 'risk_policy.yaml'
        if risk_path.exists():
            with open(risk_path, 'r', encoding='utf-8') as f:
                cfg.risk_policy = yaml.safe_load(f) or {}
        return cfg

    def risk_levels(self):
        return self.risk_policy.get('risk_levels', [])

    def policy_version(self) -> str:
        return self.risk_policy.get('policy_version', '1.0.0')
