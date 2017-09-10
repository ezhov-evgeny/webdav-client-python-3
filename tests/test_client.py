from unittest import TestCase

from webdav2.client import Client


class ClientTestCase(TestCase):
    def setUp(self):
        options = {
            'webdav_hostname': 'https://webdav.yandex.ru',
            'webdav_login': 'webdavclient.test',
            'webdav_password': 'Qwerty123!'
        }
        self.client = Client(options)

    def test_list(self):
        file_list = self.client.list()
        self.assertIsNotNone(file_list, 'List of files should not be None')
        self.assertGreater(file_list.__len__(), 0, 'Expected that amount of files more then 0')

    def test_upload_file(self):
        remote_path = 'test.txt'
        local_path = './res/test.txt'
        if self.client.check(remote_path=remote_path):
            self.client.clean(remote_path=remote_path)
        self.client.upload_file(remote_path=remote_path, local_path=local_path)
        self.assertTrue(self.client.check(remote_path=remote_path))
