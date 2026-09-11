from django.test import TestCase

from degree.utils.path_client import split_program_code, split_program_title


class ProgramCodeTest(TestCase):
    def test_split_program_code(self):
        self.assertEqual(split_program_code("CMPE-BSE"), ("CMPE", "BSE", None))
        self.assertEqual(split_program_code("ANTH-BA-ARC"), ("ANTH", "BA", "ARC"))
        with self.assertRaises(ValueError):
            split_program_code("CMPE")

    def test_split_program_title(self):
        self.assertEqual(
            split_program_title("Computer Engineering BSE", "BSE"),
            ("Computer Engineering", None),
        )
        self.assertEqual(
            split_program_title("Anthropology BA (Archaeology)", "BA"),
            ("Anthropology", "Archaeology"),
        )
        self.assertEqual(
            split_program_title("Computer Science BA - College 2nd Major ONLY", "BA"),
            ("Computer Science", None),
        )

    def test_split_program_title_with_a_trailing_qualifier(self):
        self.assertEqual(
            split_program_title(
                "Biomedical Science BA (Biomedical Devices) - College 2nd Major ONLY", "BA"
            ),
            ("Biomedical Science", "Biomedical Devices"),
        )
