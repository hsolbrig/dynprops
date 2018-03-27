import unittest
from collections import OrderedDict
from datetime import datetime
from typing import Optional

from dynprops import DynProps, Global, Parent, Local, row


class I2B2Core(DynProps):
    """ Ordered list of properties in the i2b2 core model"""
    update_date: Global[datetime]
    download_date: Global[Optional[datetime]] = lambda: I2B2Core.update_date
    import_date: Global[Optional[datetime]] = lambda: I2B2Core.update_date
    sourcesystem_cd: Global[str] = "Unspecified"


class I2B2CoreWithUploadId(I2B2Core):
    """ I2B2CoreModel with added upload identifier """
    _: Parent
    upload_id: Global[Optional[int]]


class I2B2SimpleDimensionProps(I2B2CoreWithUploadId):
    # We need a way to signify that the elements below are not singletons
    concept_cd: Local[str]
    modifier_cd: Local[str] = '@'
    _: Parent


# This class exists to make sure that initialization doesn't clear out
# its parent.
class I2B2CoreWithUploadId(I2B2Core):
    pass


class I2B2SimpleDimension(I2B2SimpleDimensionProps):
    # Issue - The properties below can be class or instance props
    concept_cd = "LOINC:11971"
    modifier_cd = '@'

    
class I2B2SimpleDimension2(I2B2SimpleDimensionProps):

    def __init__(self, cc: str, mc: Optional[str]=None):
        self._concept_cd = cc
        self.mc = mc

    def concept_cd(self):
        return self._concept_cd

    def modifier_cd(self):
        return self.mc if self.mc else '@'


class DynObjectTestCase(unittest.TestCase):
    def setUp(self):
        I2B2Core._clear()
        I2B2CoreWithUploadId._clear()

    def tearDown(self):
        I2B2Core._clear()
        I2B2CoreWithUploadId._clear()
        DynProps._separator = '\t'

    def test_simple_dimension(self):
        x = I2B2SimpleDimension()
        with self.assertRaises(ValueError):
            I2B2SimpleDimension.update_date = datetime(2017, 2, 4)
        I2B2Core.update_date = datetime(2017, 2, 3)
        self.assertEqual(OrderedDict([
             ('concept_cd', 'LOINC:11971'),
             ('modifier_cd', '@'),
             ('update_date', datetime(2017, 2, 3, 0, 0)),
             ('download_date', datetime(2017, 2, 3, 0, 0)),
             ('import_date', datetime(2017, 2, 3, 0, 0)),
             ('sourcesystem_cd', 'Unspecified'),
             ('upload_id', None)]), x._freeze())
        y = I2B2SimpleDimension2("SCT:1234")
        z = I2B2SimpleDimension2("TEST", "MOD")
        self.assertEqual(OrderedDict([
             ('concept_cd', 'SCT:1234'),
             ('modifier_cd', '@'),
             ('update_date', datetime(2017, 2, 3, 0, 0)),
             ('download_date', datetime(2017, 2, 3, 0, 0)),
             ('import_date', datetime(2017, 2, 3, 0, 0)),
             ('sourcesystem_cd', 'Unspecified'),
             ('upload_id', None)]), y._freeze())
        self.assertEqual(OrderedDict([
             ('concept_cd', 'TEST'),
             ('modifier_cd', 'MOD'),
             ('update_date', datetime(2017, 2, 3, 0, 0)),
             ('download_date', datetime(2017, 2, 3, 0, 0)),
             ('import_date', datetime(2017, 2, 3, 0, 0)),
             ('sourcesystem_cd', 'Unspecified'),
             ('upload_id', None)]), z._freeze())
        self.assertEqual(OrderedDict([
             ('concept_cd', 'LOINC:11971'),
             ('modifier_cd', '@'),
             ('update_date', datetime(2017, 2, 3, 0, 0)),
             ('download_date', datetime(2017, 2, 3, 0, 0)),
             ('import_date', datetime(2017, 2, 3, 0, 0)),
             ('sourcesystem_cd', 'Unspecified'),
             ('upload_id', None)]), x._freeze())

    def test_late_inheritence(self):
        class Base(DynProps):
            a_global_prop: Global[str]

        class I1(Base):
            a_local_prop: Local[str] = "loc1"

        Base.a_global_prop = "glob1"

        class I2(Base):
            a_local_prop_2: Local[str] = "loc2"
        DynProps._separator = "-"

        self.assertEqual('glob1-loc1', row(I1()))
        self.assertEqual('glob1-loc2', row(I2()))
        DynProps._separator = '\t'

    def test_simple_props(self):
        class Base(DynProps):
            a_prop: Global[str] = 'on the'
            a_general_item = "penguin"

            def __init__(self, v: str) -> None:
                self.v = v

            def try_me(self) -> str:
                return f"There is a {self.a_general_item} {self.a_prop} {self.v}"

        x = Base("telly")
        self.assertEqual("There is a penguin on the telly", x.try_me())

    def test_method(self):
        class Base(DynProps):
            p1: Local[str]
            p2: Local[str]

        class C(Base):
            def p1(self) -> str:
                return "pie"

            def p2(self) -> str:
                return "pizza " + self.p1()

        x = C()
        from pprint import PrettyPrinter; pp = PrettyPrinter().pprint
        pp(row(x))


if __name__ == '__main__':
    unittest.main()
