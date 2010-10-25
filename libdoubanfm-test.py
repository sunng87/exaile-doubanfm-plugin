import unittest

from libdoubanfm import DoubanFM, LoginException

class TestLibDoubanfm(unittest.TestCase):
    def setUp(self):
        self.libdbfm = DoubanFM('a2721891@bofthew.com', '123456')
        
    def test_recommend(self):
        self.libdbfm.recommend('4747645','Just for test')

    def test_playlist(self):
        result = self.libdbfm.new_playlist()
        self.assertNotEqual(None, result)
        self.assertTrue(len(result) > 0)

    def test_login_fail(self):
        try:
            lidbfm = DoubanFM('not_a_user_name', '111')
            self.fail('should not here')
        except LoginException:
            self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
