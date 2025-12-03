from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Email:
    sender: str
    subject: str
    body: str
    contacts: Optional[List[str]] = None


CATEGORY_LABELS_TR = {
    "Important": "Önemli",
    "Work": "İş",
    "Personal": "Kişisel",
    "Finance": "Finans",
    "Notification": "Bildirim",
    "Marketing / Promotion": "Pazarlama / Promosyon",
    "Newsletter": "Bülten",
    "Spam / Junk": "Spam / Gereksiz",
    "Review Needed": "İnceleme Gerekiyor",
}

CATEGORY_FOLDERS_TR = {
    "Important": "📁 Önemli",
    "Work": "📁 İş",
    "Personal": "📁 Kişisel",
    "Finance": "📁 Finans",
    "Notification": "📁 Bildirimler",
    "Marketing / Promotion": "📁 Promosyonlar",
    "Newsletter": "📁 Bültenler",
    "Spam / Junk": None,
    "Review Needed": None,
}


FINANCE_TERMS = {
    "invoice",
    "payment",
    "bank",
    "bill",
    "due",
    "subscription",
    "receipt",
    "tax",
}

WORK_HINTS = {"task", "deadline", "due", "instruction", "deliverable", "action required"}
MARKETING_HINTS = {"sale", "discount", "offer", "coupon", "deal", "affiliate", "buy now"}
NEWSLETTER_HINTS = {"unsubscribe", "newsletter", "digest"}
SPAM_HINTS = {"win money", "lottery", "free gift", "click here", "urgent reply", "claim now"}


def normalize(text: str) -> str:
    return text.lower()


def detect_finance(text: str) -> bool:
    lower_text = normalize(text)
    return any(term in lower_text for term in FINANCE_TERMS)


def detect_newsletter(text: str) -> bool:
    lower_text = normalize(text)
    return any(term in lower_text for term in NEWSLETTER_HINTS)


def detect_marketing(text: str) -> bool:
    lower_text = normalize(text)
    return any(term in lower_text for term in MARKETING_HINTS)


def detect_spam(text: str) -> bool:
    lower_text = normalize(text)
    return any(term in lower_text for term in SPAM_HINTS)


def detect_work(text: str) -> bool:
    lower_text = normalize(text)
    return any(term in lower_text for term in WORK_HINTS)


def summarize(body: str) -> str:
    if not body:
        return "İçerik belirtilmedi."
    sentences = [segment.strip() for segment in body.split(".") if segment.strip()]
    if sentences:
        return sentences[0] + "."
    return body[:120]


def classify_email(email: Email) -> dict:
    sender = email.sender or ""
    subject = email.subject or ""
    body = email.body or ""
    contacts = set(email.contacts or [])

    combined_text = " ".join([sender, subject, body])
    category = "Review Needed"
    confidence = 0.4

    if detect_spam(combined_text):
        category = "Spam / Junk"
        confidence = 0.9
    elif detect_finance(sender) or detect_finance(subject):
        category = "Finance"
        confidence = 0.9
    elif detect_work(combined_text):
        category = "Work"
        confidence = 0.85
    elif sender in contacts:
        category = "Personal"
        confidence = 0.8
    elif detect_marketing(combined_text):
        category = "Marketing / Promotion"
        confidence = 0.8
    elif detect_newsletter(subject):
        category = "Newsletter"
        confidence = 0.8

    action = "review"
    target_folder = "none"

    if category == "Spam / Junk":
        action = "delete"
    elif category == "Review Needed":
        action = "review"
    else:
        action = "move"
        target_folder = CATEGORY_FOLDERS_TR.get(category, "none") or "none"

    # Ensure low-confidence results trigger a review
    if confidence < 0.5:
        category = "Review Needed"
        action = "review"
        target_folder = "none"

    localized_category = CATEGORY_LABELS_TR.get(category, category)
    return {
        "category": localized_category,
        "confidence": f"{confidence:.2f}",
        "action": action,
        "target_folder": target_folder,
        "summary": summarize(body),
    }


def _cli() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Classify an email according to predefined rules.")
    parser.add_argument("sender", help="Gönderen")
    parser.add_argument("subject", help="Konu")
    parser.add_argument("body", help="İçerik")
    parser.add_argument("--contacts", nargs="*", default=[], help="Kişi listesi (kişisel göndericiler)")
    args = parser.parse_args()

    email = Email(sender=args.sender, subject=args.subject, body=args.body, contacts=args.contacts)
    result = classify_email(email)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
