from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError

from shared.auth import AuthError, unavailable
from shared.config import settings
from shared.product_images import IMAGE_FILENAME, IMAGE_MAX_BYTES

FORMATS = {"JPEG": ("jpg", "image/jpeg"), "PNG": ("png", "image/png"), "WEBP": ("webp", "image/webp")}
MAX_PIXELS = 16_000_000


def save_image(content: bytes, content_type: str | None) -> str:
    if len(content) > IMAGE_MAX_BYTES:
        raise AuthError(413, "IMAGE_TOO_LARGE", "Ảnh được giới hạn ở 5 MiB")
    try:
        with Image.open(BytesIO(content), formats=list(FORMATS)) as source:
            image_format = source.format
            extension, mime = FORMATS[image_format]
            if content_type != mime or source.width * source.height > MAX_PIXELS:
                raise AuthError(422, "VALIDATION_ERROR", "Định dạng hoặc kích thước ảnh không hợp lệ")
            source.load()
            image = ImageOps.exif_transpose(source)
            image.info.clear()
            encoded = BytesIO()
            image.save(encoded, format=image_format)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError, SyntaxError):
        raise AuthError(422, "VALIDATION_ERROR", "Tệp phải là ảnh JPEG, PNG hoặc WebP hợp lệ") from None
    if encoded.tell() > IMAGE_MAX_BYTES:
        raise AuthError(413, "IMAGE_TOO_LARGE", "Ảnh sau xử lý vượt 5 MiB")

    directory = Path(settings.product_image_dir)
    filename = f"{uuid4().hex}.{extension}"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / filename).open("xb") as file:
            file.write(encoded.getbuffer())
    except OSError:
        raise unavailable() from None
    return f"{settings.product_image_public_base_url.rstrip('/')}/{filename}"


def read_image(filename: str):
    path = Path(settings.product_image_dir) / filename
    if not IMAGE_FILENAME.fullmatch(filename) or path.is_symlink() or not path.is_file():
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy ảnh")
    return FileResponse(path, headers={"X-Content-Type-Options": "nosniff"})
