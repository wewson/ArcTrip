from pydantic import BaseModel, Field
from typing import List

class CreateOrderRequest(BaseModel):
    user_identifier: str = Field(..., description="User's primary wallet address (primaryWallet)")
    backup_wallet: str = Field(..., description="Emergency backup wallet address designated by the user")
    sub_room_id: str = Field(..., description="X402 decentralized sub-room space ID (bytes32 compatible string)")
    premium: float = Field(..., description="Protocol premium calculated via adaptive actuarial metrics (in USDC)")
    deposit: float = Field(..., description="Principal collateral locked into the vault by the user (in USDC)")
    lock_duration: int = Field(5, description="Protocol protection lock duration in seconds (defaults to 5 seconds for demonstration purposes)")

class TripGenerateRequest(BaseModel):
    destination: str = Field(..., description="Travel destination")
    days: int = Field(..., ge=1, le=30, description="Total duration of the trip in days")
    preferences: str = Field(..., description="User travel style and preferences description")

class DailyScheduleItem(BaseModel):
    day: int
    activities: List[str]

class TripPlanResponse(BaseModel):
    title: str
    budget_estimate: str
    daily_schedule: List[DailyScheduleItem]


class CircleMetadata(BaseModel):
    order_id: str

class CirclePaymentData(BaseModel):
    id: str
    status: str
    amount: str
    currency: str
    metadata: CircleMetadata

class CircleWebhookPayload(BaseModel):
    type: str
    data: CirclePaymentData