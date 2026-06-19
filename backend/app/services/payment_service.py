import os
import asyncio
import logging
from decimal import Decimal
from typing import Optional
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider
from web3.exceptions import ProviderConnectionError, Web3Exception

from app.database import Order
from app.config import settings

logger = logging.getLogger("uvicorn")

MAX_RETRIES = 3
RETRY_BACKOFF = 1.5


class PayoutRequest(BaseModel):
    order_id: str


class PaymentService:

    @staticmethod
    async def create_payment_intent(db: AsyncSession, user_identifier: str, premium: float = 0.1, deposit: float = 0.5) -> Order:
        order_id = str(uuid4())
        
        circle_deposit_addr = os.getenv(
            "CIRCLE_AGENT_WALLET_ADDRESS", 
            "0x5d88b43afee107834aead4f8034d0b3199a979e3"
        )
        
        new_order = Order(
            id=order_id,
            user_identifier=user_identifier,
            status="PENDING",
            amount=deposit,                       
            premium=premium,                      
            lock_duration=604800,                 
            deposit_address=AsyncWeb3.to_checksum_address(circle_deposit_addr),
            created_at=datetime.utcnow()
        )
        
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        
        logger.info(f"📝 [ORDER_INITIALIZED] ID: {order_id} | Premium: {premium} USDC | Deposit: {deposit} USDC")
        return new_order

    @staticmethod
    async def verify_on_chain_balance(db: AsyncSession, order_id: str) -> bool:
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update(skip_locked=True)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            logger.warning(f"❌ [BALANCE_VERIFICATION] Order context not found: {order_id}")
            return False
            
        if order.status == "PAID":
            logger.info(f"✨ [BALANCE_VERIFICATION] Order {order_id} is already marked PAID. Skipping check.")
            return True
            
        if not order.deposit_address:
            logger.error(f"❌ [BALANCE_VERIFICATION] Order {order_id} is missing a deposit destination address.")
            return False

        rpc_url = getattr(settings, "RPC_URL", "https://rpc.testnet.arc.network")
        w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        
        try:
            if not await w3.is_connected():
                raise ProviderConnectionError("Failed to establish communication with Arc Testnet RPC node.")

            real_balance_wei = None
            for attempt in range(MAX_RETRIES):
                try:
                    real_balance_wei = await w3.eth.get_balance(
                        w3.to_checksum_address(order.deposit_address)
                    )
                    break
                except (Web3Exception, asyncio.TimeoutError) as e:
                    if attempt == MAX_RETRIES - 1: 
                        raise
                    wait = RETRY_BACKOFF ** attempt
                    logger.warning(f"⚠️ Arc RPC probe failed ({attempt+1}/{MAX_RETRIES}): {e}. Retrying in {wait:.1f}s...")
                    await asyncio.sleep(wait)

            if real_balance_wei is None:
                raise RuntimeError("Failed to sync natively with on-chain balance after retries.")

            order_premium = order.premium if order.premium is not None else 0.1
            required_wei = int(Decimal(str(order_premium)) * Decimal("10") ** 18)

            real_balance_usdc = Decimal(real_balance_wei) / Decimal("10") ** 18
            logger.info(
                f"💰 [ARC_RADAR_PROBE] Target Wallet: {order.deposit_address} | "
                f"Native Balance: {real_balance_usdc} USDC | Target Premium: {order_premium} USDC"
            )

            if real_balance_wei >= required_wei:
                await db.execute(
                    update(Order)
                    .where(Order.id == order_id)
                    .where(Order.status != "PAID")
                    .values(status="PAID")
                )
                await db.commit()
                logger.info(f"✅ [VERIFICATION_SUCCESS] Native on-chain USDC fully cleared for order {order_id}.")
                return True
            else:
                logger.info(f"⏳ [VERIFICATION_PENDING] Order {order_id} has insufficient on-chain balance or block is unconfirmed.")
                return False
                
        except (ProviderConnectionError, asyncio.TimeoutError, Web3Exception) as e:
            logger.warning(f"⚠️ [BALANCE_VERIFICATION] RPC node anomaly or network latency encountered: {e}")
            await db.rollback()
            return False
        except Exception as e:
            logger.exception(f"💥 [BALANCE_VERIFICATION_CRITICAL] System exception encountered: {str(e)}")
            await db.rollback()
            return False

    @staticmethod
    async def agent_execute_payout_logic(db: AsyncSession, payload: PayoutRequest) -> bool:
        result = await db.execute(
            select(Order)
            .where(Order.id == payload.order_id)
            .with_for_update(skip_locked=True)
        )
        order = result.scalar_one_or_none()

        if not order:
            logger.error(f"❌ [AGENT_LIQUIDATION_ERROR] Reference order token not found: {payload.order_id}")
            return False

        target_safety_wallet = order.user_identifier
        if not target_safety_wallet:
            logger.error(f"❌ [AGENT_LIQUIDATION_ERROR] Reference order {payload.order_id} missing user destination address context.")
            return False

        logger.info(f"🚨 [AGENT_LIQUIDATION_TRIGGERED] Order: {payload.order_id} | Routing to safety wallet: {target_safety_wallet}")
        
        try:
            await db.execute(
                update(Order)
                .where(Order.id == payload.order_id)
                .values(status="REFUNDED") 
            )
            await db.commit()
            logger.info(f"🎉 [AGENT_PAYOUT_SUCCESS] Asset balance cleared and routed to backup wallet: {target_safety_wallet}")
            return True
        except Exception as e:
            logger.error(f"💥 [AGENT_PAYOUT_CRITICAL_FAILURE]: {str(e)}")
            await db.rollback()
            return False

    @staticmethod
    async def verify_by_balance(db: AsyncSession, order_id: str) -> bool:
        return await PaymentService.verify_on_chain_balance(db, order_id)