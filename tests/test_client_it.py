import os.path
import shutil
import unittest
from io import BytesIO, StringIO
from os import path
from time import sleep

from tests.base_client_it import BaseClientTestCase
from webdav3.exceptions import MethodNotSupported, OptionNotValid, RemoteResourceNotFound


class ClientTestCase(BaseClientTestCase):
    pulled_file = BaseClientTestCase.local_path_dir + os.sep + BaseClientTestCase.local_file

    def test_list(self):
        self._prepare_for_downloading()
        file_list = self.client.list()
        self.assertIsNotNone(file_list, 'List of files should not be None')
        self.assertGreater(file_list.__len__(), 0, 'Expected that amount of files more then 0')

    def test_free(self):
        if 'localhost' in self.options['webdav_hostname']:
            with self.assertRaises(MethodNotSupported):
                self.client.free()
        else:
            self.assertGreater(self.client.free(), 0, 'Expected that free space on WebDAV server is more then 0 bytes')

    def test_check(self):
        self.assertTrue(self.client.check(), 'Expected that root directory is exist')

    def test_mkdir(self):
        if self.client.check(remote_path=self.remote_path_dir):
            self.client.clean(remote_path=self.remote_path_dir)
        self.client.mkdir(remote_path=self.remote_path_dir)
        self.assertTrue(self.client.check(remote_path=self.remote_path_dir), 'Expected the directory is created.')

    def test_download_from(self):
        self._prepare_for_downloading()
        buff = BytesIO()
        self.client.download_from(buff=buff, remote_path=self.remote_path_file)
        self.assertEqual(buff.getvalue(), b'test content for testing of webdav client')

    def test_download_from_dir(self):
        self._prepare_for_downloading()
        buff = BytesIO()
        with self.assertRaises(OptionNotValid):
            self.client.download_from(buff=buff, remote_path=self.remote_path_dir)

    def test_download_from_wrong_file(self):
        self._prepare_for_downloading()
        buff = BytesIO()
        with self.assertRaises(RemoteResourceNotFound):
            self.client.download_from(buff=buff, remote_path='wrong')

    def test_download_directory_wrong(self):
        self._prepare_for_downloading()
        with self.assertRaises(RemoteResourceNotFound):
            self.client.download_directory(remote_path=self.remote_path_file, local_path=self.local_path_dir)

    def test_download(self):
        self._prepare_for_downloading()
        self.client.download(local_path=self.local_path_dir, remote_path=self.remote_path_dir)
        self.assertTrue(path.exists(self.local_path_dir), 'Expected the directory is downloaded.')
        self.assertTrue(path.isdir(self.local_path_dir), 'Expected this is a directory.')
        self.assertTrue(path.exists(self.local_path_dir + os.path.sep + self.local_file),
                        'Expected the file is downloaded')
        self.assertTrue(path.isfile(self.local_path_dir + os.path.sep + self.local_file),
                        'Expected this is a file')

    def test_download_sync(self):
        self._prepare_for_downloading()

        def callback():
            self.assertTrue(path.exists(self.local_path_dir + os.path.sep + self.local_file),
                            'Expected the file is downloaded')
            self.assertTrue(path.isfile(self.local_path_dir + os.path.sep + self.local_file),
                            'Expected this is a file')

        self.client.download_sync(local_path=self.local_path_dir + os.path.sep + self.local_file,
                                  remote_path=self.remote_path_file, callback=callback)
        self.assertTrue(path.exists(self.local_path_dir + os.path.sep + self.local_file),
                        'Expected the file has already been downloaded')

    def test_download_async(self):
        self._prepare_for_downloading()

        def callback():
            self.assertTrue(path.exists(self.local_path_dir + os.path.sep + self.local_file),
                            'Expected the file is downloaded')
            self.assertTrue(path.isfile(self.local_path_dir + os.path.sep + self.local_file),
                            'Expected this is a file')

        self.client.download_async(local_path=self.local_path_dir + os.path.sep + self.local_file,
                                   remote_path=self.remote_path_file, callback=callback)
        self.assertFalse(path.exists(self.local_path_dir + os.path.sep + self.local_file),
                         'Expected the file has not been downloaded yet')
        # It needs for ending download before environment will be cleaned in tearDown
        sleep(0.4)

    def test_upload_from(self):
        self._prepare_for_uploading()
        buff = StringIO()
        buff.write(u'test content for testing of webdav client')
        self.client.upload_to(buff=buff, remote_path=self.remote_path_file)
        self.assertTrue(self.client.check(self.remote_path_file), 'Expected the file is uploaded.')

    def test_upload(self):
        self._prepare_for_uploading()
        self.client.upload(remote_path=self.remote_path_file, local_path=self.local_path_dir)
        self.assertTrue(self.client.check(self.remote_path_dir), 'Expected the directory is created.')
        self.assertTrue(self.client.check(self.remote_path_file), 'Expected the file is uploaded.')

    def test_upload_file(self):
        self._prepare_for_uploading()
        self.client.upload_file(remote_path=self.remote_path_file, local_path=self.local_file_path)
        self.assertTrue(self.client.check(remote_path=self.remote_path_file), 'Expected the file is uploaded.')

    def test_upload_sync(self):
        self._prepare_for_uploading()

        def callback():
            self.assertTrue(self.client.check(self.remote_path_dir), 'Expected the directory is created.')
            self.assertTrue(self.client.check(self.remote_path_file), 'Expected the file is uploaded.')

        self.client.upload_sync(remote_path=self.remote_path_file, local_path=self.local_path_dir, callback=callback)

    def test_copy(self):
        self._prepare_for_downloading()
        self.client.mkdir(remote_path=self.remote_path_dir2)
        self.client.copy(remote_path_from=self.remote_path_file, remote_path_to=self.remote_path_file2)
        self.assertTrue(self.client.check(remote_path=self.remote_path_file2))

    def test_move(self):
        self._prepare_for_downloading()
        self.client.mkdir(remote_path=self.remote_path_dir2)
        self.client.move(remote_path_from=self.remote_path_file, remote_path_to=self.remote_path_file2)
        self.assertFalse(self.client.check(remote_path=self.remote_path_file))
        self.assertTrue(self.client.check(remote_path=self.remote_path_file2))

    def test_clean(self):
        self._prepare_for_downloading()
        self.client.clean(remote_path=self.remote_path_dir)
        self.assertFalse(self.client.check(remote_path=self.remote_path_file))
        self.assertFalse(self.client.check(remote_path=self.remote_path_dir))

    def test_info(self):
        self._prepare_for_downloading()
        result = self.client.info(remote_path=self.remote_path_file)
        self.assertEqual(result['size'], '41')
        self.assertTrue('created' in result)
        self.assertTrue('modified' in result)

    def test_directory_is_dir(self):
        self._prepare_for_downloading()
        self.assertTrue(self.client.is_dir(self.remote_path_dir), 'Should return True for directory')

    def test_file_is_not_dir(self):
        self._prepare_for_downloading()
        self.assertFalse(self.client.is_dir(self.remote_path_file), 'Should return False for file')

    def test_get_property_of_non_exist(self):
        self._prepare_for_downloading()
        result = self.client.get_property(remote_path=self.remote_path_file, option={'name': 'aProperty'})
        self.assertEqual(result, None, 'For not found property should return value as None')

    def test_set_property(self):
        self._prepare_for_downloading()
        self.client.set_property(remote_path=self.remote_path_file, option={
            'namespace': 'test',
            'name': 'aProperty',
            'value': 'aValue'
        })
        result = self.client.get_property(remote_path=self.remote_path_file,
                                          option={'namespace': 'test', 'name': 'aProperty'})
        self.assertEqual(result, 'aValue', 'Property value should be set')

    def test_set_property_batch(self):
        self._prepare_for_downloading()
        self.client.set_property_batch(remote_path=self.remote_path_file, option=[
            {
                'namespace': 'test',
                'name': 'aProperty',
                'value': 'aValue'
            },
            {
                'namespace': 'test',
                'name': 'aProperty2',
                'value': 'aValue2'
            }
        ])
        result = self.client.get_property(remote_path=self.remote_path_file,
                                          option={'namespace': 'test', 'name': 'aProperty'})
        self.assertEqual(result, 'aValue', 'First property value should be set')
        result = self.client.get_property(remote_path=self.remote_path_file,
                                          option={'namespace': 'test', 'name': 'aProperty2'})
        self.assertEqual(result, 'aValue2', 'Second property value should be set')

    def test_pull(self):
        self._prepare_for_downloading(True)
        self.client.pull(self.remote_path_dir, self.local_path_dir)
        self.assertTrue(path.exists(self.local_path_dir), 'Expected the directory is downloaded.')
        self.assertTrue(path.exists(self.local_path_dir + os.path.sep + self.inner_dir_name), 'Expected the directory is downloaded.')
        self.assertTrue(path.exists(self.local_path_dir + os.path.sep + self.inner_dir_name), 'Expected the directory is downloaded.')
        self.assertTrue(path.isdir(self.local_path_dir), 'Expected this is a directory.')
        self.assertTrue(path.isdir(self.local_path_dir + os.path.sep + self.inner_dir_name), 'Expected this is a directory.')
        self.assertTrue(path.exists(self.local_path_dir + os.path.sep + self.local_file),
                        'Expected the file is downloaded')
        self.assertTrue(path.isfile(self.local_path_dir + os.path.sep + self.local_file),
                        'Expected this is a file')

    def test_push(self):
        self._prepare_for_uploading()
        self.client.push(self.remote_path_dir, self.local_path_dir)
        self.assertTrue(self.client.check(self.remote_path_dir), 'Expected the directory is created.')
        self.assertTrue(self.client.check(self.remote_path_file), 'Expected the file is uploaded.')

    def test_valid(self):
        self.assertTrue(self.client.valid())

    def test_check_is_overridden(self):
        self.assertEqual('GET', self.client.requests['check'])

    def test_pull_newer(self):
        init_modification_time = int(self._prepare_local_test_file_and_get_modification_time())
        sleep(1)
        self._prepare_for_downloading(base_path='time/')
        result = self.client.pull('time/' + self.remote_path_dir, self.local_path_dir)
        update_modification_time = int(os.path.getmtime(self.pulled_file))
        self.assertTrue(result)
        self.assertGreater(update_modification_time, init_modification_time)
        self.client.clean(remote_path='time/' + self.remote_path_dir)

    def test_pull_older(self):
        self._prepare_for_downloading(base_path='time/')
        sleep(1)
        init_modification_time = int(self._prepare_local_test_file_and_get_modification_time())
        result = self.client.pull('time/' + self.remote_path_dir, self.local_path_dir)
        update_modification_time = int(os.path.getmtime(self.pulled_file))
        self.assertFalse(result)
        self.assertEqual(update_modification_time, init_modification_time)
        self.client.clean(remote_path='time/' + self.remote_path_dir)

    def test_push_newer(self):
        self._prepare_for_downloading(base_path='time/')
        sleep(1)
        self._prepare_for_uploading()
        init_modification_time = self.client.info('time/' + self.remote_path_file)['modified']
        result = self.client.push('time/' + self.remote_path_dir, self.local_path_dir)
        update_modification_time = self.client.info('time/' + self.remote_path_file)['modified']
        self.assertTrue(result)
        self.assertNotEqual(init_modification_time, update_modification_time)
        self.client.clean(remote_path='time/' + self.remote_path_dir)

    def test_push_older(self):
        self._prepare_for_uploading()
        sleep(1)
        self._prepare_for_downloading(base_path='time/')
        init_modification_time = self.client.info('time/' + self.remote_path_file)['modified']
        result = self.client.push('time/' + self.remote_path_dir, self.local_path_dir)
        update_modification_time = self.client.info('time/' + self.remote_path_file)['modified']
        self.assertFalse(result)
        self.assertEqual(init_modification_time, update_modification_time)
        self.client.clean(remote_path='time/' + self.remote_path_dir)

    def _prepare_local_test_file_and_get_modification_time(self):
        if not path.exists(path=self.local_path_dir):
            os.mkdir(self.local_path_dir)
        if not path.exists(path=self.local_path_dir + os.sep + self.local_file):
            shutil.copy(src=self.local_file_path, dst=self.pulled_file)
        return os.path.getmtime(self.pulled_file)


if __name__ == '__main__':
    unittest.main()
