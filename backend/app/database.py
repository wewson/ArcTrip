# app/database.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_identifier: Mapped[str] = mapped_column(String, index=True, comment="Primary user wallet address")
    status: Mapped[str] = mapped_column(String, default="PENDING")
    amount: Mapped[float] = mapped_column(Float, default=settings.TRIP_PRICE_USDC)
    
    backup_wallet: Mapped[str] = mapped_column(String, nullable=True)
    sub_room_id: Mapped[str] = mapped_column(String, nullable=True)
    premium: Mapped[float] = mapped_column(Float, default=0.0)
    lock_duration: Mapped[float] = mapped_column(Float, default=20.0)
    order_hash: Mapped[str] = mapped_column(String, nullable=True)
    
    vault_address: Mapped[str] = mapped_column(String, nullable=True, comment="Isolated vault instance address derived on Arc network")
    circle_payment_id: Mapped[str] = mapped_column(String, nullable=True)
    deposit_address: Mapped[str] = mapped_column(String, nullable=True) 
    ai_result: Mapped[str] = mapped_column(Text, nullable=True)     
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


async def get_db():
    """FastAPI context dependency injection for database session management"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Automated schema synchronization initialization routine for database layers"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)