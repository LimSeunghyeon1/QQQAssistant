from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    role: Mapped[str] = mapped_column(String(20))


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(Text)
    source_site: Mapped[str] = mapped_column(String(50))
    raw_title: Mapped[str] = mapped_column(Text)
    raw_price: Mapped[float] = mapped_column(Numeric(12, 2))
    raw_currency: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    options: Mapped[List["ProductOption"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    localizations: Mapped[List["ProductLocalizedInfo"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductOption(Base):
    __tablename__ = "product_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    option_key: Mapped[str] = mapped_column(String(255))
    raw_name: Mapped[str] = mapped_column(String(255))
    raw_price_diff: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    product: Mapped[Product] = relationship(back_populates="options")


class ProductLocalizedInfo(Base):
    __tablename__ = "product_localized_info"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    locale: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    option_display_name_format: Mapped[Optional[str]] = mapped_column(String(255))

    product: Mapped[Product] = relationship(back_populates="localizations")


class SalesChannelTemplate(Base):
    __tablename__ = "sales_channel_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_name: Mapped[str] = mapped_column(String(50))
    template_type: Mapped[str] = mapped_column(String(50))
    config_json: Mapped[str] = mapped_column(Text)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_order_id: Mapped[str] = mapped_column(String(100))
    channel_name: Mapped[str] = mapped_column(String(50))
    customer_name: Mapped[str] = mapped_column(String(100))
    customer_phone: Mapped[str] = mapped_column(String(50))
    customer_address: Mapped[str] = mapped_column(Text)
    order_datetime: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50))
    total_amount_krw: Mapped[float] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    shipments: Mapped[List["OrderShipmentLink"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_option_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_options.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column()
    unit_price_krw: Mapped[float] = mapped_column(Numeric(12, 2))

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
    product_option: Mapped[Optional[ProductOption]] = relationship()


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    carrier_name: Mapped[str] = mapped_column(String(50))
    tracking_number: Mapped[str] = mapped_column(String(100))
    shipment_type: Mapped[str] = mapped_column(String(20))
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    orders: Mapped[List["OrderShipmentLink"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan"
    )


class OrderShipmentLink(Base):
    __tablename__ = "order_shipment_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"))

    order: Mapped[Order] = relationship(back_populates="shipments")
    shipment: Mapped[Shipment] = relationship(back_populates="orders")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped[Order] = relationship(back_populates="status_history")
