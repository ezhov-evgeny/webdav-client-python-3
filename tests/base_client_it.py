import os
import shutil
import unittest
from os import path

from webdav3.client import Client


class BaseClientTestCase(unittest.TestCase):
    remote_path_file = 'test_dir/test.txt'
    remote_path_file2 = 'test_dir2/test.txt'
    remote_inner_path_file = 'test_dir/inner/test.txt'
    remote_path_dir = 'test_dir'
    remote_path_dir2 = 'test_dir2'
    remote_inner_path_dir = 'test_dir/inner'
    local_base_dir = 'tests/'
    local_file = 'test.txt'
    local_file_path = local_base_dir + 'test.txt'
    local_path_dir = local_base_dir + 'res/test_dir'

    options = {
        'webdav_hostname': 'http://localhost:8585',
        'webdav_login': 'alice',
        'webdav_password': 'secret1234',
        'webdav_override_methods': {
            'check': 'GET'
        }
    }

    # options = {
    #     'webdav_hostname': 'https://webdav.yandex.ru',
    #     'webdav_login': 'webdavclient.test2',
    #     'webdav_password': 'Qwerty123!'
    # }

    def setUp(self):
        self.client = Client(self.options)
        if path.exists(path=self.local_path_dir):
            shutil.rmtree(path=self.local_path_dir)

    def tearDown(self):
        if path.exists(path=self.local_path_dir):
            shutil.rmtree(path=self.local_path_dir)
        if self.client.check(remote_path=self.remote_path_dir):
            self.client.clean(remote_path=self.remote_path_dir)
        if self.client.check(remote_path=self.remote_path_dir2):
            self.client.clean(remote_path=self.remote_path_dir2)

    def _prepare_for_downloading(self, inner_dir=False):
        if not self.client.check(remote_path=self.remote_path_dir):
            self.client.mkdir(remote_path=self.remote_path_dir)
        if not self.client.check(remote_path=self.remote_path_file):
            self.client.upload_file(remote_path=self.remote_path_file, local_path=self.local_file_path)
        if not path.exists(self.local_path_dir):
            os.makedirs(self.local_path_dir)
        if inner_dir:
            if not self.client.check(remote_path=self.remote_inner_path_dir):
                self.client.mkdir(remote_path=self.remote_inner_path_dir)
            if not self.client.check(remote_path=self.remote_inner_path_file):
                self.client.upload_file(remote_path=self.remote_inner_path_file, local_path=self.local_file_path)

    def _prepare_for_uploading(self):
        if not self.client.check(remote_path=self.remote_path_dir):
            self.client.mkdir(remote_path=self.remote_path_dir)
        if not path.exists(path=self.local_path_dir):
            os.makedirs(self.local_path_dir)
        if not path.exists(path=self.local_path_dir + os.sep + self.local_file):
            shutil.copy(src=self.local_file_path, dst=self.local_path_dir + os.sep + self.local_file)


if __name__ == '__main__':
    unittest.main()
