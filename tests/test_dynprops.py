import unittest
from collections import OrderedDict
from datetime import datetime
from typing import Optional, cast
import time

from dynprops import DynProps, Global, Parent, Local, row, as_dict


class I2B2Core(DynProps):
    """ Ordered list of properties in the i2b2 core model"""
    update_date: Global[datetime]
    download_date: Global[Optional[datetime]]
    import_date: Global[Optional[datetime]]
    sourcesystem_cd: Global[Optional[str]] = "Unspecified"


class I2B2CoreUploadIdFirst(I2B2Core):
    """ I2B2CoreModel with added upload identifier """
    upload_id: Global[Optional[int]]
    _: Parent


class I2B2CoreParentMiddle(I2B2Core):
    upload_id: Global[Optional[int]]
    _: Parent
    another_prop: Local[int]


class I2B2CoreNoParent(I2B2Core):
    upload_id: Global[Optional[int]]


class I2B2CoreDupValue(I2B2Core):
    upload_id: Global[Optional[int]]
    sourcesystem_cd: Global[int]


class I2B2SimpleDimension(I2B2CoreNoParent):
    concept_cd: Local[str]
    modifier_cd: Local[str] = "@"
    _: Parent


class DynPropsTestCase(unittest.TestCase):
    _b = '17'

    def setUp(self):
        I2B2SimpleDimension._clear()

    def tearDown(self):
        I2B2SimpleDimension._clear()
        I2B2SimpleDimension._separator = '\t'

    def test_headers(self):
        self.assertEqual('update_date\tdownload_date\timport_date\tsourcesystem_cd',
                         I2B2Core._head())
        self.assertEqual('upload_id\tupdate_date\tdownload_date\timport_date\tsourcesystem_cd',
                         I2B2CoreUploadIdFirst._head())
        self.assertEqual('upload_id\tupdate_date\tdownload_date\timport_date\tsourcesystem_cd\t'
                         'another_prop', I2B2CoreParentMiddle._head())
        self.assertEqual('update_date\tdownload_date\timport_date\tsourcesystem_cd\tupload_id',
                         I2B2CoreNoParent._head())
        self.assertEqual('update_date\tdownload_date\timport_date\tupload_id\tsourcesystem_cd',
                         I2B2CoreDupValue._head())
        self.assertEqual('concept_cd\tmodifier_cd\tupdate_date\tdownload_date\timport_date\t'
                         'sourcesystem_cd\tupload_id', I2B2SimpleDimension._head())

    def test_separator_and_head(self):
        x = I2B2Core()
        self.assertEqual("update_date\tdownload_date\timport_date\tsourcesystem_cd", I2B2Core._head())
        self.assertEqual(I2B2Core._head(), x._head())
        # Note: if you get a failure below
        I2B2Core._separator = 'A'
        self.assertEqual("update_dateAdownload_dateAimport_dateAsourcesystem_cd", I2B2Core._head())
        self.assertEqual(I2B2Core._head(), x._head())
        I2B2CoreUploadIdFirst._separator = 'B'
        self.assertEqual("update_dateAdownload_dateAimport_dateAsourcesystem_cd", I2B2Core._head())
        self.assertEqual(I2B2Core._head(), x._head())
        self.assertEqual("upload_idBupdate_dateBdownload_dateBimport_dateBsourcesystem_cd",
                         I2B2CoreUploadIdFirst._head())
        self.assertEqual("upload_idBupdate_dateBdownload_dateBimport_dateBsourcesystem_cd",
                         I2B2CoreUploadIdFirst()._head())

    def test_esc(self):
        self.assertEqual("abc", I2B2Core._escape("abc"))
        self.assertEqual(r'ABC\"DEF\"', I2B2Core._escape('ABC"DEF"'))
        self.assertEqual("ABC'DEF", I2B2Core._escape("ABC'DEF"))
        self.assertEqual("ABC\\\"DEF\\", I2B2Core._escape("ABC\"DEF\\"))

    def test_attributes(self):
        cwi_instance = I2B2CoreUploadIdFirst()
        core_instance = I2B2Core()
        # Cannot set property on the instance level
        with self.assertRaises(ValueError):
            core_instance.sourcesystem_cd = "test"
        # Cannot access a properties' internal form on instance level
        with self.assertRaises(ValueError):
            core_instance._sourcesystem_cd = "test"
        # Or the class level
        with self.assertRaises(ValueError):
            I2B2Core._sourcesystem_cd = "test"

        # Properties can be set on the class level
        I2B2Core.sourcesystem_cd = "test"

        # Properties are visible at the instance level
        self.assertEqual("test", core_instance.sourcesystem_cd)

        # Properties are visible at the class level
        self.assertEqual(core_instance.sourcesystem_cd, I2B2Core.sourcesystem_cd)

        # Properties are visible to subclasses
        self.assertEqual(core_instance.sourcesystem_cd, I2B2CoreUploadIdFirst.sourcesystem_cd)
        self.assertEqual(core_instance.sourcesystem_cd, cwi_instance.sourcesystem_cd)

        # Global Properties CANNOT be set at the inherited class level
        with self.assertRaises(ValueError):
            I2B2CoreUploadIdFirst.sourcesystem_cd = "test2"
        I2B2Core.sourcesystem_cd = "test3"

        # And settings are visible on the instance
        self.assertEqual("test3", core_instance.sourcesystem_cd)
        # ... inherited instance
        self.assertEqual(core_instance.sourcesystem_cd, cwi_instance.sourcesystem_cd)
        # ... class ...
        self.assertEqual(core_instance.sourcesystem_cd, I2B2CoreUploadIdFirst.sourcesystem_cd)
        # ... and superclass level
        self.assertEqual(core_instance.sourcesystem_cd, I2B2Core.sourcesystem_cd)

        # Subclass properties cannot be set at the instance level
        with self.assertRaises(ValueError):
            cwi_instance.upload_id = 117

        # Only the class level
        I2B2CoreUploadIdFirst.upload_id = 118

        # Subclass properties are not visible to superclass instances
        with self.assertRaises(AttributeError):
            _ = core_instance.upload_id
        # ... or the superclasses
        with self.assertRaises(AttributeError):
            _ = I2B2Core.upload_id

        # But are visible at the subclass instance level
        self.assertEqual(118, cwi_instance.upload_id)
        # And class level
        self.assertEqual(cwi_instance.upload_id, I2B2CoreUploadIdFirst.upload_id)

        # Clear covers base class but not inherited elements
        I2B2Core._clear()
        self.assertEqual("Unspecified", core_instance.sourcesystem_cd)
        self.assertEqual("Unspecified", cwi_instance.sourcesystem_cd)
        self.assertEqual(118, cwi_instance.upload_id)

        # Clear of subclass covers superclass as well
        I2B2Core.sourcesystem_cd = "test3"
        I2B2Core._clear()
        self.assertEqual("Unspecified", core_instance.sourcesystem_cd)
        self.assertEqual("Unspecified", cwi_instance.sourcesystem_cd)
        self.assertEqual(118, cwi_instance.upload_id)
        I2B2CoreUploadIdFirst._clear()
        self.assertIsNone(cwi_instance.upload_id)

    def test_function_property(self):
        I2B2Core.sourcesystem_cd = lambda: 'a' + self._b
        cwi_instance = I2B2CoreUploadIdFirst()
        core_instance = I2B2Core()
        self.assertEqual('a17', cwi_instance.sourcesystem_cd)
        self._b = '43'
        self.assertEqual('a43', cwi_instance.sourcesystem_cd)
        self.assertEqual('a43', core_instance.sourcesystem_cd)

    def test_extension_placement(self):
        x = I2B2CoreParentMiddle()
        self.assertEqual('upload_id\tupdate_date\tdownload_date\timport_date\tsourcesystem_cd\tanother_prop', x._head())
        self.assertEqual('update_date\tdownload_date\timport_date\tsourcesystem_cd\tupload_id',
                         I2B2CoreNoParent._head())

    def test_freeze(self):
        x = I2B2Core()
        y = I2B2CoreUploadIdFirst()
        I2B2Core.sourcesystem_cd = "SSCODE"
        I2B2Core.import_date = datetime(2017, 5, 31)
        I2B2Core.download_date = datetime(2017, 5, 30, 11, 33, 20)
        I2B2Core.update_date = datetime(2017, 5, 29, 8, 33, 20)

        self.assertEqual(OrderedDict([
            ('update_date', datetime(2017, 5, 29, 8, 33, 20)),
            ('download_date', datetime(2017, 5, 30, 11, 33, 20)),
            ('import_date', datetime(2017, 5, 31, 0, 0)),
            ('sourcesystem_cd', 'SSCODE')]), x._freeze())
        self.assertEqual(OrderedDict([
            ('upload_id', None),
            ('update_date', datetime(2017, 5, 29, 8, 33, 20)),
            ('download_date', datetime(2017, 5, 30, 11, 33, 20)),
            ('import_date', datetime(2017, 5, 31, 0, 0)),
            ('sourcesystem_cd', 'SSCODE')]), y._freeze())
        I2B2CoreUploadIdFirst.upload_id = 12345
        self.assertEqual(OrderedDict([
            ('update_date', datetime(2017, 5, 29, 8, 33, 20)),
            ('download_date', datetime(2017, 5, 30, 11, 33, 20)),
            ('import_date', datetime(2017, 5, 31, 0, 0)),
            ('sourcesystem_cd', 'SSCODE')]), x._freeze())
        self.assertEqual(OrderedDict([
            ('upload_id', 12345),
            ('update_date', datetime(2017, 5, 29, 8, 33, 20)),
            ('download_date', datetime(2017, 5, 30, 11, 33, 20)),
            ('import_date', datetime(2017, 5, 31, 0, 0)),
            ('sourcesystem_cd', 'SSCODE')]), y._freeze())
        I2B2Core._clear()
        self.assertEqual(OrderedDict([
             ('update_date', None),
             ('download_date', None),
             ('import_date', None),
             ('sourcesystem_cd', ''"Unspecified"'')]), x._freeze())
        self.assertEqual(OrderedDict([
             ('upload_id', 12345),
             ('update_date', None),
             ('download_date', None),
             ('import_date', None),
             ('sourcesystem_cd', ''"Unspecified"'')]), y._freeze())
        I2B2CoreUploadIdFirst._clear()

    def test_repr(self):
        I2B2CoreUploadIdFirst._clear()
        x = I2B2Core()
        y = I2B2CoreUploadIdFirst()
        I2B2Core.sourcesystem_cd = "SSCODE"
        I2B2Core.import_date = datetime(2017, 5, 31)
        I2B2Core.download_date = datetime(2017, 5, 30, 11, 33, 20)
        I2B2Core.update_date = datetime(2017, 5, 29, 8, 33, 20)
        self.assertEqual('2017-05-29 08:33:20\t2017-05-30 11:33:20\t2017-05-31 00:00:00\t"SSCODE"', x._delimited())
        self.assertEqual('\t2017-05-29 08:33:20\t2017-05-30 11:33:20\t2017-05-31 00:00:00\t"SSCODE"', y._delimited())
        I2B2CoreUploadIdFirst.upload_id = 12345
        self.assertEqual('2017-05-29 08:33:20\t2017-05-30 11:33:20\t2017-05-31 00:00:00\t"SSCODE"', x._delimited())
        self.assertEqual('12345\t2017-05-29 08:33:20\t2017-05-30 11:33:20\t2017-05-31 00:00:00\t"SSCODE"',
                         y._delimited())
        I2B2Core._separator = ','
        self.assertEqual('2017-05-29 08:33:20,2017-05-30 11:33:20,2017-05-31 00:00:00,"SSCODE"', x._delimited())
        self.assertEqual('12345,2017-05-29 08:33:20,2017-05-30 11:33:20,2017-05-31 00:00:00,"SSCODE"',
                         y._delimited())
        I2B2Core._clear()
        self.assertEqual(',,,"Unspecified"', x._delimited())
        self.assertEqual('12345,,,,"Unspecified"', y._delimited())
        I2B2CoreUploadIdFirst._clear()
        I2B2Core._separator = '\t'

    def test_str(self):
        I2B2CoreUploadIdFirst._clear()
        x = I2B2Core()
        y = I2B2CoreUploadIdFirst()
        I2B2Core.sourcesystem_cd = "SSCODE"
        I2B2Core.import_date = datetime(2017, 5, 31)
        I2B2Core.download_date = datetime(2017, 5, 30, 11, 33, 20)
        I2B2Core.update_date = datetime(2017, 5, 29, 8, 33, 20)
        self.assertEqual(
            "I2B2Core(update_date:'2017-05-29 08:33:20', download_date:'2017-05-30 "
            "11:33:20', import_date:'2017-05-31 00:00:00', sourcesystem_cd:'SSCODE')", str(x))
        self.assertEqual(
            "I2B2CoreUploadIdFirst(upload_id:'None', update_date:'2017-05-29 08:33:20', "
            "download_date:'2017-05-30 11:33:20', import_date:'2017-05-31 00:00:00', "
            "sourcesystem_cd:'SSCODE')", str(y))

    def test_dynamic_properties(self):
        test_dt = datetime.now()

        I2B2Core.sourcesystem_cd = "SS1"
        I2B2Core.update_date = test_dt
        I2B2Core.download_date = lambda: I2B2Core.update_date
        I2B2Core.import_date = lambda: I2B2Core.update_date

        self.assertEqual(OrderedDict([
             ('update_date', test_dt),
             ('download_date', test_dt),
             ('import_date', test_dt),
             ('sourcesystem_cd', 'SS1')]), I2B2Core()._freeze())

        I2B2Core.sourcesystem_cd = "Bananas"
        self.assertEqual(OrderedDict([
             ('update_date', test_dt),
             ('download_date', test_dt),
             ('import_date', test_dt),
             ('sourcesystem_cd', 'Bananas')]), I2B2Core()._freeze())

        I2B2Core.sourcesystem_cd = "SS2"
        I2B2Core.update_date = datetime.now
        I2B2Core.download_date = lambda: I2B2Core.update_date
        I2B2Core.import_date = lambda: I2B2Core.update_date

        x = I2B2Core()._freeze()
        time.sleep(1)
        self.assertTrue(cast(datetime, x['update_date']) < datetime.now())
        self.assertTrue(x['download_date'] >= x['update_date'])
        self.assertTrue(x['import_date'] >= x['update_date'])
        y = I2B2Core()._freeze()
        y1 = y['update_date']
        time.sleep(1)
        self.assertEqual(y1, y['update_date'])
        self.assertTrue(y['update_date'] > x['update_date'])
        I2B2Core.update_date = datetime.now()
        # Issue: If you omit this line, download_date is still bound to the dynamic update_date
        I2B2Core.download_date = I2B2Core.update_date
        x = I2B2Core()._freeze()
        self.assertEqual(x['update_date'], x['download_date'])

    def test_what_we_want(self):
        I2B2Core._clear()
        I2B2Core.download_date = lambda: I2B2Core.update_date
        I2B2Core.import_date = lambda: I2B2Core.update_date

        I2B2Core.sourcesystem_cd = "Biggie"
        self.assertEqual(OrderedDict([
             ('update_date', None),
             ('download_date', None),
             ('import_date', None),
             ('sourcesystem_cd', 'Biggie')]), I2B2Core()._freeze())
        I2B2Core.update_date = datetime(2017, 9, 27)
        self.assertEqual(OrderedDict([
             ('update_date', datetime(2017, 9, 27, 0, 0)),
             ('download_date', datetime(2017, 9, 27, 0, 0)),
             ('import_date', datetime(2017, 9, 27, 0, 0)),
             ('sourcesystem_cd', 'Biggie')]), I2B2Core()._freeze())

        # Clear doesn't affect class functions
        I2B2Core._clear()
        self.assertEqual(OrderedDict([
             ('update_date', None),
             ('download_date', None),
             ('import_date', None),
             ('sourcesystem_cd', "Unspecified")]), I2B2Core()._freeze())
        I2B2Core.update_date = datetime(2003, 1, 4)
        self.assertEqual(OrderedDict([
             ('update_date', datetime(2003, 1, 4)),
             ('download_date', None),
             ('import_date', None),
             ('sourcesystem_cd', "Unspecified")]), I2B2Core()._freeze())

    def test_extension(self):
        class C1(DynProps):
            """ Ordered list of properties in the i2b2 core model"""
            sourcesystem_cd: Global[Optional[str]]
            x: Global[str]

        self.assertEqual("\t", C1()._delimited())

        with self.assertRaises(AttributeError):
            class Extension0(C1):
                sourcesystem_cd = "SS2"
                foo: Local[str]
            _ = Extension0                      # Prevent lint check

        class Extension(C1):
            foo: Local[str] = "Apples"

        _ = Extension()                         # Prevent lint check
        C1.sourcesystem_cd = "SS3"

        self.assertEqual('"SS3"\t', C1()._delimited())
        C1._clear()
        self.assertEqual("\t", C1()._delimited())

    def test_reify(self):
        class SpecialProp1:
            def __init__(self, *parts) -> None:
                self.parts = parts

            def reify(self):
                return '-'.join(str(s) for s in self.parts) if self.parts else None

        class SpecialProp2:
            def __init__(self, *parts) -> None:
                self.parts = parts

            def reify(self):
                return sum(int(p) for p in self.parts) if self.parts else None

        class R1(DynProps):
            sp1: Local[SpecialProp1]
            sp2: Local[SpecialProp1]
            sp3: Local[SpecialProp2]
            sp4: Local[SpecialProp2]

        r = R1()
        r.sp1 = SpecialProp1('a', 17, None)
        r.sp2 = SpecialProp1()
        r.sp3 = SpecialProp2(17, -3, 100101)
        r.sp4 = SpecialProp2()
        self.assertEqual('"a-17-None"\t\t100115\t', row(r))
        self.assertEqual(OrderedDict([
             ('sp1', 'a-17-None'),
             ('sp2', None),
             ('sp3', 100115),
             ('sp4', None)]), as_dict(r))


if __name__ == '__main__':
    unittest.main()
