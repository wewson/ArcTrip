# d:\arctrip-x402-core\blockchain\config.py
import os
import json
from web3 import Web3
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets

# 1. 锁定总根目录下的 .env 文件
CORE_DIR = r"d:\arctrip-x402-core"
env_path = os.path.join(CORE_DIR, ".env")

if not os.path.exists(env_path):
    raise FileNotFoundError(f"💥 核心错误：在总根路径 {env_path} 找不到 .env 配置文件！")

load_dotenv(dotenv_path=env_path)

# 2. 从 .env 读取配置（严格对齐你的实际变量名，坚决不返回 None）
def get_env_or_raise(key):
    value = os.getenv(key)
    if not value:
        raise ValueError(f"💥 致命配置缺失：.env 文件中未配置 key: '{key}'")
    return value.strip('"').strip("'")

# 🎯 严丝合缝对齐你的 .env 命名
RPC_URL = get_env_or_raise("ARC_TESTNET_RPC")
CHAIN_ID = int(get_env_or_raise("CHAIN_ID"))

USDC_ADDRESS = Web3.to_checksum_address(get_env_or_raise("USDC_CONTRACT_ADDRESS"))
FACTORY_ADDRESS = Web3.to_checksum_address(get_env_or_raise("FACTORY_ADDRESS"))
AGENT_ADDRESS = Web3.to_checksum_address(get_env_or_raise("CIRCLE_AGENT_ADDRESS"))

CIRCLE_API_KEY = get_env_or_raise("CIRCLE_API_KEY")
CIRCLE_ENTITY_SECRET = get_env_or_raise("CIRCLE_ENTITY_SECRET")
WALLET_SET_ID = get_env_or_raise("CIRCLE_WALLET_SET_ID")
WALLET_ID = get_env_or_raise("CIRCLE_AGENT_WALLET_ID")

# 3. 实例化 Web3 对象
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# 4. 加载合约 ABI 逻辑（恢复你最原始、100% 成功的死磕死办法）
def get_contract_abi(name):
    """采用绝对路径，不管脚本在哪执行，死磕到项目的 abis 目录下"""
    blockchain_dir = r"d:\arctrip-x402-core\blockchain"
    abi_path = os.path.join(blockchain_dir, "abis", f"{name}.json")
    with open(abi_path, "r", encoding="utf-8") as f:
        return json.load(f)["abi"]

factory_abi = get_contract_abi("TravelPigeonFactory")
trip_abi = get_contract_abi("TravelPigeon")

# 5. 实例化已经部署上链的工厂合约对象
factory_contract = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)

# 6. 初始化 Circle 开发者控制钱包客户端与交易 API
circle_client = utils.init_developer_controlled_wallets_client(
    api_key=CIRCLE_API_KEY, 
    entity_secret=CIRCLE_ENTITY_SECRET
)
circle_tx_api = developer_controlled_wallets.TransactionsApi(circle_client)