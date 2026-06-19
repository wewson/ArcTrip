# app/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


class Settings(BaseSettings):
    APP_NAME: str = "arctrip-x402-core"
    PROJECT_NAME: str = "arctrip-x402-core"
    DATABASE_URL: str = "sqlite+aiosqlite:///./arctrip.db"
    TRIP_PRICE_USDC: float = 0.5
    
    # 🔗 Arc Network & Web3 Core Parameters
    ARC_TESTNET_RPC: str = os.getenv("ARC_TESTNET_RPC", "https://rpc.testnet.arc.network")
    CHAIN_ID: int = int(os.getenv("CHAIN_ID", 5042002))
    
    # 🎯 X402 Factory & Token Physical Contract Addresses
    FACTORY_ADDRESS: str = os.getenv("X402_FACTORY_ADDRESS", "0x68b7200887bfF90c9800941524Cb546BBf3c47Ae")
    USDC_CONTRACT_ADDRESS: str = os.getenv("USDC_CONTRACT_ADDRESS", "0x3600000000000000000000000000000000000000")
    
    # 📡 Circle Developer-Controlled Wallets SDK Custody Secrets
    CIRCLE_API_KEY: str = os.getenv("CIRCLE_API_KEY", "")
    CIRCLE_ENTITY_SECRET: str = os.getenv("CIRCLE_ENTITY_SECRET", "")
    CIRCLE_AGENT_WALLET_ID: str = os.getenv("CIRCLE_AGENT_WALLET_ID", "")
    CIRCLE_AGENT_WALLET_ADDRESS: str = os.getenv("CIRCLE_AGENT_WALLET_ADDRESS", "0x5d88b43afee107834aead4f8034d0b3199a979e3")

    class Config:
        case_sensitive = True


settings = Settings()