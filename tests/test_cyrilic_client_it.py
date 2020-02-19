import os
import unittest

from tests.test_client_it import ClientTestCase


class MultiClientTestCase(ClientTestCase):
    remote_path_file = 'директория/тестовый.txt'
    remote_path_file2 = 'директория/тестовый2.txt'
    remote_inner_path_file = 'директория/вложенная/тестовый.txt'
    remote_path_dir = 'директория'
    remote_path_dir2 = 'директория2'
    remote_inner_path_dir = 'директория/вложенная'
    inner_dir_name = 'вложенная'
    local_base_dir = 'tests/'
    local_file = 'тестовый.txt'
    local_file_path = local_base_dir + 'тестовый.txt'
    local_path_dir = local_base_dir + 'res/директория'
    pulled_file = local_path_dir + os.sep + local_file


if __name__ == '__main__':
    unittest.main()
