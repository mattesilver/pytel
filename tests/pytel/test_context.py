from unittest import TestCase

from pytel import ContextCreator
from pytel.context import ObjectDescriptor


class Service:
    @staticmethod
    def a() -> str:
        return 'a'


class TestContextCreator(TestCase):
    def test_set(self):
        cc = ContextCreator()
        s = Service()

        descr = ObjectDescriptor.from_(s.a)
        cc.set('a', descr)

        self.assertEqual(descr, cc._map['a'])

    def test_set_deuplicate_keyerror(self):
        cc = ContextCreator()
        s = Service()

        descr = ObjectDescriptor.from_(s.a)
        cc.set('a', descr)

        self.assertRaises(KeyError, lambda: cc.set('a', descr))

    def test_pytel(self):
        cc = ContextCreator()
        s = Service()

        descr = ObjectDescriptor.from_(s.a)
        cc.set('a', descr)

        ctx = cc.resolve()
        result_descr = ctx._context._objects['a']
        self.assertEqual(descr, result_descr)


