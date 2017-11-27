class WebDavException(Exception):
    pass


class NotValid(WebDavException):
    pass


class OptionNotValid(NotValid):
    def __init__(self, name, value, ns=""):
        self.name = name
        self.value = value
        self.ns = ns

    def __str__(self):
        return "Option ({ns}{name}={value}) have invalid name or value".format(ns=self.ns, name=self.name,
                                                                               value=self.value)


class CertificateNotValid(NotValid):
    pass


class NotFound(WebDavException):
    pass


class LocalResourceNotFound(NotFound):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return "Local file: {path} not found".format(path=self.path)


class RemoteResourceNotFound(NotFound):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return "Remote resource: {path} not found".format(path=self.path)


class RemoteParentNotFound(NotFound):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return "Remote parent for: {path} not found".format(path=self.path)


class ResourceTooBig(WebDavException):
    def __init__(self, path, size, max_size):
        self.path = path
        self.size = size
        self.max_size = max_size

    def __str__(self):
        return "Resource {path} is too big, it should be less then {max_size} but actually: {size}".format(
            path=self.path,
            max_size=self.max_size,
            size=self.size)


class MethodNotSupported(WebDavException):
    def __init__(self, name, server):
        self.name = name
        self.server = server

    def __str__(self):
        return "Method {name} not supported for {server}".format(name=self.name, server=self.server)


class ConnectionException(WebDavException):
    def __init__(self, exception):
        self.exception = exception

    def __str__(self):
        return self.exception.__str__()


class NoConnection(WebDavException):
    def __init__(self, hostname):
        self.hostname = hostname

    def __str__(self):
        return "Not connection with {hostname}".format(hostname=self.hostname)


# This exception left only for supporting original library interface.
class NotConnection(WebDavException):
    def __init__(self, hostname):
        self.hostname = hostname

    def __str__(self):
        return "No connection with {hostname}".format(hostname=self.hostname)


class ResponseErrorCode(WebDavException):
    def __init__(self, url, code, message):
        self.url = url
        self.code = code
        self.message = message

    def __str__(self):
        return "Request to {url} failed with code {code} and message: {message}".format(url=self.url, code=self.code,
                                                                                        message=self.message)


class NotEnoughSpace(WebDavException):
    def __init__(self):
        pass

    def __str__(self):
        return "Not enough space on the server"
