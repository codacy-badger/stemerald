import unittest

from stemerald.tests.helpers import As, WebTestCase


class RootTestCase(WebTestCase):
    url = '/apiv2/version'

    def test_root(self):
        result, ___ = self.request(As.everyone, 'GET', self.url)

        self.assertIn('version', result)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
