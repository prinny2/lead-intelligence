import unittest

from app.utils.json_parser import extract_first_json


class JsonParserTests(unittest.TestCase):
    def test_extracts_json_from_markdown_fence(self) -> None:
        raw = '```json\n{"score": 7, "urgency": "media", "recommendation": "ok"}\n```'
        self.assertEqual(
            extract_first_json(raw),
            {"score": 7, "urgency": "media", "recommendation": "ok"},
        )

    def test_extracts_first_valid_json_when_more_text_follows(self) -> None:
        raw = '{"score": 1, "urgency": "baixa", "recommendation": "x"} trailing {"ignored": true}'
        self.assertEqual(
            extract_first_json(raw),
            {"score": 1, "urgency": "baixa", "recommendation": "x"},
        )

    def test_returns_none_for_invalid_json(self) -> None:
        self.assertIsNone(extract_first_json("not json at all"))


if __name__ == "__main__":
    unittest.main()
