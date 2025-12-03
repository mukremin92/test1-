import json

from email_classifier import Email, classify_email


def test_finance_detection_prefers_finance_folder():
    email = Email(
        sender="billing@service.com",
        subject="Payment invoice for your plan",
        body="Your invoice is attached.",
    )
    result = classify_email(email)
    assert result["category"] == "Finans"
    assert result["action"] == "move"
    assert result["target_folder"] == "📁 Finans"


def test_newsletter_from_subject_keywords():
    email = Email(
        sender="updates@example.com",
        subject="October newsletter",
        body="Here is your monthly digest of updates.",
    )
    result = classify_email(email)
    assert result["category"] == "Bülten"
    assert result["target_folder"] == "📁 Bültenler"


def test_work_overrides_personal_when_task_present():
    email = Email(
        sender="alice@example.com",
        subject="Reminder",
        body="Please finish the report before the deadline tomorrow.",
        contacts=["alice@example.com"],
    )
    result = classify_email(email)
    assert result["category"] == "İş"
    assert result["target_folder"] == "📁 İş"


def test_spam_is_deleted():
    email = Email(
        sender="unknown@random.com",
        subject="Win money now!",
        body="Click here to claim your free gift.",
    )
    result = classify_email(email)
    assert result["category"] == "Spam / Gereksiz"
    assert result["action"] == "delete"


def test_review_needed_for_uncertain_content():
    email = Email(sender="", subject="", body="")
    result = classify_email(email)
    assert result["category"] == "İnceleme Gerekiyor"
    assert result["action"] == "review"
    assert result["target_folder"] == "none"


def test_cli_outputs_json(monkeypatch, capsys):
    args = [
        "email_classifier.py",
        "friend@example.com",
        "Catch up",
        "Let's grab coffee soon.",
        "--contacts",
        "friend@example.com",
    ]
    monkeypatch.setenv("PYTHONPATH", ".")
    monkeypatch.chdir(".")
    monkeypatch.setenv("LC_ALL", "C.UTF-8")
    import sys
    from email_classifier import _cli

    monkeypatch.setattr(sys, "argv", args)
    _cli()
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["category"] == "Kişisel"
    assert data["target_folder"] == "📁 Kişisel"


def test_classify_recent_with_mocked_imap(monkeypatch):
    # Arrange
    class DummyIMAP:
        def __init__(self, *_args, **_kwargs):
            self.logged_out = False

        def login(self, *_args, **_kwargs):
            return "OK", [b"Logged in"]

        def select(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def search(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def fetch(self, *_args, **_kwargs):
            raw_email = (
                b"From: billing@example.com\r\n"
                b"Subject: Payment receipt\r\n"
                b"\r\n"
                b"Here is your payment receipt."
            )
            return "OK", [(b"1 (RFC822 {100})", raw_email)]

        def logout(self):
            self.logged_out = True
            return "BYE", [b"Logged out"]

    monkeypatch.setenv("IMAP_HOST", "imap.example.com")
    monkeypatch.setenv("IMAP_USER", "user@example.com")
    monkeypatch.setenv("IMAP_PASSWORD", "secret")
    monkeypatch.setattr("imap_runner.imaplib.IMAP4_SSL", DummyIMAP)

    # Act
    from imap_runner import classify_recent

    results = classify_recent(limit=1)

    # Assert
    assert results
    entry = results[0]
    assert entry["result"]["category"] == "Finans"
    assert entry["result"]["action"] == "move"
    assert entry["result"]["target_folder"] == "📁 Finans"


def test_classify_recent_loads_env_file(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "IMAP_HOST=imap.example.com",
                "IMAP_USER=user@example.com",
                "IMAP_PASSWORD=secret",
            ]
        ),
        encoding="utf-8",
    )

    class DummyIMAP:
        def __init__(self, *_args, **_kwargs):
            self.logged_out = False

        def login(self, *_args, **_kwargs):
            return "OK", [b"Logged in"]

        def select(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def search(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def fetch(self, *_args, **_kwargs):
            raw_email = (
                b"From: billing@example.com\r\n"
                b"Subject: Payment receipt\r\n"
                b"\r\n"
                b"Here is your payment receipt."
            )
            return "OK", [(b"1 (RFC822 {100})", raw_email)]

        def logout(self):
            self.logged_out = True
            return "BYE", [b"Logged out"]

    # Ensure environment variables are absent so .env is required
    monkeypatch.delenv("IMAP_HOST", raising=False)
    monkeypatch.delenv("IMAP_USER", raising=False)
    monkeypatch.delenv("IMAP_PASSWORD", raising=False)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("imap_runner.imaplib.IMAP4_SSL", DummyIMAP)

    from imap_runner import classify_recent

    results = classify_recent(limit=1)

    assert results
    entry = results[0]
    assert entry["result"]["category"] == "Finans"
    assert entry["result"]["action"] == "move"
    assert entry["result"]["target_folder"] == "📁 Finans"


def test_classify_recent_with_custom_env_file(monkeypatch, tmp_path):
    env_file = tmp_path / "imap_credentials.env"
    env_file.write_text(
        "\n".join(
            [
                "IMAP_HOST=imap.example.com",
                "IMAP_USER=user@example.com",
                "IMAP_PASSWORD=secret",
            ]
        ),
        encoding="utf-8",
    )

    class DummyIMAP:
        def __init__(self, *_args, **_kwargs):
            self.logged_out = False

        def login(self, *_args, **_kwargs):
            return "OK", [b"Logged in"]

        def select(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def search(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def fetch(self, *_args, **_kwargs):
            raw_email = (
                b"From: billing@example.com\r\n"
                b"Subject: Payment receipt\r\n"
                b"\r\n"
                b"Here is your payment receipt."
            )
            return "OK", [(b"1 (RFC822 {100})", raw_email)]

        def logout(self):
            self.logged_out = True
            return "BYE", [b"Logged out"]

    monkeypatch.delenv("IMAP_HOST", raising=False)
    monkeypatch.delenv("IMAP_USER", raising=False)
    monkeypatch.delenv("IMAP_PASSWORD", raising=False)

    monkeypatch.setattr("imap_runner.imaplib.IMAP4_SSL", DummyIMAP)

    from imap_runner import classify_recent

    results = classify_recent(limit=1, env_path=str(env_file))

    assert results
    entry = results[0]
    assert entry["result"]["category"] == "Finans"
    assert entry["result"]["action"] == "move"
    assert entry["result"]["target_folder"] == "📁 Finans"
