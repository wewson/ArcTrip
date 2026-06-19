import logging
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db, Order
from app.services.payment_service import PaymentService
from app.services.ai_service import AIService
from app.services.agent_service import AgentService

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/v1/trip", tags=["Trip"])

agent_svc = AgentService()


class CreateOrderRequest(BaseModel):
    user_identifier: str  


class VerifyRequest(BaseModel):
    order_id: str         


@router.post("/order", summary="Create Arc X402 parametric vault order")
async def create_order(payload: CreateOrderRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"📥 [X402_ROUTER] Intent captured for trip creation. User identifier: {payload.user_identifier}")
    try:
        order = await PaymentService.create_payment_intent(db, payload.user_identifier)
        
        logger.info(f"🪙 [Circle_Agent] Vault escrow locked -> Order ID: {order.id} | Deposit Address: {order.deposit_address}")
        
        return {
            "status": "success",
            "order_id": order.id,
            "deposit_blockchain_address": order.deposit_address,
            "msg": "X402 Parametric vault registry success."
        }
    except Exception as e:
        logger.error(f"❌ [X402_ROUTER] Critical error during order initialization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create insurance vault: {str(e)}")


@router.post("/verify_by_balance", summary="Trigger on-chain smart balance verification")
async def verify_by_balance(payload: VerifyRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"📡 [X402_ROUTER] Received verification settlement request for Order: {payload.order_id}")
    try:
        success = await PaymentService.verify_by_balance(db, payload.order_id)
        
        if success:
            logger.info(f"🎉 [X402_VERIFIED] On-chain collateral validated for Order: {payload.order_id}. State changed to PAID.")
            return {
                "status": "PAID",
                "msg": "USDC Asset locked into parametric vault successfully."
            }
        else:
            logger.warning(f"⏳ [X402_PENDING] Collateral mismatch or insufficient on-chain balance for Order: {payload.order_id}.")
            return {
                "status": "PENDING",
                "msg": "Still waiting for on-chain collateral deposit."
            }
    except Exception as e:
        logger.error(f"❌ [X402_ROUTER] On-chain settlement tracking crashed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"On-chain verification tracking crashed: {str(e)}")


@router.post("/generate", summary="Release native backup AI engine blueprint")
async def generate_trip(
    request: Request, 
    x_order_id: str = Header(..., alias="X-Order-ID"), 
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"🤖 [X402_ROUTER] Processing AI itinerary generation via secure lane for Order: {x_order_id}")
    
    result = await db.execute(select(Order).filter(Order.id == x_order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Target parametric contract ledger not found.")
        
    if order.status != "PAID" and order.status != "COMPLETED":
        raise HTTPException(status_code=402, detail="X402 Contract collateral lock verification missing. AI computation denied.")
    
    destination = "Singapore"
    days = 1
    try:
        raw_body = await request.body()
        if raw_body:
            body = await request.json()
            destination = body.get("destination") or body.get("to_location") or body.get("location") or "Singapore"
            days = int(body.get("days") or body.get("duration") or 1)
    except Exception:
        pass

    logger.info(f"🚀 [X402_AI_TRIGGER] Validation verified. Deploying DeepSeek SDK array for destination: {destination}")
    ai_plan = await AIService.generate_trip_plan(destination, days)
    
    order.status = "COMPLETED"
    order.ai_result = ai_plan
    await db.commit()
    
    return {
        "status": "success",
        "ai_plan": ai_plan,
        "plan_content": ai_plan
    }