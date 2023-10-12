from django.test import TestCase
from degree.utils.model_utils import q_object_parser
from django.db.models import Q
from lark.exceptions import LarkError

class QObjectParserTest(TestCase):
    def assertParsedEqual(self, q: Q):
        self.assertEqual(q_object_parser.parse(repr(q)), q)
        self.assertEqual(
            repr(q_object_parser.parse(repr(q))), 
            repr(q)
        )

    def test_no_clause(self):
        with self.assertRaises(LarkError): 
            q_object_parser.parse(r"<Q: >")

    def test_empty_q(self):
        self.assertParsedEqual(Q())

    def test_negated_empty_q(self):
        self.assertParsedEqual(~Q())

    def test_string_condition(self):
        self.assertParsedEqual(Q(key="value"))
    
    def test_null_condition(self):
        self.assertParsedEqual(Q(key=None))
    
    def test_int_condition(self):
        self.assertParsedEqual(Q(key=100))
    
    def test_signed_int_condition(self):
        self.assertParsedEqual(Q(key=-100))

    def test_float_condition(self):
        self.assertParsedEqual(Q(key=1.0))
    
    def test_signed_float_condition(self):
        self.assertParsedEqual(Q(key=-1.0))    

    def test_string_escaping(self):
        self.assertParsedEqual(Q(key="\""))
        self.assertParsedEqual(Q(key='\''))
        self.assertParsedEqual(Q(key="""""'"'"""))


    def test_and(self):
        self.assertParsedEqual(Q(key=r"value") & Q(key2=r"value2"))

    def test_or(self):
        self.assertParsedEqual(Q(key="value") | Q(key2="value2"))
    
    def test_nested_negations(self):
        q1 = Q(key="value")
        q2 = Q(key2="value2")
        self.assertParsedEqual(~(q1 | q2)) 
        self.assertParsedEqual((~q1 | q2))
        self.assertParsedEqual((q1 | ~q2))
        self.assertParsedEqual(~(q1 & q2)) 
        self.assertParsedEqual((~q1 & q2))
        self.assertParsedEqual((q1 & ~q2))
    
    def test_double_negations(self):
        self.assertParsedEqual(~~Q(key="value"))

    def test_unparseable_clause(self):
        with self.assertRaises(LarkError):
            q_object_parser.parse(r"<Q: (XOR: ('key', 'value'))>")

    def test_unparseable_value(self):
        with self.assertRaises(LarkError):
            q_object_parser.parse(r"<Q: (AND: ('key', datetime.datetime(2023, 10, 11, 1, 24, 6, 114278)))>")

    def test_idempotency(self):
        self.assertParsedEqual(q_object_parser.parse(repr(Q(key="\"'value"))))
    
        

