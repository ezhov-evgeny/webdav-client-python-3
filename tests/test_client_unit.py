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
        result = utils.parse_get_list_response(content)
        self.assertEquals(result.__len__(), 2)

    def test_create_free_space_request_content(self):
        result = utils.create_free_space_request_content()
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                  '<quota-available-bytes/><quota-used-bytes/></prop></propfind>')

    def test_parse_free_space_response(self):
        content = '<?xml version="1.0" encoding="utf-8"?><d:multistatus xmlns:d="DAV:"><d:response><d:href>/</d:href>' \
                  '<d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop><d:quota-used-bytes>697' \
                  '</d:quota-used-bytes><d:quota-available-bytes>10737417543</d:quota-available-bytes></d:prop>' \
                  '</d:propstat></d:response></d:multistatus>'
        result = utils.parse_free_space_response(content, 'localhost')
        self.assertEquals(result, 10737417543)

    def test_parse_info_response(self):
        content = '<?xml version="1.0" encoding="utf-8"?><d:multistatus xmlns:d="DAV:"><d:response>' \
                  '<d:href>/test_dir/test.txt</d:href><d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop>' \
                  '<d:resourcetype/><d:getlastmodified>Wed, 18 Oct 2017 15:16:04 GMT</d:getlastmodified>' \
                  '<d:getetag>ab0b4b7973803c03639b848682b5f38c</d:getetag><d:getcontenttype>text/plain' \
                  '</d:getcontenttype><d:getcontentlength>41</d:getcontentlength><d:displayname>test.txt' \
                  '</d:displayname><d:creationdate>2017-10-18T15:16:04Z</d:creationdate></d:prop></d:propstat>' \
                  '</d:response></d:multistatus>'
        result = utils.parse_info_response(content, '/test_dir/test.txt', 'localhost')
        self.assertEquals(result['created'], '2017-10-18T15:16:04Z')
        self.assertEquals(result['name'], 'test.txt')
        self.assertEquals(result['modified'], 'Wed, 18 Oct 2017 15:16:04 GMT')
        self.assertEquals(result['size'], '41')

    def test_create_get_property_request_content(self):
        option = {
            'namespace': 'test',
            'name': 'aProperty'
        }
        result = utils.create_get_property_request_content(option=option, )
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                  '<aProperty xmlns="test"/></prop></propfind>')

    def test_create_get_property_request_content_name_only(self):
        option = {
            'name': 'aProperty'
        }
        result = utils.create_get_property_request_content(option=option)
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propfind xmlns="DAV:"><prop>'
                                  '<aProperty xmlns=""/></prop></propfind>')

    def test_parse_get_property_response(self):
        content = '<?xml version="1.0" encoding="utf-8"?><d:multistatus xmlns:d="DAV:"><d:response>' \
                  '<d:href>/test_dir/test.txt</d:href><d:propstat><d:status>HTTP/1.1 200 OK</d:status><d:prop>' \
                  '<aProperty xmlns="test">aValue</aProperty></d:prop></d:propstat></d:response></d:multistatus>'

        result = utils.parse_get_property_response(content=content, name='aProperty')
        self.assertEquals(result, 'aValue')

    def test_create_set_one_property_request_content(self):
        option = {
            'namespace': 'test',
            'name': 'aProperty',
            'value': 'aValue'
        }
        result = utils.create_set_property_batch_request_content(options=[option])
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                  '<aProperty xmlns="test">aValue</aProperty></prop></set></propertyupdate>')

    def test_create_set_one_property_request_content_name_only(self):
        option = {
            'name': 'aProperty'
        }
        result = utils.create_set_property_batch_request_content(options=[option])
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                  '<aProperty xmlns=""></aProperty></prop></set></propertyupdate>')

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
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                  '<aProperty xmlns="test">aValue</aProperty><aProperty2 xmlns="test2">aValue2'
                                  '</aProperty2></prop></set></propertyupdate>')

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
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<propertyupdate xmlns="DAV:"><set><prop>'
                                  '<aProperty xmlns=""></aProperty><aProperty2 xmlns=""></aProperty2></prop></set>'
                                  '</propertyupdate>')

    def test_etree_to_string(self):
        tree = ElementTree(Element('test'))
        result = utils.etree_to_string(tree)
        self.assertEquals(result, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<test/>')


if __name__ == '__main__':
    unittest.main()
