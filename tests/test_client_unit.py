# coding=utf-8
import unittest
from unittest import TestCase

from lxml.etree import ElementTree, Element

from webdav3.client import WebDavXmlUtils as Utils, listdir, MethodNotSupported, RemoteResourceNotFound


def read_file_content(file_name):
    with open(file_name, encoding='utf-8') as f:
        return f.read().encode('utf-8')


class ClientTestCase(TestCase):
    def test_parse_get_list_response(self):
        content = read_file_content('./tests/responses/get_list.xml')
        result = Utils.parse_get_list_response(content)
        self.assertEqual(result.__len__(), 2)
        self.assertTrue(result[0].is_dir(), '{} should be marked as directory'.format(result[0].path()))
        self.assertFalse(result[1].is_dir(), '{} should be marked as file'.format(result[1].path()))
        self.assertEqual(result[1].__str__(), '/test_dir/test.txt')

    def test_parse_get_list_response_empty(self):
        content = read_file_content('./tests/responses/get_list_empty.xml')
        result = Utils.parse_get_list_response(content)
        self.assertEqual(result.__len__(), 0)

    def test_parse_get_list_response_incorrect(self):
        content = read_file_content('./tests/responses/get_list_incorrect.xml')
        result = Utils.parse_get_list_response(content)
        self.assertEqual(result.__len__(), 0)

    def test_parse_get_list_response_dirs(self):
        content = read_file_content('./tests/responses/get_list_directories.xml')
        result = Utils.parse_get_list_response(content)
        self.assertEqual(result.__len__(), 5)
        for d in result:
            self.assertTrue(d.is_dir(), '{} should be marked as directory'.format(d.path()))

    def test_create_free_space_request_content(self):
        result = Utils.create_free_space_request_content()
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                 b'<quota-available-bytes/><quota-used-bytes/></prop></propfind>')

    def test_parse_free_space_response(self):
        content = read_file_content('./tests/responses/free_space.xml')
        result = Utils.parse_free_space_response(content, 'localhost')
        self.assertEqual(result, 10737417543)

    def test_parse_free_space_response_not_supported(self):
        content = read_file_content('./tests/responses/free_space_not_supported.xml')
        self.assertRaises(MethodNotSupported, Utils.parse_free_space_response, content, 'localhost')

    def test_parse_free_space_response(self):
        content = read_file_content('./tests/responses/free_space_incorrect.xml')
        result = Utils.parse_free_space_response(content, 'localhost')
        self.assertEqual(result, '')

    def test_parse_info_response(self):
        content = read_file_content('./tests/responses/get_info.xml')
        result = Utils.parse_info_response(content, '/test_dir/test.txt', 'localhost')
        self.assertEqual(result['created'], '2017-10-18T15:16:04Z')
        self.assertEqual(result['name'], 'test.txt')
        self.assertEqual(result['modified'], 'Wed, 18 Oct 2017 15:16:04 GMT')
        self.assertEqual(result['size'], '41')

    def test_create_get_property_request_content(self):
        option = {
            'namespace': 'test',
            'name': 'aProperty'
        }
        result = Utils.create_get_property_request_content(option=option, )
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                 b'<aProperty xmlns="test"/></prop></propfind>')

    def test_create_get_property_request_content_name_only(self):
        option = {
            'name': 'aProperty'
        }
        result = Utils.create_get_property_request_content(option=option)
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                 b'<aProperty xmlns=""/></prop></propfind>')

    def test_parse_get_property_response(self):
        content = read_file_content('./tests/responses/get_property.xml')
        result = Utils.parse_get_property_response(content=content, name='aProperty')
        self.assertEqual(result, 'aValue')

    def test_create_set_one_property_request_content(self):
        option = {
            'namespace': 'test',
            'name': 'aProperty',
            'value': 'aValue'
        }
        result = Utils.create_set_property_batch_request_content(options=[option])
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                 b'<aProperty xmlns="test">aValue</aProperty></prop></set></propertyupdate>')

    def test_create_set_one_property_request_content_name_only(self):
        option = {
            'name': 'aProperty'
        }
        result = Utils.create_set_property_batch_request_content(options=[option])
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                 b'<aProperty xmlns=""></aProperty></prop></set></propertyupdate>')

    def test_create_set_property_batch_request_content(self):
        options = [
            {
                'namespace': 'test',
                'name': 'aProperty',
                'value': 'aValue'
            },
            {
                'namespace': 'test2',
                'name': 'aProperty2',
                'value': 'aValue2'
            }
        ]
        result = Utils.create_set_property_batch_request_content(options=options)
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                 b'<aProperty xmlns="test">aValue</aProperty><aProperty2 xmlns="test2">aValue2'
                                 b'</aProperty2></prop></set></propertyupdate>')

    def test_create_set_property_batch_request_content_name_only(self):
        options = [
            {
                'name': 'aProperty'
            },
            {
                'name': 'aProperty2'
            }
        ]
        result = Utils.create_set_property_batch_request_content(options=options)
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                 b'<aProperty xmlns=""></aProperty><aProperty2 xmlns=""></aProperty2></prop></set>'
                                 b'</propertyupdate>')

    def test_etree_to_string(self):
        tree = ElementTree(Element('test'))
        result = Utils.etree_to_string(tree)
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<test/>')

    def test_parse_is_dir_response_not_supported(self):
        content = read_file_content('./tests/responses/is_dir_directory_not_supported.xml')
        path = '/test_dir'
        hostname = 'https://webdav.yandex.ru'
        self.assertRaises(MethodNotSupported, Utils.parse_is_dir_response, content, path, hostname)

    def test_parse_is_dir_response_directory(self):
        content = read_file_content('./tests/responses/is_dir_directory.xml')
        path = '/test_dir'
        hostname = 'https://webdav.yandex.ru'
        result = Utils.parse_is_dir_response(content, path, hostname)
        self.assertTrue(result, 'It should be directory')

    def test_parse_is_dir_response_file(self):
        content = read_file_content('./tests/responses/is_dir_file.xml')
        path = '/test_dir/test.txt'
        hostname = 'https://webdav.yandex.ru'
        result = Utils.parse_is_dir_response(content, path, hostname)
        self.assertFalse(result, 'It should be file')

    def test_listdir_inner_dir(self):
        file_names = listdir('.')
        self.assertGreater(len(file_names), 0)
        self.assertTrue('webdav3/' in file_names)

    def test_extract_response_for_path_not_supported(self):
        self.assertRaises(MethodNotSupported, Utils.extract_response_for_path, 'WrongXML', 'test', 'https://webdav.ru')

    def test_extract_response_for_path_not_found(self):
        content = read_file_content('./tests/responses/is_dir_directory.xml')
        hostname = 'https://webdav.yandex.ru'
        self.assertRaises(RemoteResourceNotFound, Utils.extract_response_for_path, content, 'wrong_name', hostname)

    def test_parse_is_dir_response_file_with_prefix(self):
        content = read_file_content('./tests/responses/is_dir_file.xml')
        path = '/test.txt'
        hostname = 'https://webdav.yandex.ru/test_dir/'
        result = Utils.parse_is_dir_response(content, path, hostname)
        self.assertFalse(result, 'It should be file')

    def test_utils_created(self):
        self.assertIsNotNone(Utils())


if __name__ == '__main__':
    unittest.main()
