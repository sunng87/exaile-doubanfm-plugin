import unittest

from libdbfm import DoubanFM

class TestLibDoubanfm(unittest.TestCase):
    def setUp(self):
        self.libdbfm = DoubanFM('a2721891@bofthew.com', '123456')

    def test_playlist(self):
        result = self.libdbfm.new_playlist()
        self.assertNotEqual(None, result)
        self.assertTrue(len(result) > 0)

if __name__ == '__main__':
    unittest.main()
