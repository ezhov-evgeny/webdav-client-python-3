from os.path import exists

from webdav3.exceptions import *
from webdav3.urn import Urn


class ConnectionSettings:
    def is_valid(self):
        pass

    def valid(self):

        try:
            self.is_valid()
        except OptionNotValid:
            return False
        else:
            return True


class WebDAVSettings(ConnectionSettings):
    ns = "webdav:"
    prefix = "webdav_"
    keys = {'hostname', 'login', 'password', 'token', 'root', 'cert_path', 'key_path', 'recv_speed', 'send_speed',
            'verbose', 'disable_check'}

    hostname = None
    login = None
    password = None
    token = None
    root = None
    cert_path = None
    key_path = None
    recv_speed = None
    send_speed = None
    verbose = None
    disable_check = False

    def __init__(self, options):

        self.options = dict()

        for key in self.keys:
            value = options.get(key, '')
            self.options[key] = value
            self.__dict__[key] = value

        self.root = Urn(self.root).quote() if self.root else ''
        self.root = self.root.rstrip(Urn.separate)

    def is_valid(self):

        if not self.hostname:
            raise OptionNotValid(name="hostname", value=self.hostname, ns=self.ns)

        if self.cert_path and not exists(self.cert_path):
            raise OptionNotValid(name="cert_path", value=self.cert_path, ns=self.ns)

        if self.key_path and not exists(self.key_path):
            raise OptionNotValid(name="key_path", value=self.key_path, ns=self.ns)

        if self.key_path and not self.cert_path:
            raise OptionNotValid(name="cert_path", value=self.cert_path, ns=self.ns)

        if self.password and not self.login:
            raise OptionNotValid(name="login", value=self.login, ns=self.ns)

        if not self.token and not self.login:
            raise OptionNotValid(name="login", value=self.login, ns=self.ns)
