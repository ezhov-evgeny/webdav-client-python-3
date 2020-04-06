import unittest

from tests.test_client_it import ClientTestCase


class TailingSlashClientTestCase(ClientTestCase):
    options = {
        'webdav_hostname': 'http://localhost:8585/',
        'webdav_login': 'alice',
        'webdav_password': 'secret1234',
        'webdav_override_methods': {
            'check': 'GET'
        }
    }

    def test_list_inner(self):
        self._prepare_for_downloading(True)
        file_list = self.client.list(self.remote_inner_path_dir)
        self.assertIsNotNone(file_list, 'List of files should not be None')

    def test_hostname_no_tailing_slash(self):
        self.assertEqual('5', self.client.webdav.hostname[-1])


if __name__ == '__main__':
    unittest.main()
