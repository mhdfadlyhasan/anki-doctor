import unittest

from ankidoctor import prompt


class DescribeFieldTest(unittest.TestCase):
    def test_reading(self):
        self.assertIn("hiragana reading", prompt.describe_field("Reading"))

    def test_sentence_meaning_takes_precedence(self):
        self.assertIn(
            "translation", prompt.describe_field("SentenceMeaning")
        )
        self.assertIn("translation", prompt.describe_field("Sentence Meaning"))

    def test_sentence(self):
        self.assertIn("example sentence", prompt.describe_field("Sentence"))

    def test_meaning(self):
        self.assertIn("English definition", prompt.describe_field("Meaning"))

    def test_note(self):
        self.assertIn("usage note", prompt.describe_field("Note"))

    def test_link(self):
        self.assertEqual("an empty string", prompt.describe_field("Link"))

    def test_fallback_includes_field_name(self):
        self.assertIn("PitchAccent", prompt.describe_field("PitchAccent"))


class MakeCardPromptTest(unittest.TestCase):
    def test_lists_every_field(self):
        fields = ["Japanese", "Reading", "Meaning", "Sentence", "SentenceMeaning"]
        text = prompt.make_card_prompt("勉強", fields)
        for name in fields:
            self.assertIn(f'"{name}"', text)
        self.assertIn("勉強", text)

    def test_uses_actual_custom_field_names(self):
        text = prompt.make_card_prompt("食べる", ["Front", "Back", "Extra"])
        self.assertIn('"Front"', text)
        self.assertIn('"Back"', text)
        self.assertIn('"Extra"', text)
        self.assertNotIn('"Japanese"', text)


if __name__ == "__main__":
    unittest.main()
