"""Create synthetic customer and inbox records in the configured local MySQL."""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from shared.config import settings
from shared.db.models import Conversation, Customer, CustomerNote, Message
from shared.db.session import db_lifespan, get_session_factory


def demo_id(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"socialcart.local/inbox-demo/{key}"))


async def main():
    if settings.app_env != "local":
        raise SystemExit("Inbox demo requires APP_ENV=local")

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
    asyncio.run(main())
