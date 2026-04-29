from core.metrics import field_f1, exact_match


def test_field_f1_perfect_match():
    """Perfect match should return 1.0 for all fields."""
    pred = {"company": "Walmart", "date": "04/15/2024", "address": "123 Main St", "total": "6.48"}
    truth = {"company": "Walmart", "date": "04/15/2024", "address": "123 Main St", "total": "6.48"}
    scores = field_f1(pred, truth)
    assert scores["macro_f1"] == 1.0


def test_field_f1_no_match():
    """No match should return 0.0."""
    pred = {"company": "Target", "date": "01/01/2020", "address": "456 Oak Ave", "total": "99.99"}
    truth = {"company": "Walmart", "date": "04/15/2024", "address": "123 Main St", "total": "6.48"}
    scores = field_f1(pred, truth)
    assert scores["macro_f1"] == 0.0


def test_exact_match_true():
    """Exact match should return True when all fields match."""
    pred = {"company": "Walmart", "date": "04/15/2024", "address": "123 Main St", "total": "6.48"}
    truth = {"company": "Walmart", "date": "04/15/2024", "address": "123 Main St", "total": "6.48"}
    assert exact_match(pred, truth) is True


def test_exact_match_false():
    """Exact match should return False when any field differs."""
    pred = {"company": "Target", "date": "04/15/2024", "address": "123 Main St", "total": "6.48"}
    truth = {"company": "Walmart", "date": "04/15/2024", "address": "123 Main St", "total": "6.48"}
    assert exact_match(pred, truth) is False
