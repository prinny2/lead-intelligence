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

    def test_returns_none_for_empty_string(self) -> None:
        self.assertIsNone(extract_first_json(""))

    def test_returns_none_for_whitespace_only(self) -> None:
        self.assertIsNone(extract_first_json("   \n\t  "))

    def test_handles_escaped_quotes_in_string_values(self) -> None:
        raw = r'{"score": 5, "urgency": "media", "recommendation": "ele disse \"ok\""}'
        result = extract_first_json(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 5)
        self.assertIn("ok", result["recommendation"])

    def test_handles_backslash_escape_in_string_values(self) -> None:
        raw = r'{"score": 4, "urgency": "baixa", "recommendation": "caminho: C:\\Users\\test"}'
        result = extract_first_json(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 4)

    def test_strips_code_fence_without_json_specifier(self) -> None:
        raw = '```\n{"score": 6, "urgency": "media", "recommendation": "follow up"}\n```'
        result = extract_first_json(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 6)

    def test_returns_none_when_candidate_is_not_a_dict(self) -> None:
        # Bracket matching will find {}, but json.loads on an array prefix
        # We produce text that contains no {…} at all, only an array
        self.assertIsNone(extract_first_json("[1, 2, 3]"))

    def test_skips_invalid_candidate_and_returns_next_valid(self) -> None:
        # First { } block is bracket-matched but not valid JSON; second is valid
        raw = "{invalid: true} then {\"score\": 2, \"urgency\": \"baixa\", \"recommendation\": \"x\"}"
        result = extract_first_json(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 2)

    def test_returns_none_when_no_complete_object_found(self) -> None:
        self.assertIsNone(extract_first_json('{"score": 7, "urgency": "alta"'))


if __name__ == "__main__":
    unittest.main()
