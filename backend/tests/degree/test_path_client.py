from unittest.mock import patch

from django.test import TestCase

from degree.utils.path_client import PathClient, split_program_code, split_program_title


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


# A slice of the catalog Path lists for a term: undergraduate degrees, the masters degrees a
# submatriculant pursues, a minor, and graduate degrees we do not model.
CATALOG = [
    {"code": "CMPE-BSE", "title": "Computer Engineering BSE"},
    {"code": "CIS-BSE-ARIN", "title": "Computer Science BSE (Artificial Intelligence)"},
    {"code": "ANTH-BA-ARC", "title": "Anthropology BA (Archaeology)"},
    {"code": "NURS-BSN", "title": "Nursing BSN"},
    {"code": "EES-BAS", "title": "Environmental Science BAS"},
    {"code": "ACCT-BS", "title": "Accounting BS"},
    {"code": "CIS-MSE-NCON", "title": "Computer & Information Science MSE (No Concentration)"},
    {"code": "DATS-MSE", "title": "Data Science MSE"},
    {"code": "MATH-MINOR", "title": "Mathematics MINOR"},
    {"code": "CIS-PHD", "title": "Computer & Information Science PhD"},
    {"code": "WH-MBA", "title": "Wharton MBA"},
]


class ProgramFilteringTest(TestCase):
    """
    The catalog lists every program Penn offers, so each fetch selects the degree codes it
    models. Masters programs are fetched for submatriculants, separately from the
    undergraduate degrees they sit alongside.
    """

    def setUp(self):
        self.client = PathClient()
        patcher = patch.object(PathClient, "list_programs", return_value=CATALOG)
        patcher.start()
        self.addCleanup(patcher.stop)

    def codes(self, programs):
        return [program["code"] for program in programs]

    def test_undergraduate_programs_excludes_masters(self):
        self.assertEqual(
            self.codes(self.client.undergraduate_programs("202630")),
            ["CMPE-BSE", "CIS-BSE-ARIN", "ANTH-BA-ARC", "NURS-BSN", "EES-BAS", "ACCT-BS"],
        )

    def test_masters_programs(self):
        self.assertEqual(
            self.codes(self.client.masters_programs("202630")),
            ["CIS-MSE-NCON", "DATS-MSE"],
        )

    def test_minor_programs(self):
        self.assertEqual(self.codes(self.client.minor_programs("202630")), ["MATH-MINOR"])

    def test_unmodelled_graduate_programs_are_never_returned(self):
        returned = (
            self.codes(self.client.undergraduate_programs("202630"))
            + self.codes(self.client.masters_programs("202630"))
            + self.codes(self.client.minor_programs("202630"))
        )
        self.assertNotIn("CIS-PHD", returned)
        self.assertNotIn("WH-MBA", returned)

    def test_programs_with_degree_codes(self):
        self.assertEqual(
            self.codes(self.client.programs_with_degree_codes("202630", {"BSE", "MSE"})),
            ["CMPE-BSE", "CIS-BSE-ARIN", "CIS-MSE-NCON", "DATS-MSE"],
        )
