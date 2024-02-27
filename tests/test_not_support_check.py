import unittest

from tests.test_client_it import ClientTestCase


class TailingSlashClientTestCase(ClientTestCase):
    options = {
        'webdav_hostname': 'http://localhost:8585/',
        'webdav_login': 'alice',
        'webdav_password': 'secret1234',
        'webdav_override_methods': {
            'check': 'PROPFIND'
        }
    }

    def test_check_is_overridden(self):
        self.assertEqual('PROPFIND', self.client.requests['check'])

if __name__ == '__main__':
    unittest.main()
