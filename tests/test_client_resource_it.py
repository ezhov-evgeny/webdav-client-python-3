import io
import unittest
from os import path
from os.path import sep

from tests.base_client_it import BaseClientTestCase
from webdav3.client import Resource
from webdav3.urn import Urn


class ResourceTestCase(BaseClientTestCase):

    def test_str(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        self.assertEqual('resource /test_dir/test.txt', resource.__str__())

    def test_is_not_dir(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        self.assertFalse(resource.is_dir())

    def test_is_dir(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_dir))
        self.assertTrue(resource.is_dir())

    def test_rename(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        resource.rename('new_name.text')
        self.assertTrue(self.client.check(self.remote_path_dir + '/new_name.text'))

    def test_move(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        self.client.mkdir(self.remote_path_dir2)
        resource.move(self.remote_path_file2)
        self.assertFalse(self.client.check(self.remote_path_file))
        self.assertTrue(self.client.check(self.remote_path_file2))

    def test_copy(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        self.client.mkdir(self.remote_path_dir2)
        resource.copy(self.remote_path_file2)
        self.assertTrue(self.client.check(self.remote_path_file))
        self.assertTrue(self.client.check(self.remote_path_file2))

    def test_info(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        info = resource.info()
        self.assertIsNotNone(info)
        self.assertGreater(len(info), 0)

    def test_info_params(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        info = resource.info(['size'])
        self.assertIsNotNone(info)
        self.assertEqual(1, len(info))
        self.assertTrue('size' in info)

    def test_clean(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        resource.clean()
        self.assertFalse(self.client.check(self.remote_path_file))

    def test_check(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        self.assertTrue(resource.check())

    def test_read_from_and_write_to(self):
        self._prepare_for_downloading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        resource.read_from('string')
        buff = io.BytesIO(b'')
        resource.write_to(buff)
        self.assertEqual(buff.getvalue().decode(), 'string')

    def test_read_and_write(self):
        self._prepare_for_uploading()
        resource = Resource(self.client, Urn(self.remote_path_file))
        resource.read(self.local_file_path)
        resource.write(self.local_path_dir + sep + 'test2.txt')
        self.assertTrue(path.exists(self.local_path_dir + sep + 'test2.txt'))


if __name__ == '__main__':
    unittest.main()
