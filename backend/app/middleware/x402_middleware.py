import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models.order import Order  

logger = logging.getLogger("uvicorn")

class X402PaymentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/pledge/generate_trip_plan" and request.method == "POST":
            order_id = request.headers.get("X-Order-ID")
            
            if not order_id:
                logger.warning("🛡️ [X402_INTERCEPT] Client attempted to access AI resource with missing 'X-Order-ID' header.")
                return JSONResponse(
                    status_code=402,
                    content={
                        "detail": "Payment Required. 'X-Order-ID' header missing.", 
                        "code": "ORDER_ID_MISSING"
                    }
                )
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Order).where(Order.id == order_id))
                order = result.scalar_one_or_none()
                
                if not order:
                    logger.warning(f"🛡️ [X402_INTERCEPT] Client provided an invalid order ID: {order_id}")
                    return JSONResponse(
                        status_code=402,
                        content={
                            "detail": "Order not found. Please create an order first.", 
                            "code": "ORDER_NOT_FOUND"
                        }
                    )
                
                if order.status == "PENDING":
                    logger.info(f"🛡️ [X402_INTERCEPT] Order {order_id} has not cleared on-chain verification. Access denied.")
                    return JSONResponse(
                        status_code=402,
                        content={
                            "detail": f"Payment Required. Order {order_id} is unpaid.",
                            "code": "PAYMENT_REQUIRED",
                            "order_id": order_id,
                            "amount": getattr(order, 'amount', 0.5)
                        }
                    )
                
                if order.status in ["PAID", "COMPLETED"]:
                    logger.info(f"🔓 [X402_RELEASE] Order {order_id} validation passed. Injecting context state...")
                    request.state.order_id = order.id

        response = await call_next(request)
        return response