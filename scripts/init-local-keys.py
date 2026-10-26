"""
scripts/init-local-keys.py — Tạo cặp RSA key cho JWT RS256.

Chạy: python scripts/init-local-keys.py
- Tạo keys/private.pem và keys/public.pem nếu CHƯA tồn tại
- KHÔNG ghi đè key hiện tại (bảo toàn DB token đã ký)
- Key không commit vào Git (xem .gitignore)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        print("ERROR: Cần cài package 'cryptography'. Chạy:")
        print("  pip install cryptography")
        sys.exit(1)

    # Xác định thư mục keys/ ở root repo (script chạy từ root)
    repo_root = Path(__file__).parent.parent
    keys_dir = repo_root / "keys"
    private_key_path = keys_dir / "private.pem"
    public_key_path = keys_dir / "public.pem"

    keys_dir.mkdir(exist_ok=True)

    if private_key_path.exists() or public_key_path.exists():
        print("INFO: Key đã tồn tại — không ghi đè.")
        print(f"  private: {private_key_path}")
        print(f"  public:  {public_key_path}")
        print("Xóa thủ công nếu cần tạo lại (lưu ý: token DB cũ sẽ không hợp lệ).")
        return

    print("Đang tạo RSA 2048-bit key pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Ghi private key (PEM, PKCS8, không mã hóa)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key_path.write_bytes(private_pem)

    # Ghi public key
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_key_path.write_bytes(public_pem)

    # Đặt permission chặt cho private key (Unix; Windows bỏ qua lỗi)
    try:
        os.chmod(private_key_path, 0o600)
    except OSError:
        pass  # Windows không hỗ trợ chmod — OK cho dev local

    print(f"OK: Đã tạo {private_key_path}")
    print(f"OK: Đã tạo {public_key_path}")
    print("CẢNH BÁO: Không commit keys/ vào Git!")


if __name__ == "__main__":
    main()
