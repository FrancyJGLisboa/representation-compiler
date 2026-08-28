"""Source adapters. Credentials are read only from environment variables."""
from __future__ import annotations

import email
import json
import os
from dataclasses import dataclass
from email import policy
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class SourceMaterial:
    id: str
    text: str
    origin: str
    locator: str
    warnings: tuple[str, ...] = ()


def local_file(path: str | Path) -> SourceMaterial:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json"}:
        return SourceMaterial(f"file-{path.stem}", path.read_text(encoding="utf-8"), "file", str(path))
    if suffix == ".eml":
        message = email.message_from_bytes(path.read_bytes(), policy=policy.default)
        body = "\n".join(part.get_content() for part in message.walk() if part.get_content_type() == "text/plain" and not part.is_attachment())
        header = f"From: {message.get('From', '')}\nTo: {message.get('To', '')}\nSubject: {message.get('Subject', '')}\nDate: {message.get('Date', '')}"
        return SourceMaterial(f"email-{path.stem}", f"{header}\n\n{body}", "email", str(path))
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError("PDF ingestion needs pypdf: python3 -m pip install pypdf") from error
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF: decrypt it locally before ingestion")
        pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
        text = "\n\n".join(pages).strip()
        warnings = ("No selectable text found; OCR is required before reliable extraction.",) if not text else ()
        return SourceMaterial(f"pdf-{path.stem}", text, "pdf", str(path), warnings)
    raise ValueError(f"Unsupported local source type: {suffix}")


def slack_channel(channel_id: str, limit: int = 15) -> SourceMaterial:
    payload = _get("https://slack.com/api/conversations.history?" + urlencode({"channel": channel_id, "limit": limit}), "SLACK_BOT_TOKEN")
    if not payload.get("ok"):
        raise RuntimeError(f"Slack rejected request: {payload.get('error', 'unknown error')}")
    text = "\n".join(f"[{item.get('ts', '')}] {item.get('user', 'unknown')}: {item.get('text', '')}" for item in reversed(payload.get("messages", [])))
    return SourceMaterial(f"slack-{channel_id}", text, "slack", f"channel:{channel_id}")


def notion_page(page_id: str) -> SourceMaterial:
    blocks = _get(f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100", "NOTION_API_KEY", {"Notion-Version": "2025-09-03"})
    text = "\n".join(_notion_text(block) for block in blocks.get("results", []) if _notion_text(block))
    return SourceMaterial(f"notion-{page_id}", text, "notion", f"page:{page_id}")


def drive_file(file_id: str, export_mime: str | None = None) -> SourceMaterial:
    """Download a Drive blob, or export a Google Workspace document as plain text."""
    if export_mime:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?" + urlencode({"mimeType": export_mime})
    else:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    data = _bytes(url, "GOOGLE_DRIVE_ACCESS_TOKEN")
    return SourceMaterial(f"drive-{file_id}", data.decode("utf-8", errors="replace"), "google-drive", f"file:{file_id}")


def jira_issue(base_url: str, issue_key: str) -> SourceMaterial:
    payload = _get(f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}", "JIRA_API_TOKEN", {"Accept": "application/json"})
    fields = payload.get("fields", {})
    text = f"Issue: {payload.get('key', issue_key)}\nSummary: {fields.get('summary', '')}\nStatus: {fields.get('status', {}).get('name', '')}\nDescription: {fields.get('description', '')}"
    return SourceMaterial(f"jira-{issue_key}", text, "jira", f"issue:{issue_key}")


def _get(url: str, token_env: str, headers: dict[str, str] | None = None) -> dict:
    return json.loads(_bytes(url, token_env, headers))


def _bytes(url: str, token_env: str, headers: dict[str, str] | None = None) -> bytes:
    token = os.getenv(token_env)
    if not token:
        raise RuntimeError(f"{token_env} is required for this connector")
    request = Request(url, headers={"Authorization": f"Bearer {token}", **(headers or {})})
    with urlopen(request, timeout=20) as response:
        return response.read()


def _notion_text(block: dict) -> str:
    value = block.get(block.get("type", ""), {})
    return "".join(part.get("plain_text", "") for part in value.get("rich_text", []))
