from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, Depends
from sqlalchemy import select, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from pydantic import BaseModel

from app.models.models import users_shops, User, Invoice, InvoiceItem, Shop
from app.schemas.schemas import InvoiceCreate, InvoiceUpdate, InvoiceFilter


# --- Helper functions ---
async def insert_invoice(
        session: AsyncSession,
        invoice_data: InvoiceCreate,
        current_user: User
) -> Invoice:
    """Create new invoice with proper relationship loading"""
    async with session.begin_nested():
        # Проверяем доступ к магазину
        has_access = await check_user_shop_access(
            session,
            current_user.id,
            invoice_data.shop_id
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="No access to this shop")

        # Получаем магазин для проверки
        shop_query = select(Shop).where(Shop.id == invoice_data.shop_id)
        shop_result = await session.execute(shop_query)
        shop = shop_result.scalar_one_or_none()

        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")

        # Создаем инвойс
        new_invoice = Invoice(
            shop_id=invoice_data.shop_id,
            user_id=current_user.id,
            contact_info=invoice_data.contact_info,
            additional_info=invoice_data.additional_info,
            total_amount=invoice_data.total_amount,
            is_paid=invoice_data.is_paid
        )

        session.add(new_invoice)
        await session.flush()

        # Создаем items если они есть
        if hasattr(invoice_data, 'items'):
            for item_data in invoice_data.items:
                item = InvoiceItem(
                    invoice_id=new_invoice.id,
                    name=item_data.name,
                    quantity=item_data.quantity,
                    price=item_data.price,
                    total=item_data.total
                )
                session.add(item)

    await session.commit()

    # Загружаем полные данные для ответа
    query = select(Invoice).options(
        selectinload(Invoice.shop),
        selectinload(Invoice.items)
    ).where(
        Invoice.id == new_invoice.id
    )

    result = await session.execute(query)
    invoice = result.unique().scalar_one()

    return invoice


async def check_user_shop_access(
        session: AsyncSession,
        user_id: int,
        shop_id: int
) -> bool:
    """Check if user has access to shop"""
    query = select(users_shops).where(
        and_(
            users_shops.c.user_id == user_id,
            users_shops.c.shop_id == shop_id
        )
    )
    result = await session.execute(query)
    return result.first() is not None


async def update_invoice(
        session: AsyncSession,
        invoice_id: int,
        invoice_data: InvoiceUpdate,
        current_user: User
) -> Invoice:
    """Update existing invoice"""
    async with session.begin_nested():
        # Получаем инвойс со всеми связанными данными
        query = select(Invoice).options(
            selectinload(Invoice.items),
            selectinload(Invoice.shop)
        ).where(Invoice.id == invoice_id)

        result = await session.execute(query)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Проверяем права
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Only admins can update invoices")

        # Обновляем основные поля
        if invoice_data.contact_info is not None:
            invoice.contact_info = invoice_data.contact_info
        if invoice_data.additional_info is not None:
            invoice.additional_info = invoice_data.additional_info
        if invoice_data.is_paid is not None:
            invoice.is_paid = invoice_data.is_paid

        # Обновляем items если они предоставлены
        if invoice_data.items:
            # Удаляем существующие items
            delete_stmt = delete(InvoiceItem).where(
                InvoiceItem.invoice_id == invoice_id
            )
            await session.execute(delete_stmt)

            # Добавляем новые items
            total_amount = 0
            for item_data in invoice_data.items:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    name=item_data.name,
                    quantity=item_data.quantity,
                    price=item_data.price,
                    total=item_data.quantity * item_data.price
                )
                total_amount += item.total
                session.add(item)

            # Обновляем общую сумму
            invoice.total_amount = total_amount

    # Коммитим изменения
    await session.commit()

    # Загружаем обновленные данные со всеми связями
    refresh_query = select(Invoice).options(
        selectinload(Invoice.items),
        selectinload(Invoice.shop)
    ).where(Invoice.id == invoice_id)

    result = await session.execute(refresh_query)
    updated_invoice = result.unique().scalar_one()

    return updated_invoice


async def delete_invoice(
        session: AsyncSession,
        invoice_id: int,
        current_user: User
) -> bool:
    """Delete invoice"""
    # Get invoice
    query = select(Invoice).where(Invoice.id == invoice_id)
    result = await session.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can delete invoices")

    await session.delete(invoice)
    await session.commit()
    return True


async def fetch_invoice(
        session: AsyncSession,
        invoice_id: int,
        current_user: User
) -> Invoice:
    """Fetch single invoice with all related data"""
    query = select(Invoice).options(
        joinedload(Invoice.items),
        joinedload(Invoice.shop),
        joinedload(Invoice.user)
    ).where(Invoice.id == invoice_id)

    result = await session.execute(query)
    invoice = result.unique().scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check if user has access to the shop
    has_access = await check_user_shop_access(session, current_user.id, invoice.shop_id)
    if not has_access:
        raise HTTPException(status_code=403, detail="No access to this invoice")

    return invoice


async def fetch_invoices_with_filters(
        session: AsyncSession,
        current_user: User,
        filters: InvoiceFilter,
        skip: int = 0,
        limit: int = 100
) -> List[Invoice]:
    """Fetch invoices with filters"""
    # Start building query
    query = select(Invoice).options(
        joinedload(Invoice.items),
        joinedload(Invoice.shop),
        joinedload(Invoice.user)
    )

    # Get all shops user has access to
    shops_query = select(users_shops.c.shop_id).where(
        users_shops.c.user_id == current_user.id
    )
    result = await session.execute(shops_query)
    accessible_shops = [row[0] for row in result.fetchall()]

    # Base filter by accessible shops
    query = query.where(Invoice.shop_id.in_(accessible_shops))

    # Apply filters
    if filters.shop_id:
        if filters.shop_id not in accessible_shops:
            raise HTTPException(status_code=403, detail="No access to this shop")
        query = query.where(Invoice.shop_id == filters.shop_id)

    if filters.is_paid is not None:
        query = query.where(Invoice.is_paid == filters.is_paid)

    if filters.created_after:
        query = query.where(Invoice.created_at >= filters.created_after)

    if filters.created_before:
        query = query.where(Invoice.created_at <= filters.created_before)

    if filters.min_amount is not None:
        query = query.where(Invoice.total_amount >= filters.min_amount)

    if filters.max_amount is not None:
        query = query.where(Invoice.total_amount <= filters.max_amount)

    # Add sorting by date
    query = query.order_by(Invoice.created_at.desc())

    # Add pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await session.execute(query)
    invoices = result.unique().scalars().all()

    # Add formatted dates
    for invoice in invoices:
        if hasattr(invoice, 'created_at') and invoice.created_at:
            invoice.formatted_date = invoice.created_at.strftime("%d-%m-%y %H:%M")

    return invoices