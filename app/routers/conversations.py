import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/conversations", tags=["Messages"])


class StartConversation(BaseModel):
    listing_id: uuid.UUID


class SendMessage(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.post("", status_code=201)
async def start_conversation(
    body: StartConversation,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await db.get(Listing, body.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
    if not listing.user_id:
        raise HTTPException(status_code=400, detail="Anonim e'longa yozib bo'lmaydi")
    if listing.user_id == user.id:
        raise HTTPException(status_code=400, detail="O'z e'loningizga yozib bo'lmaydi")

    existing = (await db.execute(
        select(Conversation).where(
            Conversation.listing_id == body.listing_id,
            Conversation.buyer_id == user.id,
        )
    )).scalar_one_or_none()

    if existing:
        return _conv_out(existing, user.id)

    conv = Conversation(
        listing_id=body.listing_id,
        buyer_id=user.id,
        seller_id=listing.user_id,
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return _conv_out(conv, user.id)


@router.get("")
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(or_(Conversation.buyer_id == user.id, Conversation.seller_id == user.id))
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
    )
    convs = result.scalars().all()

    out = []
    for c in convs:
        other_id = c.seller_id if c.buyer_id == user.id else c.buyer_id
        other = await db.get(User, other_id)
        listing = await db.get(Listing, c.listing_id)

        unread = (await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == c.id,
                Message.sender_id != user.id,
                Message.is_read == False,
            )
        )).scalar() or 0

        out.append({
            "id": str(c.id),
            "listing_id": str(c.listing_id),
            "listing_title": listing.category if listing else "—",
            "listing_price": listing.price if listing else 0,
            "listing_image": listing.image_urls[0] if listing and listing.image_urls else None,
            "other_id": str(other_id),
            "other_name": other.full_name if other else "—",
            "other_username": other.username if other else None,
            "last_message": c.last_message,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "unread": unread,
        })

    return out


@router.get("/unread-count")
async def unread_total(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = (await db.execute(
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            or_(Conversation.buyer_id == user.id, Conversation.seller_id == user.id),
            Message.sender_id != user.id,
            Message.is_read == False,
        )
    )).scalar() or 0
    return {"count": count}


@router.get("/{conv_id}/messages")
async def get_messages(
    conv_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await db.get(Conversation, conv_id)
    if not conv or (conv.buyer_id != user.id and conv.seller_id != user.id):
        raise HTTPException(status_code=404, detail="Suhbat topilmadi")

    await db.execute(
        update(Message).where(
            Message.conversation_id == conv_id,
            Message.sender_id != user.id,
            Message.is_read == False,
        ).values(is_read=True)
    )

    result = await db.execute(
        select(Message, User.full_name)
        .join(User, Message.sender_id == User.id)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
    )

    listing = await db.get(Listing, conv.listing_id)

    return {
        "conversation_id": str(conv_id),
        "listing": {
            "id": str(conv.listing_id),
            "title": listing.category if listing else "—",
            "price": listing.price if listing else 0,
            "image": listing.image_urls[0] if listing and listing.image_urls else None,
        } if listing else None,
        "messages": [
            {
                "id": str(msg.id),
                "sender_id": str(msg.sender_id),
                "sender_name": name,
                "text": msg.text,
                "is_read": msg.is_read,
                "is_mine": msg.sender_id == user.id,
                "created_at": msg.created_at.isoformat(),
            }
            for msg, name in result.all()
        ],
    }


@router.post("/{conv_id}/messages")
async def send_message(
    conv_id: uuid.UUID,
    body: SendMessage,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await db.get(Conversation, conv_id)
    if not conv or (conv.buyer_id != user.id and conv.seller_id != user.id):
        raise HTTPException(status_code=404, detail="Suhbat topilmadi")

    msg = Message(conversation_id=conv_id, sender_id=user.id, text=body.text)
    db.add(msg)

    conv.last_message = body.text[:100]
    conv.last_message_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(msg)

    recipient_id = conv.seller_id if conv.buyer_id == user.id else conv.buyer_id
    recipient = await db.get(User, recipient_id)
    if recipient:
        from app.services.notification import _send
        WEB_APP = "https://onbozor.vercel.app"
        await _send(recipient.tg_id,
            f"💬 <b>Yangi xabar!</b>\n\n"
            f"👤 {user.full_name}: {body.text[:100]}",
            [[{"text": "💬 Javob berish", "web_app": {"url": f"{WEB_APP}/messages/{conv_id}"}}]],
        )

    return {
        "id": str(msg.id),
        "sender_id": str(user.id),
        "text": msg.text,
        "is_read": False,
        "is_mine": True,
        "created_at": msg.created_at.isoformat(),
    }


@router.put("/{conv_id}/read")
async def mark_read(
    conv_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Message).where(
            Message.conversation_id == conv_id,
            Message.sender_id != user.id,
            Message.is_read == False,
        ).values(is_read=True)
    )
    return {"status": "ok"}


def _conv_out(conv, user_id):
    return {
        "id": str(conv.id),
        "listing_id": str(conv.listing_id),
        "buyer_id": str(conv.buyer_id),
        "seller_id": str(conv.seller_id),
    }
