import unittest

from webdav3.client import get_options
from webdav3.connection import WebDAVSettings, OptionNotValid, ConnectionSettings


class ConnectionTestCase(unittest.TestCase):
    def test_connection_settings_valid(self):
        options = {
            'webdav_hostname': 'http://localhost:8585',
            'webdav_login': 'alice',
            'webdav_password': 'secret1234'
        }
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        settings = WebDAVSettings(webdav_options)
        self.assertTrue(settings.is_valid())
        self.assertTrue(settings.valid())

    def test_connection_settings_no_hostname(self):
        options = {
            'webdav_login': 'alice',
            'webdav_password': 'secret1234'
        }
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        settings = WebDAVSettings(webdav_options)
        self.assertRaises(OptionNotValid, settings.is_valid)
        self.assertFalse(settings.valid())

    def test_connection_settings_no_login(self):
        options = {
            'webdav_hostname': 'http://localhost:8585',
            'webdav_password': 'secret1234'
        }
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        settings = WebDAVSettings(webdav_options)
        self.assertRaises(OptionNotValid, settings.is_valid)
        self.assertFalse(settings.valid())

    def test_connection_settings_no_token_and_no_login(self):
        options = {
            'webdav_hostname': 'http://localhost:8585'
        }
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        settings = WebDAVSettings(webdav_options)
        self.assertRaises(OptionNotValid, settings.is_valid)
        self.assertFalse(settings.valid())

    def test_connection_settings_wrong_cert_path(self):
        options = {
            'webdav_hostname': 'http://localhost:8585',
            'webdav_login': 'alice',
            'cert_path': './wrong.file',
            'webdav_password': 'secret1234'
        }
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        settings = WebDAVSettings(webdav_options)
        self.assertRaises(OptionNotValid, settings.is_valid)
        self.assertFalse(settings.valid())

    def test_connection_settings_wrong_key_path(self):
        options = {
            'webdav_hostname': 'http://localhost:8585',
            'webdav_login': 'alice',
            'key_path': './wrong.file',
            'webdav_password': 'secret1234'
        }
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        settings = WebDAVSettings(webdav_options)
        self.assertRaises(OptionNotValid, settings.is_valid)
        self.assertFalse(settings.valid())

    def test_connection_settings_with_key_path_an_no_cert_path(self):
        options = {
            'webdav_hostname': 'http://localhost:8585',
            'webdav_login': 'alice',
            'key_path': './publish.sh',
            'webdav_password': 'secret1234'
        }
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        settings = WebDAVSettings(webdav_options)
        self.assertRaises(OptionNotValid, settings.is_valid)
        self.assertFalse(settings.valid())

    def test_connection_settings_does_nothing(self):
        settings = ConnectionSettings()
        settings.is_valid()
        self.assertTrue(settings.valid())


if __name__ == '__main__':
    unittest.main()
