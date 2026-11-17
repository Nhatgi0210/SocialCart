"""Create synthetic customer and inbox records in the configured local MySQL."""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from shared.config import settings
from shared.db.models import Conversation, Customer, CustomerNote, Message, RealtimeOutbox
from shared.db.session import db_lifespan, get_session_factory


def demo_id(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"socialcart.local/inbox-demo/{key}"))


async def add_demo_message(content: str, thread: int):
    conversation_id = demo_id(f"conversation/1/{thread}")
    message_id = str(uuid4())
    async with db_lifespan(), get_session_factory().begin() as db:
        conversation = await db.get(Conversation, conversation_id, with_for_update=True)
        if conversation is None:
            raise SystemExit("Run seed-inbox-demo.py first to create demo conversations")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(Message(id=message_id, conversation_id=conversation_id, platform=conversation.platform,
                       platform_account_id=conversation.platform_account_id, platform_msg_id=message_id,
                       sender="CUSTOMER", content=content, status="SENT", created_at=now))
        conversation.is_read = False
        conversation.version += 1
        conversation.ai_generation += 1
        conversation.last_message_at = now
        db.add(RealtimeOutbox(event_type="message:new", data={
            "conversation_id": conversation_id, "message_id": message_id,
        }))
    print(f"Demo message committed: {message_id} (conversation {conversation_id})")


async def main(message: str | None = None, thread: int = 2):
    if settings.app_env != "local":
        raise SystemExit("Inbox demo requires APP_ENV=local")
    if message is not None:
        await add_demo_message(message, thread)
        return

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with db_lifespan(), get_session_factory().begin() as db:
        for index, (name, platform) in enumerate((
            ("Lan", "FACEBOOK"), ("Minh", "ZALO"), ("An", "FACEBOOK"),
        )):
            customer_id = demo_id(f"customer/{index}")
            account = f"socialcart-demo-{platform.lower()}"
            if await db.get(Customer, customer_id) is None:
                db.add(Customer(id=customer_id, platform=platform, platform_account_id=account,
                                platform_user_id=f"socialcart-demo-user-{index}", display_name=f"[Demo] {name}"))
                await db.flush()
                db.add(CustomerNote(id=demo_id(f"note/{index}"), customer_id=customer_id,
                                    content="Ghi chú mẫu dùng để kiểm thử trên máy local."))
            for thread in range(4):
                key = f"{index}/{thread}"
                conversation_id = demo_id(f"conversation/{key}")
                if await db.get(Conversation, conversation_id) is not None:
                    continue
                latest = now - timedelta(hours=index * 4 + thread)
                count = 22 if index == thread == 0 else 2
                db.add(Conversation(
                    id=conversation_id, platform=platform, platform_account_id=account,
                    platform_chat_id=f"socialcart-demo-chat-{key}", customer_id=customer_id,
                    status=("NEW", "IN_PROGRESS", "RESOLVED", "NEW")[thread],
                    ai_status=("NEEDS_SELLER", "AI_HANDLING", "SELLER_HANDLING", "AI_HANDLING")[thread],
                    is_read=thread == 2, created_at=latest - timedelta(minutes=count), last_message_at=latest,
                ))
                await db.flush()
                for position in range(count):
                    db.add(Message(
                        id=demo_id(f"message/{key}/{position}"), conversation_id=conversation_id,
                        platform=platform, platform_account_id=account,
                        platform_msg_id=f"socialcart-demo-msg-{key}-{position}", status="SENT",
                        sender=("CUSTOMER", "AI", "SELLER")[position % 3],
                        content=("Shop có áo size M không?", "Shop sẽ kiểm tra size cho bạn.", "Mình sẽ kiểm tra và phản hồi nhé.")[position % 3],
                        created_at=latest - timedelta(minutes=count - position - 1),
                    ))
    print("Demo inbox ready: 3 customers, 12 conversations. Existing records were preserved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", help="Commit a simulated incoming message in a [Demo] Minh conversation")
    parser.add_argument("--thread", type=int, choices=range(4), default=2, help="Demo conversation index")
    options = parser.parse_args()
    if options.message is not None and not 1 <= len(options.message.strip()) <= 10000:
        parser.error("--message requires 1–10000 characters")
    asyncio.run(main(options.message.strip() if options.message is not None else None, options.thread))
