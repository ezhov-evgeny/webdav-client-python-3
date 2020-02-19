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
    inner_dir_name = 'inner'
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
        self.clean_local_dir(self.local_path_dir)

    def tearDown(self):
        self.clean_local_dir(self.local_path_dir)
        self.clean_remote_dir(self.remote_path_dir)
        self.clean_remote_dir(self.remote_path_dir2)

    def clean_remote_dir(self, remote_path_dir):
        if self.client.check(remote_path=remote_path_dir):
            self.client.clean(remote_path=remote_path_dir)

    @staticmethod
    def clean_local_dir(local_path_dir):
        if path.exists(path=local_path_dir):
            shutil.rmtree(path=local_path_dir)

    def _prepare_for_downloading(self, inner_dir=False, base_path=''):
        if base_path:
            self._create_remote_dir_if_needed(base_path)
        self._prepare_dir_for_downloading(base_path + self.remote_path_dir, base_path + self.remote_path_file, self.local_file_path)
        if not path.exists(self.local_path_dir):
            os.makedirs(self.local_path_dir)
        if inner_dir:
            self._prepare_dir_for_downloading(base_path + self.remote_inner_path_dir, base_path + self.remote_inner_path_file, self.local_file_path)

    def _prepare_dir_for_downloading(self, remote_path_dir, remote_path_file, local_file_path):
        self._create_remote_dir_if_needed(remote_path_dir)
        if not self.client.check(remote_path=remote_path_file):
            self.client.upload_file(remote_path=remote_path_file, local_path=local_file_path)

    def _create_remote_dir_if_needed(self, remote_dir):
        if not self.client.check(remote_path=remote_dir):
            self.client.mkdir(remote_path=remote_dir)

    def _prepare_for_uploading(self):
        if not self.client.check(remote_path=self.remote_path_dir):
            self.client.mkdir(remote_path=self.remote_path_dir)
        if not path.exists(path=self.local_path_dir):
            os.makedirs(self.local_path_dir)
        if not path.exists(path=self.local_path_dir + os.sep + self.local_file):
            shutil.copy(src=self.local_file_path, dst=self.local_path_dir + os.sep + self.local_file)


if __name__ == '__main__':
    unittest.main()
