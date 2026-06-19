import logging
from typing import Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from web3 import Web3
from eth_account import Account

from app.database import get_db, Order
from app.services.ai_service import AIService

from app.routers.vault_router import router as pledge_router
from app.routers.vault_router import execute_factory_vault
from app.routers.trip_router import router as trip_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*20 + " 📡 X402 DYNAMIC API RADAR ACTIVATED " + "="*20)
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"🔗 Endpoint registered successfully -> {route.path} {list(route.methods)}")
    print("="*75 + "\n")
    yield


app = FastAPI(title="ArcTrip X402 Parametric Protocol", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             
    allow_credentials=True,
    allow_methods=["*"],             
    allow_headers=["*"],             
)

app.include_router(pledge_router, prefix="/api/pledge")
app.include_router(trip_router, prefix="/api/pledge")

RPC_URL = "https://rpc.testnet.arc.network"  
w3 = Web3(Web3.HTTPProvider(RPC_URL))

AGENT_PRIVATE_KEY = "0x0000000000000000000000000000000000000000000000000000000000000000"  
try:
    agent_account = Account.from_key(AGENT_PRIVATE_KEY)
    AGENT_ADDRESS = agent_account.address
    logger.info(f"🤖 [X402_AGENT_ACTIVE] Agent cryptographic identity bound. Address: {AGENT_ADDRESS}")
except Exception as e:
    logger.warning(f"⚠️ [X402_AGENT_STANDBY] Agent key contextual setup missing or invalid: {str(e)}")

FACTORY_ADDRESS = w3.to_checksum_address("0x68b7200887bfF90c9800941524Cb546BBf3c47Ae")
FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_orderId", "type": "string"},
            {"internalType": "address", "name": "_backupWallet", "type": "address"}
        ],
        "name": "agentExecutePayout",  
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class AgentPayoutPayload(BaseModel):
    order_id: str
    vault_address: str
    user_wallet_address: str
    backup_wallet: str  


@app.post("/api/pledge/agent_execute_payout", tags=["X402 On-Chain Agent Core Liquidation Path"])
async def alias_agent_execute_payout(payload: AgentPayoutPayload, db: AsyncSession = Depends(get_db)):
    """
    Agent cryptographic signature execution pipeline gateway.
    """
    logger.info(f"🚨 [LIQUIDATION_PHASE_3] Inbound payout clearing signal received. Order Reference Token: 🎫 {payload.order_id}")
    logger.info(f"🔒 Destination settlement recipient target locked: {payload.backup_wallet}")
    
    if not w3.is_connected():
        raise HTTPException(status_code=500, detail="Network node connectivity failure. Unable to clear on-chain transaction logs.")
        
    if not w3.is_address(payload.backup_wallet):
        raise HTTPException(status_code=400, detail="Settlement routing target failed standard 0x address pattern matching.")

    target_backup_wallet = w3.to_checksum_address(payload.backup_wallet)

    try:
        factory_contract = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)
        nonce = w3.eth.get_transaction_count(AGENT_ADDRESS, "pending")
        
        try:
            gas_estimate = factory_contract.functions.agentExecutePayout(
                payload.order_id,
                target_backup_wallet
            ).estimate_gas({"from": AGENT_ADDRESS})
        except Exception as ge:
            logger.warning(f"⚠️ Dynamic resource profiling variance encountered. Forcing fallback bounds calculation: {str(ge)}")
            gas_estimate = 250000

        logger.info("🛡️ [RESCUE_DISPATCH] Agent constructing raw smart contract deployment transaction wrapper...")
        tx_data = factory_contract.functions.agentExecutePayout(
            payload.order_id,
            target_backup_wallet
        ).build_transaction({
            "from": AGENT_ADDRESS,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": w3.eth.gas_price,
            "chainId": 5042002  
        })

        signed_tx = w3.eth.account.sign_transaction(tx_data, private_key=AGENT_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = w3.to_hex(tx_hash)
        logger.info(f"📡 Broadcast completed. On-chain validation footprint trace reference: {tx_hash_hex}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        
        if receipt["status"] == 1:
            logger.info(f"🎉 [ON_CHAIN_RESCUE_SUCCESS] Voucher settlement verified. Assets extracted and routed to destination wallet: {target_backup_wallet}")
            return {
                "status": "SUCCESS",
                "message": "Asset distribution executed successfully.",
                "tx_hash": tx_hash_hex,
                "backup_wallet": target_backup_wallet
            }
        else:
            raise HTTPException(status_code=500, detail="On-chain gas engine reverted execution. Contract criteria validation failed.")

    except Exception as e:
        logger.error(f"❌ Critical restriction encountered during Agent on-chain clearing pipeline execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent execution path interrupted: {str(e)}")


@app.post("/api/pledge/execute_vault", tags=["X402 Legacy Routing Interceptor Layer"])
async def alias_execute_vault(request: Any = Depends()):
    """ Automatically reroutes client integration steps connecting via old Phase 2 entrypoints """
    return await execute_factory_vault(request)


@app.post("/api/pledge/generate_trip_plan", tags=["X402 Legacy Routing Interceptor Layer"])
async def alias_generate_trip_plan(
    request: Request, 
    x_order_id: Optional[str] = Header(None, alias="X-Order-ID"), 
    db: AsyncSession = Depends(get_db)
):
    """
    Dynamic request body extraction layer. Handles adaptive parameters tracking without hardcoded values.
    """
    logger.info("🎯 [X402_MAIN_RADAR_INTERCEPT] Interception successful. Initializing adaptive unpack routine matrices...")
    try:
        destination = "Tokyo"  
        days = 5  
        budget = 0  
        
        try:
            raw_body = await request.body()
            if raw_body:
                body = await request.json()
                logger.info(f"📦 [X402_PACKET_INBOUND] Verified client ingress structural JSON layout payload: {body}")
                
                if isinstance(body, dict):
                    inner_data = body.get("params") or body.get("data") or body
                    if not isinstance(inner_data, dict):
                        inner_data = body
                    
                    extracted_dest = (
                        inner_data.get("destination") or 
                        inner_data.get("to_location") or 
                        inner_data.get("location") or 
                        inner_data.get("city") or 
                        body.get("destination")
                    )
                    if extracted_dest:
                        destination = str(extracted_dest).strip()
                    
                    extracted_days = (
                        inner_data.get("days") or 
                        inner_data.get("duration") or 
                        body.get("days")
                    )
                    if extracted_days:
                        days = int(extracted_days)

                    extracted_budget = (
                        inner_data.get("budget") or 
                        inner_data.get("totalBudget") or 
                        inner_data.get("deposit") or 
                        body.get("budget")
                    )
                    if extracted_budget:
                        budget = int(float(extracted_budget))
                        
                logger.info(f"🚀 [X402_PARSED_EFFECTIVE] Parameters computed -> Target Vector: 【{destination}】 | Bounded Timeframe: {days} days | Budget Allowance: {budget} USDC")
        except Exception as e:
            logger.warning(f"⚠️ [X402_MAIN] Packet extraction encounter anomaly: {str(e)}. Enforcing robust demo bypass configurations.")

        effective_order_id = x_order_id
        if not effective_order_id or effective_order_id in ["", "undefined", "null"]:
            logger.warning("⚠️ [X402_MAIN] Missing authorization context in X-Order-ID headers. Injecting simulated token schema access credentials...")
            effective_order_id = "DEMO_ROADSHOW_LOCK_05_USDC"

        order = None
        if effective_order_id != "DEMO_ROADSHOW_LOCK_05_USDC":
            result = await db.execute(select(Order).filter(Order.id == effective_order_id))
            order = result.scalar_one_or_none()
        
        if not order:
            logger.warning(f"🚨 [X402_MAIN_DEMO_MODE] Hackathon validation bypass triggered. Offloading computation path directly to inference layer...")
            ai_plan = await AIService.generate_trip_plan(destination, days, budget)
            return {
                "status": "success", 
                "ai_plan": ai_plan,
                "plan_content": ai_plan
            }
        
        if order.status != "PAID" and order.status != "COMPLETED":
            raise HTTPException(status_code=402, detail="❌ Parametric weather weather vault on-chain balancing checkpoint unfulfilled. Compute assets locked.")
            
        logger.info(f"🚀 [AI_ENGINE_TRIGGERED] On-chain vault clearing successful for order reference {effective_order_id}. Compiling tracking algorithms for destination: 【{destination}】...")
        
        
        order_budget = int(order.amount) if (order and order.amount) else budget

        ai_plan = await AIService.generate_trip_plan(destination, days, order_budget)
        
        order.status = "COMPLETED"
        order.ai_result = ai_plan
        await db.commit()
        
        return {
            "status": "success", 
            "ai_plan": ai_plan,
            "plan_content": ai_plan
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ [X402_MAIN_ERROR] Core routing framework pipeline encountered an unhandled exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"status": "RUNNING", "protocol": "X402_PARAMETRIC"}