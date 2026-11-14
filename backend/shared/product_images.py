import re

IMAGE_MAX_BYTES = 5 * 1024 * 1024
# Allow space for a normal multipart envelope while bounding the buffered request.
IMAGE_REQUEST_MAX_BYTES = IMAGE_MAX_BYTES + 64 * 1024
IMAGE_FILENAME = re.compile(r"[0-9a-f]{32}\.(?:jpg|png|webp)")
IMAGE_ROUTE = "/api/v1/products/images"
