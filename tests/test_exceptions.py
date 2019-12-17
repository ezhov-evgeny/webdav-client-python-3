import unittest

from webdav3.exceptions import OptionNotValid, LocalResourceNotFound, RemoteResourceNotFound, MethodNotSupported, ConnectionException, NoConnection, \
    RemoteParentNotFound, NotConnection, ResponseErrorCode, NotEnoughSpace


class ExceptionsTestCase(unittest.TestCase):
    def test_option_not_valid(self):
        exception = OptionNotValid('Name', 'Value', 'Namespace/')
        self.assertEqual("Option (Namespace/Name=Value) have invalid name or value", exception.__str__())

    def test_local_resource_not_found(self):
        exception = LocalResourceNotFound('Path')
        self.assertEqual("Local file: Path not found", exception.__str__())

    def test_remote_resource_not_found(self):
        exception = RemoteResourceNotFound('Path')
        self.assertEqual("Remote resource: Path not found", exception.__str__())

    def test_remote_parent_not_found(self):
        exception = RemoteParentNotFound('Path')
        self.assertEqual("Remote parent for: Path not found", exception.__str__())

    def test_method_not_supported(self):
        exception = MethodNotSupported('HEAD', 'Server')
        self.assertEqual("Method 'HEAD' not supported for Server", exception.__str__())

    def test_connection_exception(self):
        exception = ConnectionException(MethodNotSupported('HEAD', 'Server'))
        self.assertEqual("Method 'HEAD' not supported for Server", exception.__str__())

    def test_no_connection(self):
        exception = NoConnection('Server')
        self.assertEqual("No connection with Server", exception.__str__())

    def test_not_connection_legacy(self):
        exception = NotConnection('Server')
        self.assertEqual("No connection with Server", exception.__str__())

    def test_response_error_code(self):
        exception = ResponseErrorCode('http://text/', 502, 'Service Unavailable')
        self.assertEqual("Request to http://text/ failed with code 502 and message: Service Unavailable", exception.__str__())

    def test_not_enough_space(self):
        exception = NotEnoughSpace()
        self.assertEqual("Not enough space on the server", exception.__str__())


if __name__ == '__main__':
    unittest.main()
