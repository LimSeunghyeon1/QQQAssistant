from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Numeric, String, Text
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
    raw_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_price: Mapped[float] = mapped_column(Numeric(12, 2))
    raw_currency: Mapped[str] = mapped_column(String(10))
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    margin_rate: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    vat_rate: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    shipping_fee: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    detail_image_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
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
    localized_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
    after_sales_cases: Mapped[List["AfterSalesCase"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    refund_records: Mapped[List["RefundRecord"]] = relationship(
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
    purchase_order_links: Mapped[List["PurchaseOrderSourceLink"]] = relationship(
        back_populates="order_item", cascade="all, delete-orphan"
    )
    after_sales_cases: Mapped[List["AfterSalesCase"]] = relationship(
        back_populates="order_item", cascade="all, delete-orphan"
    )
    refund_records: Mapped[List["RefundRecord"]] = relationship(
        back_populates="order_item", cascade="all, delete-orphan"
    )


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

    after_sales_cases: Mapped[List["AfterSalesCase"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan"
    )
    refund_records: Mapped[List["RefundRecord"]] = relationship(
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


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="CREATED")
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    expected_arrival_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["PurchaseOrderStatusHistory"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_option_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_options.id"), nullable=True
    )
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    quantity: Mapped[int] = mapped_column()
    line_total: Mapped[float] = mapped_column(Numeric(18, 2), default=0)

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    source_links: Mapped[List["PurchaseOrderSourceLink"]] = relationship(
        back_populates="purchase_order_item", cascade="all, delete-orphan"
    )


class PurchaseOrderSourceLink(Base):
    __tablename__ = "purchase_order_source_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    purchase_order_item_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_order_items.id")
    )
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    source_quantity: Mapped[int] = mapped_column()

    purchase_order_item: Mapped[PurchaseOrderItem] = relationship(
        back_populates="source_links"
    )
    order_item: Mapped[OrderItem] = relationship(
        back_populates="purchase_order_links"
    )


class PurchaseOrderStatusHistory(Base):
    __tablename__ = "purchase_order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    previous_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="status_history")


class AfterSalesNotificationChannel(PyEnum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"
    NONE = "NONE"


class AfterSalesCaseStatus(PyEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_REFUND = "WAITING_REFUND"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class AfterSalesCaseType(PyEnum):
    RETURN = "RETURN"
    EXCHANGE = "EXCHANGE"
    REPAIR = "REPAIR"
    INQUIRY = "INQUIRY"


class RefundStatus(PyEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"


class RefundAmountType(PyEnum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    SHIPPING_ONLY = "SHIPPING_ONLY"
    ADJUSTMENT = "ADJUSTMENT"


class AfterSalesCase(Base):
    __tablename__ = "after_sales_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("order_items.id"), nullable=True
    )
    shipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipments.id"), nullable=True
    )
    case_type: Mapped[AfterSalesCaseType] = mapped_column(
        Enum(AfterSalesCaseType, name="after_sales_case_type")
    )
    status: Mapped[AfterSalesCaseStatus] = mapped_column(
        Enum(AfterSalesCaseStatus, name="after_sales_case_status"),
        default=AfterSalesCaseStatus.OPEN,
    )
    customer_notification_channel: Mapped[AfterSalesNotificationChannel] = mapped_column(
        Enum(AfterSalesNotificationChannel, name="after_sales_notification_channel"),
        default=AfterSalesNotificationChannel.IN_APP,
    )
    claim_amount_krw: Mapped[float | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    order: Mapped[Order] = relationship(back_populates="after_sales_cases")
    order_item: Mapped[OrderItem | None] = relationship(back_populates="after_sales_cases")
    shipment: Mapped[Shipment | None] = relationship(back_populates="after_sales_cases")
    refund_records: Mapped[List["RefundRecord"]] = relationship(
        back_populates="after_sales_case", cascade="all, delete-orphan"
    )


class RefundRecord(Base):
    __tablename__ = "refund_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("order_items.id"), nullable=True
    )
    shipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipments.id"), nullable=True
    )
    after_sales_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("after_sales_cases.id"), nullable=True
    )
    amount_type: Mapped[RefundAmountType] = mapped_column(
        Enum(RefundAmountType, name="refund_amount_type"),
        default=RefundAmountType.FULL,
    )
    refund_amount_krw: Mapped[float] = mapped_column(Numeric(14, 2))
    refund_currency: Mapped[str] = mapped_column(String(10), default="KRW")
    status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus, name="refund_status"), default=RefundStatus.REQUESTED
    )
    refund_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    order: Mapped[Order] = relationship(back_populates="refund_records")
    order_item: Mapped[OrderItem | None] = relationship(back_populates="refund_records")
    shipment: Mapped[Shipment | None] = relationship(back_populates="refund_records")
    after_sales_case: Mapped[AfterSalesCase | None] = relationship(
        back_populates="refund_records"
    )
