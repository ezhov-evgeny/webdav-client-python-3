# coding=utf-8
import unittest
from unittest import TestCase

from lxml.etree import ElementTree, Element

from webdav3.client import WebDavXmlUtils as utils


class ClientTestCase(TestCase):
    def test_parse_get_list_response(self):
        content = '<?xml version="1.0" encoding="utf-8"?><d:multistatus xmlns:d="DAV:"><d:response><d:href>/test_dir/' \
                  '</d:href><d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop><d:resourcetype><d:collection/>' \
                  '</d:resourcetype><d:getlastmodified>Mon, 16 Oct 2017 04:18:00 GMT</d:getlastmodified>' \
                  '<d:displayname>test_dir</d:displayname><d:creationdate>2017-10-16T04:18:00Z</d:creationdate>' \
                  '</d:prop></d:propstat></d:response><d:response><d:href>/test_dir/test.txt/</d:href><d:propstat>' \
                  '<d:status>HTTP/1.1 200 OK</d:status><d:prop><d:resourcetype><d:collection/></d:resourcetype>' \
                  '<d:getlastmodified>Mon, 16 Oct 2017 04:18:18 GMT</d:getlastmodified><d:displayname>test.txt' \
                  '</d:displayname><d:creationdate>2017-10-16T04:18:18Z</d:creationdate></d:prop></d:propstat>' \
                  '</d:response></d:multistatus>'
        result = utils.parse_get_list_response(content.encode('utf-8'))
        self.assertEqual(result.__len__(), 2)

    def test_create_free_space_request_content(self):
        result = utils.create_free_space_request_content()
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                 b'<quota-available-bytes/><quota-used-bytes/></prop></propfind>')

    def test_parse_free_space_response(self):
        content = '<?xml version="1.0" encoding="utf-8"?><d:multistatus xmlns:d="DAV:"><d:response><d:href>/</d:href>' \
                  '<d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop><d:quota-used-bytes>697' \
                  '</d:quota-used-bytes><d:quota-available-bytes>10737417543</d:quota-available-bytes></d:prop>' \
                  '</d:propstat></d:response></d:multistatus>'
        result = utils.parse_free_space_response(content.encode('utf-8'), 'localhost')
        self.assertEqual(result, 10737417543)

    def test_parse_info_response(self):
        content = '<?xml version="1.0" encoding="utf-8"?><d:multistatus xmlns:d="DAV:"><d:response>' \
                  '<d:href>/test_dir/test.txt</d:href><d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop>' \
                  '<d:resourcetype/><d:getlastmodified>Wed, 18 Oct 2017 15:16:04 GMT</d:getlastmodified>' \
                  '<d:getetag>ab0b4b7973803c03639b848682b5f38c</d:getetag><d:getcontenttype>text/plain' \
                  '</d:getcontenttype><d:getcontentlength>41</d:getcontentlength><d:displayname>test.txt' \
                  '</d:displayname><d:creationdate>2017-10-18T15:16:04Z</d:creationdate></d:prop></d:propstat>' \
                  '</d:response></d:multistatus>'
        result = utils.parse_info_response(content.encode('utf-8'), '/test_dir/test.txt', 'localhost')
        self.assertEqual(result['created'], '2017-10-18T15:16:04Z')
        self.assertEqual(result['name'], 'test.txt')
        self.assertEqual(result['modified'], 'Wed, 18 Oct 2017 15:16:04 GMT')
        self.assertEqual(result['size'], '41')

    def test_create_get_property_request_content(self):
        option = {
            'namespace': 'test',
            'name': 'aProperty'
        }
        result = utils.create_get_property_request_content(option=option, )
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                 b'<aProperty xmlns="test"/></prop></propfind>')

    def test_create_get_property_request_content_name_only(self):
        option = {
            'name': 'aProperty'
        }
        result = utils.create_get_property_request_content(option=option)
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                 b'<aProperty xmlns=""/></prop></propfind>')

    def test_parse_get_property_response(self):
        content = '<?xml version="1.0" encoding="utf-8"?><d:multistatus xmlns:d="DAV:"><d:response>' \
                  '<d:href>/test_dir/test.txt</d:href><d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop>' \
                  '<aProperty xmlns="test">aValue</aProperty></d:prop></d:propstat></d:response></d:multistatus>'

        result = utils.parse_get_property_response(content=content.encode('utf-8'), name='aProperty')
        self.assertEqual(result, 'aValue')

    def test_create_set_one_property_request_content(self):
        option = {
            'namespace': 'test',
            'name': 'aProperty',
            'value': 'aValue'
        }
        result = utils.create_set_property_batch_request_content(options=[option])
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                 b'<aProperty xmlns="test">aValue</aProperty></prop></set></propertyupdate>')

    def test_create_set_one_property_request_content_name_only(self):
        option = {
            'name': 'aProperty'
        }
        result = utils.create_set_property_batch_request_content(options=[option])
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
        result = utils.create_set_property_batch_request_content(options=options)
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
        result = utils.create_set_property_batch_request_content(options=options)
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                 b'<aProperty xmlns=""></aProperty><aProperty2 xmlns=""></aProperty2></prop></set>'
                                 b'</propertyupdate>')

    def test_etree_to_string(self):
        tree = ElementTree(Element('test'))
        result = utils.etree_to_string(tree)
        self.assertEqual(result, b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<test/>')

    def test_parse_is_dir_response_directory(self):
        try:
            f = open('./tests/response_dir.xml', encoding='utf-8')
            content = f.read().encode('utf-8')
        except:
            f = open('./tests/response_dir.xml')
            content = f.read().decode('utf-8').encode('utf-8')
        f.close()
        path = '/test_dir'
        hostname = 'https://webdav.yandex.ru'
        result = utils.parse_is_dir_response(content, path, hostname)
        self.assertTrue(result, 'It should be directory')

    def test_parse_is_dir_response_file(self):
        content = '<?xml version=\'1.0\' encoding=\'UTF-8\'?><d:multistatus xmlns:d="DAV:"><d:response><d:href>/test_' \
                  'dir/</d:href><d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop><d:creationdate>2018-05-10T07' \
                  ':40:11Z</d:creationdate><d:displayname>test_dir</d:displayname><d:getlastmodified>Thu, 10 May 2018' \
                  ' 07:40:11 GMT</d:getlastmodified><d:resourcetype/></d:prop></d:propstat></d:response><d:response><' \
                  'd:href>/test_dir/test.txt</d:href><d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop><d:getet' \
                  'ag>ab0b4b7973803c03639b848682b5f38c</d:getetag><d:creationdate>2018-05-10T07:40:12Z</d:creationdat' \
                  'e><d:displayname>test.txt</d:displayname><d:getlastmodified>Thu, 10 May 2018 07:40:12 GMT</d:getla' \
                  'stmodified><d:getcontenttype>text/plain</d:getcontenttype><d:getcontentlength>41</d:getcontentleng' \
                  'th><d:resourcetype/></d:prop></d:propstat></d:response></d:multistatus>'
        path = '/test_dir/test.txt'
        hostname = 'https://webdav.yandex.ru'
        result = utils.parse_is_dir_response(content.encode('utf-8'), path, hostname)
        self.assertFalse(result, 'It should be file')


if __name__ == '__main__':
    unittest.main()
