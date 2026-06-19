import os
import logging
from web3 import Web3

logger = logging.getLogger("uvicorn")

class VaultService:
    def __init__(self):
        self.rpc_url = os.getenv("ARC_TESTNET_RPC", "https://rpc.testnet.arc.network")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.factory_addr = os.getenv("FACTORY_ADDRESS", "0x68b7200887bfF90c9800941524Cb546BBf3c47Ae")
        
        # 🎯 Factory ABI matching production contract layout
        self.abi = [
            {
                "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
                "name": "orders",
                "outputs": [
                    {"internalType": "address", "name": "vault", "type": "address"},
                    {"internalType": "bool", "name": "activated", "type": "bool"},
                    {"internalType": "bytes32", "name": "subRoom", "type": "bytes32"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    async def get_vault_address_by_hash(self, order_hash_hex: str) -> str:
        """
        [ON-CHAIN RADAR] Fetches the isolated vault contract instance address 
        from the underlying factory orders registry mapping using the orderHash context.
        """
        try:
            if not order_hash_hex.startswith("0x"): 
                order_hash_hex = "0x" + order_hash_hex
                
            order_hash_bytes = self.w3.to_bytes(hexstr=order_hash_hex)
            
            factory_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.factory_addr),
                abi=self.abi
            )
            
            # Query the public mapping getter function
            vault_data = factory_contract.functions.orders(order_hash_bytes).call()
            
            # Element index 0 is the successfully deployed physical vault contract deployment address
            vault_address = vault_data[0]
            logger.info(f"🔍 [ARC_FACTORY_PROBE] OrderHash: {order_hash_hex} -> Isolated Vault Contract: {vault_address}")
            return vault_address
        except Exception as e:
            logger.warning(f"⚠️ [VAULT_PROBE_FAILED] Error parsing factory context storage mapping: {str(e)}")
            return "0x0000000000000000000000000000000000000000"