import unittest

from dynprops import DynProps, Global, Local


# The class declarations below provide a stripped down view of what is happening in i2FHIRb2

class I2B2Core(DynProps):
    sourcesystem_cd: Global[str] = "Unspecified"


class OntologyEntry(I2B2Core):
    c_hlevel: Local[int] = 0
    c_foo: Local[str] = "fish"


class ConceptOntologyEntry(OntologyEntry):
    def c_hlevel(self) -> int:
        return 101


class OntologyRoot(OntologyEntry):
    c_hlevel = 2


class ConceptOntologyTestCase(unittest.TestCase):
    """ Test Issue #2 """
    def test_ontologyroot(self):
        self.assertEqual(0, OntologyEntry().c_hlevel)

        # The line below produces an error
        self.assertEqual(101, ConceptOntologyEntry().c_hlevel)

        # And this line produces a 101
        self.assertEqual(2, OntologyRoot().c_hlevel)

    def test_inheritedroot(self):
        self.assertEqual("fish", OntologyRoot().c_foo)

    def test_none_as_default(self):
        ConceptOntologyEntry.c_foo = None
        self.assertIsNone(ConceptOntologyEntry().c_foo)


if __name__ == '__main__':
    unittest.main()
