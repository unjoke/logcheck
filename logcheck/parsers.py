from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import unquote_plus, urlsplit

from .models import Event


IP_RE = r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
IP_SEARCH_RE = re.compile(IP_RE)
LINUX_AUTH_RE = re.compile(
    rf"^(?P<month>\w{{3}})\s+(?P<day>\d{{1,2}})\s+(?P<time>\d{{2}}:\d{{2}}:\d{{2}})\s+"
    rf"(?P<host>\S+)\s+(?P<service>\S+?):\s+(?P<message>.*)$",
    re.IGNORECASE,
)
APP_RE = re.compile(
    rf"^(?P<date>\d{{4}}-\d{{2}}-\d{{2}})\s+(?P<time>\d{{2}}:\d{{2}}:\d{{2}})\s+"
    rf"(?P<level>\w+)\s+(?P<message>.*)$",
    re.IGNORECASE,
)
ACCESS_RE = re.compile(
    rf"^(?P<ip>\d{{1,3}}(?:\.\d{{1,3}}){{3}})\s+\S+\s+\S+\s+\[(?P<access_time>[^\]]+)\]\s+"
    rf'"(?P<method>[A-Z]+)\s+(?P<request>\S+)\s+HTTP/[0-9.]+"\s+'
    rf"(?P<status>\d{{3}})\s+(?P<size>\S+)"
    rf'(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?',
    re.IGNORECASE,
)
USER_PATTERNS = (
    re.compile(r"invalid user\s+(?P<user>[A-Za-z0-9_.-]+)", re.IGNORECASE),
    re.compile(r"user=(?P<user>[A-Za-z0-9_.-]+)", re.IGNORECASE),
    re.compile(r"for\s+(?P<user>[A-Za-z0-9_.-]+)", re.IGNORECASE),
)


def _extract_actor(message: str) -> str | None:
    for pattern in USER_PATTERNS:
        match = pattern.search(message)
        if match:
            return match.group("user")
    return None


def _extract_ip(line: str) -> str | None:
    match = IP_SEARCH_RE.search(line)
    return match.group("ip") if match else None


def parse_line(source_file: str, line_number: int, raw_line: str) -> Event:
    line = raw_line.rstrip("\n")

    linux_match = LINUX_AUTH_RE.match(line)
    if linux_match:
        message = linux_match.group("message")
        return Event(
            source_file=source_file,
            line_number=line_number,
            raw_line=line,
            category="auth",
            actor=_extract_actor(line),
            source_address=_extract_ip(line),
            message=message,
        )

    app_match = APP_RE.match(line)
    if app_match:
        message = app_match.group("message")
        return Event(
            source_file=source_file,
            line_number=line_number,
            raw_line=line,
            category="application",
            actor=_extract_actor(line),
            source_address=_extract_ip(line),
            message=message,
        )

    access_match = ACCESS_RE.match(line)
    if access_match:
        request = access_match.group("request")
        target = urlsplit(request).path or request
        size_text = access_match.group("size")
        metadata = {
            "method": access_match.group("method").upper(),
            "request": request,
            "decoded_request": unquote_plus(request),
            "path": target,
            "status_code": int(access_match.group("status")),
            "response_size": int(size_text) if size_text.isdigit() else None,
            "referrer": access_match.group("referrer") or None,
            "user_agent": access_match.group("user_agent") or None,
        }
        return Event(
            source_file=source_file,
            line_number=line_number,
            raw_line=line,
            category="access",
            target=target,
            source_address=access_match.group("ip"),
            message=request,
            metadata=metadata,
        )

    return Event(source_file=source_file, line_number=line_number, raw_line=line)


def parse_files(paths: list[Path]) -> list[Event]:
    events: list[Event] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(str(path))
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                events.append(parse_line(str(path), line_number, line))
    return events
