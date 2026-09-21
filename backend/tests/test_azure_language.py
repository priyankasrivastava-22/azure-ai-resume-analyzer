from unittest.mock import MagicMock, patch

from analyzer.azure_language import (
    analyze_text_with_azure,
    chunk_text,
    extract_key_phrases,
    recognize_entities,
)


def test_chunk_text_returns_single_chunk_for_short_text():
    text = "Python Azure Docker"

    result = chunk_text(text, max_length=100)

    assert result == [text]


def test_chunk_text_splits_long_text():
    text = "A" * 250

    result = chunk_text(text, max_length=100)

    assert len(result) == 3
    assert all(len(chunk) <= 100 for chunk in result)


def test_extract_key_phrases_uses_mocked_azure_client():
    fake_document = MagicMock()
    fake_document.is_error = False
    fake_document.key_phrases = [
        "DevOps Engineer",
        "Azure",
        "Python",
    ]

    fake_client = MagicMock()
    fake_client.extract_key_phrases.return_value = [
        fake_document
    ]

    with patch(
        "analyzer.azure_language.get_azure_language_client",
        return_value=fake_client,
    ):
        result = extract_key_phrases(
            "DevOps Engineer with Azure and Python."
        )

    assert "DevOps Engineer" in result
    assert "Azure" in result
    assert "Python" in result


def test_recognize_entities_uses_mocked_azure_client():
    fake_entity = MagicMock()
    fake_entity.text = "Azure"
    fake_entity.category = "Product"
    fake_entity.subcategory = None
    fake_entity.confidence_score = 0.99

    fake_document = MagicMock()
    fake_document.is_error = False
    fake_document.entities = [
        fake_entity
    ]

    fake_client = MagicMock()
    fake_client.recognize_entities.return_value = [
        fake_document
    ]

    with patch(
        "analyzer.azure_language.get_azure_language_client",
        return_value=fake_client,
    ):
        result = recognize_entities(
            "Experience with Azure."
        )

    assert len(result) == 1
    assert result[0]["text"] == "Azure"
    assert result[0]["category"] == "Product"
    assert result[0]["confidence_score"] == 0.99


def test_analyze_text_with_azure_combines_results():
    with patch(
        "analyzer.azure_language.extract_key_phrases",
        return_value=[
            "Azure",
            "Python",
        ],
    ), patch(
        "analyzer.azure_language.recognize_entities",
        return_value=[
            {
                "text": "Azure",
                "category": "Product",
                "subcategory": None,
                "confidence_score": 0.99,
            }
        ],
    ):
        result = analyze_text_with_azure(
            "Azure Python Engineer"
        )

    assert result["key_phrases"] == [
        "Azure",
        "Python",
    ]

    assert len(result["entities"]) == 1
    assert result["entities"][0]["text"] == "Azure"


def test_analyze_text_with_azure_does_not_require_live_azure():
    with patch(
        "analyzer.azure_language.extract_key_phrases",
        return_value=[],
    ), patch(
        "analyzer.azure_language.recognize_entities",
        return_value=[],
    ):
        result = analyze_text_with_azure(
            "Any resume or JD text"
        )

    assert result == {
        "key_phrases": [],
        "entities": [],
    }