from logcheck.ip_context import classify_ip_address
from logcheck.parsers import parse_line


def test_classify_private_address_as_non_global():
    context = classify_ip_address("192.168.2.1")

    assert context.is_valid is True
    assert context.is_global is False
    assert context.category == "private"
    assert "private" in context.reason.lower()


def test_classify_documentation_address_as_non_global():
    context = classify_ip_address("203.0.113.10")

    assert context.is_valid is True
    assert context.is_global is False
    assert context.category == "documentation"
    assert "documentation" in context.reason.lower()


def test_classify_public_address_as_global():
    context = classify_ip_address("8.8.8.8")

    assert context.is_valid is True
    assert context.is_global is True
    assert context.category == "global"
    assert "globally routable" in context.reason.lower()


def test_classify_invalid_address_returns_stable_context():
    context = classify_ip_address("999.1.1.1")

    assert context.is_valid is False
    assert context.is_global is False
    assert context.category == "invalid"


def test_parse_line_preserves_source_address_context_metadata():
    event = parse_line(
        "access.log",
        1,
        '8.8.8.8 - - [01/Sep/2021:01:37:25 +0000] "GET /index.php HTTP/1.1" 200 512',
    )

    assert event.metadata["source_address_context"]["address"] == "8.8.8.8"
    assert event.metadata["source_address_context"]["category"] == "global"
    assert event.metadata["source_address_context"]["is_global"] is True
