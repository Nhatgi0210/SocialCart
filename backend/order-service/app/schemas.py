from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

MAX_INT = 2147483647
MAX_QUANTITY = 1_000_000
OrderStatus = Literal["PENDING", "CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED"]
Version = Annotated[int, Field(strict=True, ge=1, le=MAX_INT)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Phone = Annotated[str, StringConstraints(pattern=r"^[0-9]{10,11}$")]
Address = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Note = Annotated[str, StringConstraints(max_length=5000)]


class OrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ItemInput(OrderInput):
    variant_id: UUID
    quantity: Annotated[int, Field(strict=True, ge=1, le=MAX_QUANTITY)]


Items = Annotated[list[ItemInput], Field(min_length=1)]


class CreateOrder(OrderInput):
    customer_id: UUID
    conversation_id: UUID
    customer_name: Name
    phone_number: Phone
    address: Address
    note: Note = ""
    items: Items


class EditOrder(OrderInput):
    expected_version: Version
    customer_name: Name | None = None
    phone_number: Phone | None = None
    address: Address | None = None
    note: Note | None = None
    items: Items | None = None

    @model_validator(mode="after")
    def check_fields(self):
        changes = self.model_fields_set - {"expected_version"}
        if not changes or any(getattr(self, field) is None for field in changes):
            raise ValueError("Provide at least one editable field")
        return self


class ChangeStatus(OrderInput):
    expected_version: Version
    status: Literal["CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED"]
