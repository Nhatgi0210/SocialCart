"""Report local provider prerequisites without printing credentials."""
import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-gemini", action="store_true", help="List model metadata using the configured API key")
    args = parser.parse_args()
    groups = {
        "Shared": ("ENCRYPTION_KEY", "INTERNAL_SERVICE_TOKEN", "PUBLIC_API_URL", "FRONTEND_URL"),
        "Facebook": ("FB_APP_ID", "FB_APP_SECRET", "FB_PAGE_ID", "FB_GRAPH_VERSION", "FB_WEBHOOK_VERIFY_TOKEN"),
        "Zalo": ("ZALO_APP_ID", "ZALO_APP_SECRET", "ZALO_OA_ID", "ZALO_WEBHOOK_SECRET", "ZALO_AUTHORIZATION_URL"),
        "Gemini": ("GEMINI_API_KEY", "GEMINI_MODEL"),
    }
    for group, names in groups.items():
        missing = [name for name in names if not os.getenv(name)]
        print(group + ": " + ("configured" if not missing else "missing " + ", ".join(missing)))
    try:
        valid_key = len(bytes.fromhex(os.getenv("ENCRYPTION_KEY", ""))) == 32
    except ValueError:
        valid_key = False
    print("ENCRYPTION_KEY format valid:", valid_key)
    public = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
    print("Live HTTPS callback:", urlsplit(public).scheme == "https")
    for platform in ("facebook", "zalo"):
        print(platform + " callback:", public + "/api/v1/connections/" + platform + "/oauth/callback")
        print(platform + " webhook:", public + "/webhooks/" + platform)
    if args.check_gemini:
        key, model = os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_MODEL")
        if not key or not model:
            raise SystemExit("Set GEMINI_API_KEY and GEMINI_MODEL first")
        try:
            response = httpx.get("https://generativelanguage.googleapis.com/v1beta/models/" + model.removeprefix("models/"),
                                 headers={"x-goog-api-key": key}, timeout=10)
            if not response.is_success:
                raise SystemExit(f"Gemini metadata check failed (HTTP {response.status_code})")
            methods = response.json().get("supportedGenerationMethods", [])
            print("Configured Gemini model supports generateContent:", "generateContent" in methods)
        except httpx.HTTPError:
            raise SystemExit("Gemini metadata could not be reached") from None
        print("Metadata only. Structured output, latency and billing need a separate model smoke test.")


if __name__ == "__main__":
    main()
