from __future__ import annotations

import imaplib
import json
import os
from email import message_from_bytes
from email.header import decode_header, make_header
from typing import List

from email_classifier import Email, classify_email


class MissingConfigurationError(Exception):
    """Raised when required IMAP environment variables are missing."""


REQUIRED_ENV_VARS = ["IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"]


def load_dotenv(path: str = ".env") -> None:
    """Load IMAP_* values from a .env file if present.

    This is a minimal loader to avoid external dependencies. Only lines with
    the pattern KEY=VALUE are parsed; comments (#) and empty lines are ignored.
    Existing environment variables are not overwritten.
    """

    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip()


def _ensure_configuration(env_path: str = ".env") -> None:
    # Try loading defaults from a local .env file before validating.
    load_dotenv(env_path)

    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        joined = ", ".join(missing)
        raise MissingConfigurationError(
            f"Aşağıdaki ortam değişkenleri eksik: {joined}."
        )


def decode_header_value(value: str) -> str:
    if not value:
        return ""
    return str(make_header(decode_header(value)))


def extract_body_text(message) -> str:
    if message.is_multipart():
        parts: List[str] = []
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    parts.append(payload.decode(charset, errors="replace"))
                except LookupError:
                    parts.append(payload.decode("utf-8", errors="replace"))
        return "\n".join(parts).strip()

    payload = message.get_payload(decode=True) or b""
    charset = message.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def message_to_email(message) -> Email:
    sender = decode_header_value(message.get("From", ""))
    subject = decode_header_value(message.get("Subject", ""))
    body = extract_body_text(message)
    return Email(sender=sender, subject=subject, body=body)


def classify_recent(limit: int = 5, env_path: str = ".env") -> list[dict]:
    _ensure_configuration(env_path)

    host = os.environ["IMAP_HOST"]
    user = os.environ["IMAP_USER"]
    password = os.environ["IMAP_PASSWORD"]

    imap = imaplib.IMAP4_SSL(host)
    try:
        imap.login(user, password)
        imap.select("INBOX")
        status, data = imap.search(None, "ALL")
        if status != "OK":
            return []

        message_ids = data[0].split()
        if not message_ids:
            return []

        latest_ids = message_ids[-limit:]
        results = []

        for msg_id in reversed(latest_ids):
            status, msg_data = imap.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data:
                continue

            raw_email = msg_data[0][1]
            message = message_from_bytes(raw_email)
            email_obj = message_to_email(message)
            classification = classify_email(email_obj)
            results.append({
                "id": msg_id.decode(),
                "email": {
                    "sender": email_obj.sender,
                    "subject": email_obj.subject,
                    "body": email_obj.body,
                },
                "result": classification,
            })
        return results
    finally:
        imap.logout()


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "IMAP posta kutusundaki son e-postaları çekip sınıflandırır. "
            "IMAP_HOST, IMAP_USER ve IMAP_PASSWORD ortam değişkenlerini ayarladığınızdan emin olun."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Sınıflandırılacak son e-posta sayısı (varsayılan 5)",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Kimlik bilgilerini içeren .env dosyasının yolu (varsayılan: .env)",
    )
    args = parser.parse_args()

    try:
        results = classify_recent(limit=args.limit, env_path=args.env_file)
    except MissingConfigurationError as exc:
        print(str(exc))
        return

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
