from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, TypeAdapter, field_validator, model_validator

MAX_INT = 2147483647
ProductStatus = Literal["ACTIVE", "INACTIVE"]
ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
VariantName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Price = Annotated[int, Field(strict=True, ge=1, le=MAX_INT)]
Stock = Annotated[int, Field(strict=True, ge=0, le=MAX_INT)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]
ImageURL = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
http_url = TypeAdapter(HttpUrl)


class VariantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: VariantName
    price: Price
    stock: Stock
    low_stock_threshold: Stock = 0


class VariantUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: Price
    name: VariantName | None = None
    price: Price | None = None
    stock: Stock | None = None
    low_stock_threshold: Stock | None = None

    @model_validator(mode="after")
    def require_edit(self):
        edits = self.model_dump(exclude_unset=True, exclude={"expected_version"})
        if not edits or any(value is None for value in edits.values()):
            raise ValueError("Provide at least one editable variant field")
        return self


class ProductFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Description | None = None
    image_url: ImageURL | None = None

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value):
        if value is not None:
            http_url.validate_python(value)
        return value


class ProductCreate(ProductFields):
    name: ProductName
    variants: Annotated[list[VariantInput], Field(min_length=1)]

    @model_validator(mode="after")
    def nonnull_create_fields(self):
        for field in ("description", "image_url"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} may be omitted but cannot be null on create")
        return self


class ProductUpdate(ProductFields):
    name: ProductName | None = None
    status: ProductStatus | None = None

    @model_validator(mode="after")
    def require_edit(self):
        if not self.model_fields_set or any(
            field in self.model_fields_set and getattr(self, field) is None
            for field in ("name", "description", "status")
        ):
            raise ValueError("Provide at least one editable product field")
        return self
