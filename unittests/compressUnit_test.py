import tools.compress
import tools.clean
import os
import shutil
import unittest


class TestCompressModule(unittest.TestCase):
    """
    Tests for the compress module

    All the test use a predetermined file adulterado in the unittest_dataset_clean
        Only original size and compressed size are tested since decomporession time
    is always an avarage.
    """

    @classmethod
    def setUpClass(cls):
        if not os.path.exists('unittest_dataset_clean'):
            os.mkdir('unittest_dataset_clean')
        tools.clean.clean('unittest_dataset/adulterado.txt', 'unittest_dataset_clean', apply_limits=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('unittest_dataset_clean')

    def test_gzip_max(self):
        """
    Test the result of calling the gzip compression for the file with maximum
    compression level.

    """
        cd = tools.compress.gzip_compress('unittest_dataset_clean/adulterado.txt', 9, False)
        self.assertEqual(cd.original, 47385)
        self.assertEqual(cd.compressed, 17029)

    def test_brotli_max(self):
        """
    Test the result of calling the brotli compression for the file with maximum
    compression level.

    """
        cd = tools.compress.brotli_compress('unittest_dataset_clean/adulterado.txt', 11, False)
        self.assertEqual(cd.original, 47385)
        self.assertEqual(cd.compressed, 13969)

    @unittest.skipIf('paq8l' not in tools.compress.AVAILABLE_COMPRESSORS,
                     "Paq8l not installed: paq8l avalable at cs.fit.edu/~mmahoney/compression/")
    def test_paq8l_max(self):
        """
    Test the result of calling the paq8l compressor with maximum compression level
    for the file.
    """
        cd = tools.compress.paq8l_compress('unittest_dataset_clean/adulterado.txt', 8, False)
        self.assertEqual(cd.original, 47385)
        self.assertEqual(cd.compressed, 9741)

    @unittest.skipIf('lzma' not in tools.compress.AVAILABLE_COMPRESSORS,
                     "Lzma not installed: please install python-lzma")
    def test_lzma_max(self):
        """
    Test the result of calling the lzma compressor, with max level(the level is
    not used, rather it serves to show that it is in fact not being used -- see
    test_lzma_min the values are the same)
    """
        cd = tools.compress.lzma_compress('unittest_dataset_clean/adulterado.txt', 9, False)
        self.assertEqual(cd.original, 47385)
        self.assertEqual(cd.compressed, 13282)

    def test_bzip2_max(self):
        """
    Test the results of calling the bzip2 compressor with maximum level of
    compression.
    """
        cd = tools.compress.bzip2_compress('unittest_dataset_clean/adulterado.txt', 9, False)
        self.assertEqual(cd.original, 47385)
        self.assertEqual(cd.compressed, 13040)

    @unittest.skipIf('ppmd' not in tools.compress.AVAILABLE_COMPRESSORS,
                     "Ppmd not installed in path")
    def test_ppmd_max(self):
        """
    Test the results of calling the ppmd compressor with maximum level of
    compression.
    """
        cd = tools.compress.ppmd_compress('unittest_dataset_clean/adulterado.txt', 16, False)
        self.assertEqual(cd.original, 47385)
        self.assertEqual(cd.compressed, 12950)

    @unittest.skipIf('spbio' not in tools.compress.AVAILABLE_COMPRESSORS,
                     "Spbio not installed in path")
    def test_spbio_max(self):
        """
    Test the result of calling the spbio compressor with maximum compression level
    for the file.
    """
        cd = tools.compress.spbio_compress('unittest_dataset_clean/adulterado.txt', 8, False)
        self.assertEqual(cd.original, 47385)
        self.assertEqual(cd.compressed, 9741)


if __name__ == '__main__':
    unittest.main(exit=False, verbosity=2)
