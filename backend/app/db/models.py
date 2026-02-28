# backend/app/db/models.py

# ------------------------------------------------------------

# SQLAlchemy ORM models that match schema_v0_8.sql

# Money stored in cents (BIGINT).

# ------------------------------------------------------------

 

from sqlalchemy import (

    BigInteger, Integer, String, Text, DateTime, Date, Time,

    CheckConstraint, ForeignKey, UniqueConstraint, Boolean

)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime

from .session import Base

 

# USERS -------------------------------------------------------

 

class User(Base):

    __tablename__ = "users"

    __table_args__ = {"schema": "trading"}

 

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)

    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'customer' or 'admin'

    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

 

    cash_account: Mapped["CashAccount"] = relationship("CashAccount", uselist=False, back_populates="user")

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")

 

# CASH ACCOUNTS -----------------------------------------------

 

class CashAccount(Base):

    __tablename__ = "cash_accounts"

    __table_args__ = {"schema": "trading"}

 

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("trading.users.id", ondelete="CASCADE"), unique=True, nullable=False)

    balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

 

    user: Mapped["User"] = relationship("User", back_populates="cash_account")

 

# STOCKS ------------------------------------------------------

 

class Stock(Base):

    __tablename__ = "stocks"

    __table_args__ = (

        UniqueConstraint("ticker", name="uq_stocks_ticker"),

        {"schema": "trading"}

    )

 

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    ticker: Mapped[str] = mapped_column(String(10), nullable=False)

    company_name: Mapped[str] = mapped_column(String(160), nullable=False)

    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)

    current_price_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    opening_price_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    daily_high_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    daily_low_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

 

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="stock")

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="stock")

 

# ORDERS ------------------------------------------------------

 

class Order(Base):

    __tablename__ = "orders"

    __table_args__ = {"schema": "trading"}

 

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("trading.users.id", ondelete="RESTRICT"), nullable=False)

    stock_id: Mapped[int] = mapped_column(ForeignKey("trading.stocks.id", ondelete="RESTRICT"), nullable=False)

    order_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'buy' or 'sell'

    shares: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[str] = mapped_column(String(15), nullable=False)  # 'pending', 'executed', 'canceled'

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

 

    user: Mapped["User"] = relationship("User", back_populates="orders")

    stock: Mapped["Stock"] = relationship("Stock", back_populates="orders")

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="order")

 

# TRANSACTIONS ------------------------------------------------

 

class Transaction(Base):

    __tablename__ = "transactions"

    __table_args__ = {"schema": "trading"}

 

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    order_id: Mapped[int | None] = mapped_column(ForeignKey("trading.orders.id", ondelete="SET NULL"), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("trading.users.id", ondelete="RESTRICT"), nullable=False)

    stock_id: Mapped[int | None] = mapped_column(ForeignKey("trading.stocks.id", ondelete="SET NULL"), nullable=True)

    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'buy','sell','deposit','withdrawal','canceled'

    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    shares: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

 

    user: Mapped["User"] = relationship("User", back_populates="transactions")

    order: Mapped["Order"] = relationship("Order", back_populates="transactions")

    stock: Mapped["Stock"] = relationship("Stock", back_populates="transactions")

 

# MARKET HOURS / HOLIDAYS (optional ORM — used later if needed)

 

class MarketHours(Base):

    __tablename__ = "market_hours"

    __table_args__ = {"schema": "trading"}

 

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    opens_at: Mapped[str] = mapped_column(Time, nullable=False)

    closes_at: Mapped[str] = mapped_column(Time, nullable=False)

 

class MarketHoliday(Base):

    __tablename__ = "market_holidays"

    __table_args__ = {"schema": "trading"}

 

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    holiday_date: Mapped[datetime] = mapped_column(Date, nullable=False)

    description: Mapped[str | None] = mapped_column(String(200), nullable=True)