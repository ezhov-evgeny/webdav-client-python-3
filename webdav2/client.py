# -*- coding: utf-8

import functools
import logging
import os
import shutil
import threading
from io import BytesIO
from re import sub

import lxml.etree as etree
import requests

from webdav2.connection import *
from webdav2.exceptions import *
from webdav2.urn import Urn

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

__version__ = "0.2"
log = logging.getLogger(__name__)


def listdir(directory):
    """Returns list of nested files and directories for local directory by path

    :param directory: absolute or relative path to local directory
    :return: list nested of file or directory names
    """
    file_names = list()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isdir(file_path):
            filename = "{filename}{separate}".format(filename=filename, separate=os.path.sep)
        file_names.append(filename)
    return file_names


def get_options(option_type, from_options):
    """Extract options for specified option type from all options

    :param option_type: the object of specified type of options
    :param from_options: all options dictionary
    :return: the dictionary of options for specified type, each option can be filled by value from all options
             dictionary or blank in case the option for specified type is not exist in all options dictionary
    """
    _options = dict()

    for key in option_type.keys:
        key_with_prefix = "{prefix}{key}".format(prefix=option_type.prefix, key=key)
        if key not in from_options and key_with_prefix not in from_options:
            _options[key] = ""
        elif key in from_options:
            _options[key] = from_options.get(key)
        else:
            _options[key] = from_options.get(key_with_prefix)

    return _options


def wrap_connection_error(fn):
    @functools.wraps(fn)
    def _wrapper(self, *args, **kw):
        log.debug("Requesting %s(%s, %s)", fn, args, kw)
        try:
            res = fn(self, *args, **kw)
        except requests.ConnectionError:
            raise NotConnection(self.webdav.hostname)
        else:
            return res

    return _wrapper


class Client(object):
    """The client for WebDAV servers provides an ability to control files on remote WebDAV server.
    """
    # path to root directory of WebDAV
    root = '/'

    # Max size of file for uploading
    large_size = 2 * 1024 * 1024 * 1024

    # HTTP headers for different actions
    http_header = {
        'list': ["Accept: */*", "Depth: 1"],
        'free': ["Accept: */*", "Depth: 0", "Content-Type: text/xml"],
        'copy': ["Accept: */*"],
        'move': ["Accept: */*"],
        'mkdir': ["Accept: */*", "Connection: Keep-Alive"],
        'clean': ["Accept: */*", "Connection: Keep-Alive"],
        'check': ["Accept: */*"],
        'info': ["Accept: */*", "Depth: 1"],
        'get_metadata': ["Accept: */*", "Depth: 1", "Content-Type: application/x-www-form-urlencoded"],
        'set_metadata': ["Accept: */*", "Depth: 1", "Content-Type: application/x-www-form-urlencoded"]
    }

    def get_header(self, action):
        """Returns HTTP headers of specified WebDAV actions

        :param action: the identifier of action
        :return: the dictionary of headers for specified action
        """
        if action in Client.http_header:
            try:
                header = Client.http_header[action].copy()
            except AttributeError:
                header = Client.http_header[action][:]
        else:
            header = list()

        if self.webdav.token:
            webdav_token = "Authorization: OAuth {token}".format(token=self.webdav.token)
            header.append(webdav_token)
        return dict([map(lambda s: s.strip(), i.split(':')) for i in header])

    def get_url(self, path):
        """Generates url by uri path.

        :param path: uri path.
        :return: the url string.
        """
        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': path}
        return "{hostname}{root}{path}".format(**url)

    def execute_request(self, action, path, data=None):
        """Generate request to WebDAV server for specified action and path and execute it.

        :param action: the action for WebDAV server which should be executed.
        :param path: the path to resource for action
        :param data: (optional) Dictionary or list of tuples ``[(key, value)]`` (will be form-encoded), bytes,
                     or file-like object to send in the body of the :class:`Request`.
        :return: HTTP response of request.
        """
        response = requests.request(
            method=Client.requests[action],
            url=self.get_url(path),
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header(action),
            data=data
        )
        if response.status_code == 507:
            raise NotEnoughSpace()
        if response.status_code >= 400:
            raise ResponseErrorCode(url=self.get_url(path), code=response.status_code, message=response.content)
        return response

    # mapping of actions to WebDAV methods
    requests = {
        'download': "GET",
        'download_to': "GET",
        'download_file': "GET",
        'upload_from': "PUT",
        'upload_file': "PUT",
        'copy': "COPY",
        'move': "MOVE",
        'mkdir': "MKCOL",
        'clean': "DELETE",
        'check': "HEAD",
        'list': "PROPFIND",
        'free': "PROPFIND",
        'info': "PROPFIND",
        'publish': "PROPPATCH",
        'unpublish': "PROPPATCH",
        'published': "PROPPATCH",
        'get_metadata': "PROPFIND",
        'set_metadata': "PROPPATCH"
    }

    meta_xmlns = {
        'https://webdav.yandex.ru': "urn:yandex:disk:meta",
    }

    def __init__(self, options):
        """Constructor of WebDAV client

        :param options: the dictionary of connection options to WebDAV can include proxy server options.
            WebDev settings:
            `webdav_hostname`: url for WebDAV server should contain protocol and ip address or domain name.
                               Example: `https://webdav.server.com`.
            `webdav_login`: (optional) login name for WebDAV server can be empty in case using of token auth.
            `webdav_password`: (optional) password for WebDAV server can be empty in case using of token auth.
            `webdav_token': (optional) token for WebDAV server can be empty in case using of login/password auth.
            `webdav_root`: (optional) root directory of WebDAV server. Defaults is `/`.
            `webdav_cert_path`: (optional) path to certificate.
            `webdav_key_path`: (optional) path to private key.
            `webdav_recv_speed`: (optional) rate limit data download speed in Bytes per second.
                                 Defaults to unlimited speed.
            `webdav_send_speed`: (optional) rate limit data upload speed in Bytes per second.
                                 Defaults to unlimited speed.
            `webdav_verbose`: (optional) set verbose mode on.off. By default verbose mode is off.
            Proxy settings (optional):
             `proxy_hostname`: url to proxy server should contain protocol and ip address or domain name and if needed
                               port. Example: `https://proxy.server.com:8383`.
             `proxy_login`: login name for proxy server.
             `proxy_password`: password for proxy server.
        """
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)
        proxy_options = get_options(option_type=ProxySettings, from_options=options)

        self.webdav = WebDAVSettings(webdav_options)
        self.proxy = ProxySettings(proxy_options)
        self.default_options = {}

    def valid(self):
        """Validates of WebDAV and proxy settings.

        :return: True in case settings are valid and False otherwise.
        """
        return True if self.webdav.valid() and self.proxy.valid() else False

    @wrap_connection_error
    def list(self, remote_path=root):
        """Returns list of nested files and directories for remote WebDAV directory by path.

        :param remote_path: path to remote directory.
        :return: list of nested file or directory names.
        """

        def parse(list_response):
            """Parses of response from WebDAV server and extract file and directory names.

            :param list_response: HTTP response from WebDAV server for getting list of files by remote path.
            :return: list of extracted file or directory names.
            """
            try:
                response_str = list_response.content
                tree = etree.fromstring(response_str)
                hrees = [unquote(hree.text) for hree in tree.findall(".//{DAV:}href")]
                return [Urn(hree) for hree in hrees]
            except etree.XMLSyntaxError:
                return list()

        directory_urn = Urn(remote_path, directory=True)

        if directory_urn.path() != Client.root:
            if not self.check(directory_urn.path()):
                raise RemoteResourceNotFound(directory_urn.path())

        response = self.execute_request(action='list', path=directory_urn.quote())
        urns = parse(response)

        path = "{root}{path}".format(root=self.webdav.root, path=directory_urn.path())
        return [urn.filename() for urn in urns if urn.path() != path and urn.path() != path[:-1]]

    @wrap_connection_error
    def free(self):
        """Returns an amount of free space on remote WebDAV server.

        :return: an amount of free space in bytes.
        """

        def parse(free_response):
            """Parses of response from WebDAV server and extract na amount of free space.

            :param free_response: HTTP response from WebDAV server for getting free space.
            :return: an amount of free space in bytes.
            """
            try:
                response_str = free_response.content
                tree = etree.fromstring(response_str)
                node = tree.find('.//{DAV:}quota-available-bytes')
                if node is not None:
                    return int(node.text)
                else:
                    raise MethodNotSupported(name='free', server=self.webdav.hostname)
            except TypeError:
                raise MethodNotSupported(name='free', server=self.webdav.hostname)
            except etree.XMLSyntaxError:
                return str()

        def data():
            root = etree.Element("propfind", xmlns="DAV:")
            prop = etree.SubElement(root, "prop")
            etree.SubElement(prop, "quota-available-bytes")
            etree.SubElement(prop, "quota-used-bytes")
            tree = etree.ElementTree(root)
            buff = BytesIO()
            tree.write(buff)
            return buff.getvalue()

        response = self.execute_request(action='free', path='', data=data())

        return parse(response)

    @wrap_connection_error
    def check(self, remote_path=root):
        """Checks an existence of remote resource on WebDAV server by remote path

        :param remote_path: (optional) path to resource on WebDAV server. Defaults is root directory of WebDAV.
        :return: True if resource is exist or False otherwise
        """
        urn = Urn(remote_path)
        try:
            response = self.execute_request(action='check', path=urn.quote())
        except ResponseErrorCode:
            return False

        if int(response.status_code) == 200:
            return True
        return False

    @wrap_connection_error
    def mkdir(self, remote_path):
        """Makes new directory on WebDAV server.

        :param remote_path: path to directory
        :return: True if request executed with code 200 and False otherwise.

        """
        directory_urn = Urn(remote_path, directory=True)

        if not self.check(directory_urn.parent()):
            raise RemoteParentNotFound(directory_urn.path())

        response = self.execute_request(action='mkdir', path=directory_urn.quote())

        return response.status_code == 200

    @wrap_connection_error
    def download_to(self, buff, remote_path):
        """Downloads file from WebDAV and writes it in buffer.

        :param buff: buffer object for writing of downloaded file content.
        :param remote_path: path to file on WebDAV server.
        """
        urn = Urn(remote_path)

        if self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_path)

        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        response = self.execute_request(action='download_to', path=urn.quote())

        buff.write(response.content)

    def download(self, remote_path, local_path, progress=None):
        """Downloads remote resource from WebDAV and save it in local path.

        :param remote_path: the path to remote resource for downloading can be file and directory.
        :param local_path: the path to save resource locally.
        :param progress: progress function. Not supported now.
        """
        urn = Urn(remote_path)
        if self.is_dir(urn.path()):
            self.download_directory(local_path=local_path, remote_path=remote_path, progress=progress)
        else:
            self.download_file(local_path=local_path, remote_path=remote_path, progress=progress)

    def download_directory(self, remote_path, local_path, progress=None):
        """Downloads directory and downloads all nested files and directories from remote WebDAV to local.
        If there is something on local path it deletes directories and files then creates new.

        :param remote_path: the path to directory for downloading form WebDAV server.
        :param local_path: the path to local directory for saving downloaded files and directories.
        :param progress: Progress function. Not supported now.
        """
        urn = Urn(remote_path, directory=True)

        if not self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_path)

        if os.path.exists(local_path):
            shutil.rmtree(local_path)

        os.makedirs(local_path)

        for resource_name in self.list(urn.path()):
            _remote_path = "{parent}{name}".format(parent=urn.path(), name=resource_name)
            _local_path = os.path.join(local_path, resource_name)
            self.download(local_path=_local_path, remote_path=_remote_path, progress=progress)

    @wrap_connection_error
    def download_file(self, remote_path, local_path, progress=None):
        """Downloads file from WebDAV server and save it locally.

        :param remote_path: the path to remote file for downloading.
        :param local_path: the path to save file locally.
        :param progress: progress function. Not supported now.
        """
        urn = Urn(remote_path)

        if self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_path)

        if os.path.isdir(local_path):
            raise OptionNotValid(name="local_path", value=local_path)

        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        with open(local_path, 'wb') as local_file:
            response = self.execute_request('download_file', urn.quote())

            for block in response.iter_content(1024):
                local_file.write(block)

    def download_sync(self, remote_path, local_path, callback=None):
        """Downloads remote resources from WebDAV server synchronously.

        :param remote_path: the path to remote resource on WebDAV server. Can be file and directory.
        :param local_path: the path to save resource locally.
        :param callback: the callback which will be invoked when downloading is complete.
        """
        self.download(local_path=local_path, remote_path=remote_path)

        if callback:
            callback()

    def download_async(self, remote_path, local_path, callback=None):
        """Downloads remote resources from WebDAV server asynchronously

        :param remote_path: the path to remote resource on WebDAV server. Can be file and directory.
        :param local_path: the path to save resource locally.
        :param callback: the callback which will be invoked when downloading is complete.
        """
        target = (lambda: self.download_sync(local_path=local_path, remote_path=remote_path, callback=callback))
        threading.Thread(target=target).start()

    @wrap_connection_error
    def upload_from(self, buff, remote_path):
        """Uploads file from buffer to remote path on WebDAV server.

        :param buff: the buffer with content for file.
        :param remote_path: the path to save file remotely on WebDAV server.
        """
        urn = Urn(remote_path)

        if urn.is_dir():
            raise OptionNotValid(name="remote_path", value=remote_path)

        if not self.check(urn.parent()):
            raise RemoteParentNotFound(urn.path())

        self.execute_request(action='upload_from', path=urn.quote(), data=buff)

    def upload(self, remote_path, local_path, progress=None):
        """Uploads resource to remote path on WebDAV server.
        In case resource is directory it will upload all nested files and directories.

        :param remote_path: the path for uploading resources on WebDAV server. Can be file and directory.
        :param local_path: the path to local resource for uploading.
        :param progress: Progress function. Not supported now.
        """
        if os.path.isdir(local_path):
            self.upload_directory(local_path=local_path, remote_path=remote_path, progress=progress)
        else:
            self.upload_file(local_path=local_path, remote_path=remote_path)

    def upload_directory(self, remote_path, local_path, progress=None):
        """Uploads directory to remote path on WebDAV server.
        In case directory is exist on remote server it will delete it and then upload directory with nested files and
        directories.

        :param remote_path: the path to directory for uploading on WebDAV server.
        :param local_path: the path to local directory for uploading.
        :param progress: Progress function. Not supported now.
        """
        urn = Urn(remote_path, directory=True)

        if not urn.is_dir():
            raise OptionNotValid(name="remote_path", value=remote_path)

        if not os.path.isdir(local_path):
            raise OptionNotValid(name="local_path", value=local_path)

        if not os.path.exists(local_path):
            raise LocalResourceNotFound(local_path)

        if self.check(urn.path()):
            self.clean(urn.path())

        self.mkdir(remote_path)

        for resource_name in listdir(local_path):
            _remote_path = "{parent}{name}".format(parent=urn.path(), name=resource_name)
            _local_path = os.path.join(local_path, resource_name)
            self.upload(local_path=_local_path, remote_path=_remote_path, progress=progress)

    @wrap_connection_error
    def upload_file(self, remote_path, local_path, progress=None):
        """Uploads file to remote path on WebDAV server.
        File should be 2Gb or less.

        :param remote_path: the path to uploading file on WebDAV server.
        :param local_path: the path to local file for uploading.
        :param progress: Progress function. Not supported now.
        """
        if not os.path.exists(local_path):
            raise LocalResourceNotFound(local_path)

        urn = Urn(remote_path)

        if urn.is_dir():
            raise OptionNotValid(name="remote_path", value=remote_path)

        if os.path.isdir(local_path):
            raise OptionNotValid(name="local_path", value=local_path)

        if not self.check(urn.parent()):
            raise RemoteParentNotFound(urn.path())

        with open(local_path, "rb") as local_file:
            file_size = os.path.getsize(local_path)
            if file_size > self.large_size:
                raise ResourceTooBig(path=local_path, size=file_size, max_size=self.large_size)

            self.execute_request(action='upload_file', path=urn.quote(), data=local_file)

    def upload_sync(self, remote_path, local_path, callback=None):
        """Uploads resource to remote path on WebDAV server synchronously.
        In case resource is directory it will upload all nested files and directories.

        :param remote_path: the path for uploading resources on WebDAV server. Can be file and directory.
        :param local_path: the path to local resource for uploading.
        :param callback: the callback which will be invoked when downloading is complete.
        """
        self.upload(local_path=local_path, remote_path=remote_path)

        if callback:
            callback()

    def upload_async(self, remote_path, local_path, callback=None):
        """Uploads resource to remote path on WebDAV server asynchronously.
        In case resource is directory it will upload all nested files and directories.

        :param remote_path: the path for uploading resources on WebDAV server. Can be file and directory.
        :param local_path: the path to local resource for uploading.
        :param callback: the callback which will be invoked when downloading is complete.
        """
        target = (lambda: self.upload_sync(local_path=local_path, remote_path=remote_path, callback=callback))
        threading.Thread(target=target).start()

    # TODO refactor code below and write tests for it.
    @wrap_connection_error
    def copy(self, remote_path_from, remote_path_to):
        """Copies resource from one place to another on WebDAV server.

        :param remote_path_from: the path to resource which will be copied,
        :param remote_path_to: the path where resource will be copied.
        """
        def header(remote_path_to):

            path = Urn(remote_path_to).path()
            destination = "{root}{path}".format(root=self.webdav.root, path=path)
            header = self.get_header('copy')
            header["Destination"] = destination

            return header

        urn_from = Urn(remote_path_from)

        if not self.check(urn_from.path()):
            raise RemoteResourceNotFound(urn_from.path())

        urn_to = Urn(remote_path_to)

        if not self.check(urn_to.parent()):
            raise RemoteParentNotFound(urn_to.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn_from.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['copy'],
            'HTTPHEADER': header(remote_path_to)
        }

        h = header(remote_path_to)
        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=h,
        )
        # TODO: check response status

    @wrap_connection_error
    def move(self, remote_path_from, remote_path_to, overwrite=False):

        def header(remote_path_to):

            path = Urn(remote_path_to).path()
            destination = "{root}{path}".format(root=self.webdav.root, path=path)
            header = self.get_header('move')
            header["Destination"] = destination
            header["Overwrite"] = "T" if overwrite else "F"
            return header

        urn_from = Urn(remote_path_from)

        if not self.check(urn_from.path()):
            raise RemoteResourceNotFound(urn_from.path())

        urn_to = Urn(remote_path_to)

        if not self.check(urn_to.parent()):
            raise RemoteParentNotFound(urn_to.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn_from.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['move'],
        }
        h = header(remote_path_to)
        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=h,
        )
        # TODO: check response status

    @wrap_connection_error
    def clean(self, remote_path):

        urn = Urn(remote_path)

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['clean'],
            'HTTPHEADER': self.get_header('clean')
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('clean'),
        )
        # TODO: check response status

    @wrap_connection_error
    def info(self, remote_path):

        def parse(response, path):

            try:
                response_str = response.content
                tree = etree.fromstring(response_str)

                find_attributes = {
                    'created': ".//{DAV:}creationdate",
                    'name': ".//{DAV:}displayname",
                    'size': ".//{DAV:}getcontentlength",
                    'modified': ".//{DAV:}getlastmodified"
                }

                resps = tree.findall("{DAV:}response")

                for resp in resps:
                    href = resp.findtext("{DAV:}href")
                    urn = unquote(href)

                    if path[-1] == Urn.separate:
                        if not path == urn:
                            continue
                    else:
                        path_with_sep = "{path}{sep}".format(path=path, sep=Urn.separate)
                        if not path == urn and not path_with_sep == urn:
                            continue

                    info = dict()
                    for (name, value) in find_attributes.items():
                        info[name] = resp.findtext(value)
                    return info

                raise RemoteResourceNotFound(path)
            except etree.XMLSyntaxError:
                raise MethodNotSupported(name="info", server=self.webdav.hostname)

        urn = Urn(remote_path)
        # response = BytesIO()

        if not self.check(urn.path()) and not self.check(Urn(remote_path, directory=True).path()):
            raise RemoteResourceNotFound(remote_path)

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['info'],
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('info')
        )
        path = "{root}{path}".format(root=self.webdav.root, path=urn.path())
        return parse(response, path)

    @wrap_connection_error
    def is_dir(self, remote_path):

        def parse(response, path):

            try:
                response_str = response.content
                tree = etree.fromstring(response_str)

                resps = tree.findall("{DAV:}response")

                for resp in resps:
                    href = resp.findtext("{DAV:}href")
                    urn = unquote(href)

                    if path[-1] == Urn.separate:
                        if not path == urn:
                            continue
                    else:
                        path_with_sep = "{path}{sep}".format(path=path, sep=Urn.separate)
                        if not path == urn and not path_with_sep == urn:
                            continue
                    type = resp.find(".//{DAV:}resourcetype")
                    if type is None:
                        raise MethodNotSupported(name="is_dir", server=self.webdav.hostname)
                    dir_type = type.find("{DAV:}collection")

                    return True if dir_type is not None else False

                raise RemoteResourceNotFound(path)

            except etree.XMLSyntaxError:
                raise MethodNotSupported(name="is_dir", server=self.webdav.hostname)

        urn = Urn(remote_path)
        parent_urn = Urn(urn.parent())
        if not self.check(urn.path()) and not self.check(Urn(remote_path, directory=True).path()):
            raise RemoteResourceNotFound(remote_path)

        response = BytesIO()

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': parent_urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['info'],
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('info')
        )

        path = "{root}{path}".format(root=self.webdav.root, path=urn.path())

        return parse(response, path)

    def resource(self, remote_path):
        urn = Urn(remote_path)
        return Resource(self, urn.path())

    @wrap_connection_error
    def get_property(self, remote_path, option):

        def parse(response, option):
            response_str = response.content
            tree = etree.fromstring(response_str)
            xpath = "{xpath_prefix}{xpath_exp}".format(xpath_prefix=".//", xpath_exp=option['name'])
            return tree.findtext(xpath)

        def data(option):
            root = etree.Element("propfind", xmlns="DAV:")
            prop = etree.SubElement(root, "prop")
            etree.SubElement(prop, option.get('name', ""), xmlns=option.get('namespace', ""))
            tree = etree.ElementTree(root)

            buff = BytesIO()

            tree.write(buff)
            return buff.getvalue()

        urn = Urn(remote_path)

        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['get_metadata'],
            'HTTPHEADER': self.get_header('get_metadata'),
            'POSTFIELDS': data(option),
            'NOBODY': 0
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('get_metadata'),
            data=data(option)
        )
        return parse(response, option)

    @wrap_connection_error
    def set_property(self, remote_path, option):

        def data(option):
            root_node = etree.Element("propertyupdate", xmlns="DAV:")
            root_node.set('xmlns:u', option.get('namespace', ""))
            set_node = etree.SubElement(root_node, "set")
            prop_node = etree.SubElement(set_node, "prop")
            opt_node = etree.SubElement(prop_node, "{namespace}:{name}".format(namespace='u', name=option['name']))
            opt_node.text = option.get('value', "")

            tree = etree.ElementTree(root_node)

            buff = BytesIO()
            tree.write(buff)

            return buff.getvalue()

        urn = Urn(remote_path)

        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['set_metadata'],
            'HTTPHEADER': self.get_header('get_metadata'),
            'POSTFIELDS': data(option)
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('get_metadata'),
            data=data(option)
        )

    def push(self, remote_directory, local_directory):

        def prune(src, exp):
            return [sub(exp, "", item) for item in src]

        urn = Urn(remote_directory, directory=True)

        if not self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_directory)

        if not os.path.isdir(local_directory):
            raise OptionNotValid(name="local_path", value=local_directory)

        if not os.path.exists(local_directory):
            raise LocalResourceNotFound(local_directory)

        paths = self.list(urn.path())
        expression = "{begin}{end}".format(begin="^", end=urn.path())
        remote_resource_names = prune(paths, expression)

        for local_resource_name in listdir(local_directory):

            local_path = os.path.join(local_directory, local_resource_name)
            remote_path = "{remote_directory}{resource_name}".format(remote_directory=urn.path(),
                                                                     resource_name=local_resource_name)

            if os.path.isdir(local_path):
                if not self.check(remote_path=remote_path):
                    self.mkdir(remote_path=remote_path)
                self.push(remote_directory=remote_path, local_directory=local_path)
            else:
                if local_resource_name in remote_resource_names:
                    continue
                self.upload_file(remote_path=remote_path, local_path=local_path)

    def pull(self, remote_directory, local_directory):

        def prune(src, exp):
            return [sub(exp, "", item) for item in src]

        urn = Urn(remote_directory, directory=True)

        if not self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_directory)

        if not os.path.exists(local_directory):
            raise LocalResourceNotFound(local_directory)

        local_resource_names = listdir(local_directory)

        paths = self.list(urn.path())
        expression = "{begin}{end}".format(begin="^", end=remote_directory)
        remote_resource_names = prune(paths, expression)

        for remote_resource_name in remote_resource_names:

            local_path = os.path.join(local_directory, remote_resource_name)
            remote_path = "{remote_directory}{resource_name}".format(remote_directory=urn.path(),
                                                                     resource_name=remote_resource_name)

            remote_urn = Urn(remote_path)

            if self.is_dir(remote_urn.path()):
                if not os.path.exists(local_path):
                    os.mkdir(local_path)
                self.pull(remote_directory=remote_path, local_directory=local_path)
            else:
                if remote_resource_name in local_resource_names:
                    continue
                self.download_file(remote_path=remote_path, local_path=local_path)

    def sync(self, remote_directory, local_directory):

        self.pull(remote_directory=remote_directory, local_directory=local_directory)
        self.push(remote_directory=remote_directory, local_directory=local_directory)


class Resource(object):
    def __init__(self, client, urn):
        self.client = client
        self.urn = urn

    def __str__(self):
        return "resource {path}".format(path=self.urn.path())

    def is_dir(self):
        return self.client.is_dir(self.urn.path())

    def rename(self, new_name):
        old_path = self.urn.path()
        parent_path = self.urn.parent()
        new_name = Urn(new_name).filename()
        new_path = "{directory}{filename}".format(directory=parent_path, filename=new_name)

        self.client.move(remote_path_from=old_path, remote_path_to=new_path)
        self.urn = Urn(new_path)

    def move(self, remote_path):
        new_urn = Urn(remote_path)
        self.client.move(remote_path_from=self.urn.path(), remote_path_to=new_urn.path())
        self.urn = new_urn

    def copy(self, remote_path):
        urn = Urn(remote_path)
        self.client.copy(remote_path_from=self.urn.path(), remote_path_to=remote_path)
        return Resource(self.client, urn)

    def info(self, params=None):
        info = self.client.info(self.urn.path())
        if not params:
            return info

        return {key: value for (key, value) in info.items() if key in params}

    def clean(self):
        return self.client.clean(self.urn.path())

    def check(self):
        return self.client.check(self.urn.path())

    def read_from(self, buff):
        self.client.upload_from(buff=buff, remote_path=self.urn.path())

    def read(self, local_path):
        return self.client.upload_sync(local_path=local_path, remote_path=self.urn.path())

    def read_async(self, local_path, callback=None):
        return self.client.upload_async(local_path=local_path, remote_path=self.urn.path(), callback=callback)

    def write_to(self, buff):
        return self.client.download_to(buff=buff, remote_path=self.urn.path())

    def write(self, local_path):
        return self.client.download_sync(local_path=local_path, remote_path=self.urn.path())

    def write_async(self, local_path, callback=None):
        return self.client.download_async(local_path=local_path, remote_path=self.urn.path(), callback=callback)

    def publish(self):
        return self.client.publish(self.urn.path())

    def unpublish(self):
        return self.client.unpublish(self.urn.path())

    @property
    def property(self, option):
        return self.client.get_property(remote_path=self.urn.path(), option=option)

    @property.setter
    def property(self, option, value):
        option['value'] = value.__str__()
        self.client.set_property(remote_path=self.urn.path(), option=option)
