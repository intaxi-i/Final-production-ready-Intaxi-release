from app.core.protected_values import mask_card, preview_value, protect_value, unprotect_value


def test_protect_value_roundtrip_and_not_plaintext():
    key = "strong-test-key-for-intaxi"
    raw = "8600123412341234"
    protected = protect_value(raw, key=key)
    assert protected
    assert protected != raw
    assert raw not in protected
    assert unprotect_value(protected, key=key) == raw


def test_mask_card():
    assert mask_card("8600 1234 5678 9999") == "8600********9999"
    assert mask_card(None) is None


def test_preview_value():
    assert preview_value("TRC20ADDRESS123456", left=4, right=4) == "TRC2...3456"
    assert preview_value(None) is None
