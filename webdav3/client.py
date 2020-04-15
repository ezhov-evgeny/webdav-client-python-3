# -*- coding: utf-8

import functools
import logging
import os
import shutil
import threading
from io import BytesIO
from re import sub
from urllib.parse import unquote, urlsplit, urlparse

import lxml.etree as etree
import requests
from dateutil import parser as dateutil_parser

from webdav3.connection import *
from webdav3.exceptions import *
from webdav3.urn import Urn

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
            raise NoConnection(self.webdav.hostname)
        except requests.RequestException as re:
            raise ConnectionException(re)
        else:
            return res

    return _wrapper


class Client(object):
    """The client for WebDAV servers provides an ability to control files on remote WebDAV server.
    """
    # path to root directory of WebDAV
    root = '/'

    # request timeout in seconds
    timeout = 30

    # controls whether to verify the server's TLS certificate or not
    verify = True

    # HTTP headers for different actions
    default_http_header = {
        'list': ["Accept: */*", "Depth: 1"],
        'free': ["Accept: */*", "Depth: 0", "Content-Type: text/xml"],
        'copy': ["Accept: */*"],
        'move': ["Accept: */*"],
        'mkdir': ["Accept: */*", "Connection: Keep-Alive"],
        'clean': ["Accept: */*", "Connection: Keep-Alive"],
        'check': ["Accept: */*"],
        'info': ["Accept: */*", "Depth: 1"],
        'get_property': ["Accept: */*", "Depth: 1", "Content-Type: application/x-www-form-urlencoded"],
        'set_property': ["Accept: */*", "Depth: 1", "Content-Type: application/x-www-form-urlencoded"]
    }

    # mapping of actions to WebDAV methods
    default_requests = {
        'options': 'OPTIONS',
        'download': "GET",
        'upload': "PUT",
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
        'get_property': "PROPFIND",
        'set_property': "PROPPATCH"
    }

    meta_xmlns = {
        'https://webdav.yandex.ru': "urn:yandex:disk:meta",
    }

    def __init__(self, options):
        """Constructor of WebDAV client

        :param options: the dictionary of connection options to WebDAV.
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

        """
        self.session = requests.Session()
        self.http_header = Client.default_http_header.copy()
        self.requests = Client.default_requests.copy()
        webdav_options = get_options(option_type=WebDAVSettings, from_options=options)

        self.webdav = WebDAVSettings(webdav_options)
        self.requests.update(self.webdav.override_methods)
        self.default_options = {}

    def get_headers(self, action, headers_ext=None):
        """Returns HTTP headers of specified WebDAV actions.

        :param action: the identifier of action.
        :param headers_ext: (optional) the addition headers list witch sgould be added to basic HTTP headers for
                            the specified action.
        :return: the dictionary of headers for specified action.
        """
        if action in self.http_header:
            try:
                headers = self.http_header[action].copy()
            except AttributeError:
                headers = self.http_header[action][:]
        else:
            headers = list()

        if headers_ext:
            headers.extend(headers_ext)

        if self.webdav.token:
            webdav_token = "Authorization: Bearer {token}".format(token=self.webdav.token)
            headers.append(webdav_token)
        return dict([map(lambda s: s.strip(), i.split(':', 1)) for i in headers])

    def get_url(self, path):
        """Generates url by uri path.

        :param path: uri path.
        :return: the url string.
        """
        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': path}
        return "{hostname}{root}{path}".format(**url)

    def get_full_path(self, urn):
        """Generates full path to remote resource exclude hostname.

        :param urn: the URN to resource.
        :return: full path to resource with root path.
        """
        return "{root}{path}".format(root=self.webdav.root, path=urn.path())

    def execute_request(self, action, path, data=None, headers_ext=None):
        """Generate request to WebDAV server for specified action and path and execute it.

        :param action: the action for WebDAV server which should be executed.
        :param path: the path to resource for action
        :param data: (optional) Dictionary or list of tuples ``[(key, value)]`` (will be form-encoded), bytes,
                     or file-like object to send in the body of the :class:`Request`.
        :param headers_ext: (optional) the addition headers list witch should be added to basic HTTP headers for
                            the specified action.
        :return: HTTP response of request.
        """
        if self.session.auth:
            self.session.request(method="GET", url=self.webdav.hostname, verify=self.verify)  # (Re)Authenticates against the proxy
        response = self.session.request(
            method=self.requests[action],
            url=self.get_url(path),
            auth=(self.webdav.login, self.webdav.password) if (not self.webdav.token and not self.session.auth) else None,
            headers=self.get_headers(action, headers_ext),
            timeout=self.timeout,
            cert=(self.webdav.cert_path, self.webdav.key_path) if (self.webdav.cert_path and self.webdav.key_path) else None,
            data=data,
            stream=True,
            verify=self.verify
        )
        if response.status_code == 507:
            raise NotEnoughSpace()
        if response.status_code == 404:
            raise RemoteResourceNotFound(path=path)
        if response.status_code == 405:
            raise MethodNotSupported(name=action, server=self.webdav.hostname)
        if response.status_code >= 400:
            raise ResponseErrorCode(url=self.get_url(path), code=response.status_code, message=response.content)
        return response

    def valid(self):
        """Validates of WebDAV settings.

        :return: True in case settings are valid and False otherwise.
        """
        return True if self.webdav.valid() else False

    @wrap_connection_error
    def list(self, remote_path=root):
        """Returns list of nested files and directories for remote WebDAV directory by path.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPFIND

        :param remote_path: path to remote directory.
        :return: list of nested file or directory names.
        """
        directory_urn = Urn(remote_path, directory=True)
        if directory_urn.path() != Client.root and not self.check(directory_urn.path()):
            raise RemoteResourceNotFound(directory_urn.path())

        response = self.execute_request(action='list', path=directory_urn.quote())
        urns = WebDavXmlUtils.parse_get_list_response(response.content)

        path = Urn.normalize_path(self.get_full_path(directory_urn))
        return [urn.filename() for urn in urns if Urn.compare_path(path, urn.path()) is False]

    @wrap_connection_error
    def free(self):
        """Returns an amount of free space on remote WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPFIND

        :return: an amount of free space in bytes.
        """
        data = WebDavXmlUtils.create_free_space_request_content()
        response = self.execute_request(action='free', path='', data=data)
        return WebDavXmlUtils.parse_free_space_response(response.content, self.webdav.hostname)

    @wrap_connection_error
    def check(self, remote_path=root):
        """Checks an existence of remote resource on WebDAV server by remote path.
        More information you can find by link http://webdav.org/specs/rfc4918.html#rfc.section.9.4

        :param remote_path: (optional) path to resource on WebDAV server. Defaults is root directory of WebDAV.
        :return: True if resource is exist or False otherwise
        """
        if self.webdav.disable_check:
            return True

        urn = Urn(remote_path)
        try:
            response = self.execute_request(action='check', path=urn.quote())
        except RemoteResourceNotFound:
            return False
        except ResponseErrorCode:
            return False

        if int(response.status_code) == 200:
            return True
        return False

    @wrap_connection_error
    def mkdir(self, remote_path):
        """Makes new directory on WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_MKCOL

        :param remote_path: path to directory
        :return: True if request executed with code 200 or 201 and False otherwise.

        """
        directory_urn = Urn(remote_path, directory=True)
        if not self.check(directory_urn.parent()):
            raise RemoteParentNotFound(directory_urn.path())

        try:
            response = self.execute_request(action='mkdir', path=directory_urn.quote())
        except MethodNotSupported:
            # Yandex WebDAV returns 405 status code when directory already exists
            return True
        return response.status_code in (200, 201)

    @wrap_connection_error
    def download_from(self, buff, remote_path):
        """Downloads file from WebDAV and writes it in buffer.

        :param buff: buffer object for writing of downloaded file content.
        :param remote_path: path to file on WebDAV server.
        """
        urn = Urn(remote_path)
        if self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_path)

        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        response = self.execute_request(action='download', path=urn.quote())
        shutil.copyfileobj(response.raw, buff)

    def download(self, remote_path, local_path, progress=None):
        """Downloads remote resource from WebDAV and save it in local path.
        More information you can find by link http://webdav.org/specs/rfc4918.html#rfc.section.9.4

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
            if urn.path().endswith(resource_name):
                continue
            _remote_path = "{parent}{name}".format(parent=urn.path(), name=resource_name)
            _local_path = os.path.join(local_path, resource_name)
            self.download(local_path=_local_path, remote_path=_remote_path, progress=progress)

    @wrap_connection_error
    def download_file(self, remote_path, local_path, progress=None):
        """Downloads file from WebDAV server and save it locally.
        More information you can find by link http://webdav.org/specs/rfc4918.html#rfc.section.9.4

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
            response = self.execute_request('download', urn.quote())
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
    def upload_to(self, buff, remote_path):
        """Uploads file from buffer to remote path on WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PUT

        :param buff: the buffer with content for file.
        :param remote_path: the path to save file remotely on WebDAV server.
        """
        urn = Urn(remote_path)
        if urn.is_dir():
            raise OptionNotValid(name="remote_path", value=remote_path)

        if not self.check(urn.parent()):
            raise RemoteParentNotFound(urn.path())

        self.execute_request(action='upload', path=urn.quote(), data=buff)

    def upload(self, remote_path, local_path, progress=None):
        """Uploads resource to remote path on WebDAV server.
        In case resource is directory it will upload all nested files and directories.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PUT

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
            _remote_path = "{parent}{name}".format(parent=urn.path(), name=resource_name).replace('\\', '')
            _local_path = os.path.join(local_path, resource_name)
            self.upload(local_path=_local_path, remote_path=_remote_path, progress=progress)

    @wrap_connection_error
    def upload_file(self, remote_path, local_path, progress=None):
        """Uploads file to remote path on WebDAV server. File should be 2Gb or less.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PUT

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
            self.execute_request(action='upload', path=urn.quote(), data=local_file)

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

    @wrap_connection_error
    def copy(self, remote_path_from, remote_path_to, depth=1):
        """Copies resource from one place to another on WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_COPY

        :param remote_path_from: the path to resource which will be copied,
        :param remote_path_to: the path where resource will be copied.
        :param depth: folder depth to copy
        """
        urn_from = Urn(remote_path_from)
        if not self.check(urn_from.path()):
            raise RemoteResourceNotFound(urn_from.path())

        urn_to = Urn(remote_path_to)
        if not self.check(urn_to.parent()):
            raise RemoteParentNotFound(urn_to.path())

        headers = [
            "Destination: {url}".format(url=self.get_url(urn_to.quote()))
        ]
        if self.is_dir(urn_from.path()):
            headers.append("Depth: {depth}".format(depth=depth))
        self.execute_request(action='copy', path=urn_from.quote(), headers_ext=headers)

    @wrap_connection_error
    def move(self, remote_path_from, remote_path_to, overwrite=False):
        """Moves resource from one place to another on WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_MOVE

        :param remote_path_from: the path to resource which will be moved,
        :param remote_path_to: the path where resource will be moved.
        :param overwrite: (optional) the flag, overwrite file if it exists. Defaults is False
        """
        urn_from = Urn(remote_path_from)
        if not self.check(urn_from.path()):
            raise RemoteResourceNotFound(urn_from.path())

        urn_to = Urn(remote_path_to)
        if not self.check(urn_to.parent()):
            raise RemoteParentNotFound(urn_to.path())

        header_destination = "Destination: {path}".format(path=self.get_url(urn_to.quote()))
        header_overwrite = "Overwrite: {flag}".format(flag="T" if overwrite else "F")
        self.execute_request(action='move', path=urn_from.quote(), headers_ext=[header_destination, header_overwrite])

    @wrap_connection_error
    def clean(self, remote_path):
        """Cleans (Deletes) a remote resource on WebDAV server. The name of method is not changed for back compatibility
        with original library.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_DELETE

        :param remote_path: the remote resource whisch will be deleted.
        """
        urn = Urn(remote_path)
        self.execute_request(action='clean', path=urn.quote())

    @wrap_connection_error
    def info(self, remote_path):
        """Gets information about resource on WebDAV.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPFIND

        :param remote_path: the path to remote resource.
        :return: a dictionary of information attributes and them values with following keys:
                 `created`: date of resource creation,
                 `name`: name of resource,
                 `size`: size of resource,
                 `modified`: date of resource modification,
                 `etag`: etag of resource.
        """
        urn = Urn(remote_path)
        self._check_remote_resource(remote_path, urn)

        response = self.execute_request(action='info', path=urn.quote())
        path = self.get_full_path(urn)
        return WebDavXmlUtils.parse_info_response(content=response.content, path=path, hostname=self.webdav.hostname)

    def _check_remote_resource(self, remote_path, urn):
        if not self.check(urn.path()) and not self.check(Urn(remote_path, directory=True).path()):
            raise RemoteResourceNotFound(remote_path)

    @wrap_connection_error
    def is_dir(self, remote_path):
        """Checks is the remote resource directory.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPFIND

        :param remote_path: the path to remote resource.
        :return: True in case the remote resource is directory and False otherwise.
        """
        urn = Urn(remote_path)
        parent_urn = Urn(urn.parent())
        self._check_remote_resource(remote_path, urn)

        response = self.execute_request(action='info', path=parent_urn.quote())
        path = self.get_full_path(urn)
        return WebDavXmlUtils.parse_is_dir_response(content=response.content, path=path, hostname=self.webdav.hostname)

    @wrap_connection_error
    def get_property(self, remote_path, option):
        """Gets metadata property of remote resource on WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPFIND

        :param remote_path: the path to remote resource.
        :param option: the property attribute as dictionary with following keys:
                       `namespace`: (optional) the namespace for XML property which will be set,
                       `name`: the name of property which will be set.
        :return: the value of property or None if property is not found.
        """
        urn = Urn(remote_path)
        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        data = WebDavXmlUtils.create_get_property_request_content(option)
        response = self.execute_request(action='get_property', path=urn.quote(), data=data)
        return WebDavXmlUtils.parse_get_property_response(response.content, option['name'])

    @wrap_connection_error
    def set_property(self, remote_path, option):
        """Sets metadata property of remote resource on WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPPATCH

        :param remote_path: the path to remote resource.
        :param option: the property attribute as dictionary with following keys:
                       `namespace`: (optional) the namespace for XML property which will be set,
                       `name`: the name of property which will be set,
                       `value`: (optional) the value of property which will be set. Defaults is empty string.
        """
        self.set_property_batch(remote_path=remote_path, option=[option])

    @wrap_connection_error
    def set_property_batch(self, remote_path, option):
        """Sets batch metadata properties of remote resource on WebDAV server in batch.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPPATCH

        :param remote_path: the path to remote resource.
        :param option: the property attributes as list of dictionaries with following keys:
                       `namespace`: (optional) the namespace for XML property which will be set,
                       `name`: the name of property which will be set,
                       `value`: (optional) the value of property which will be set. Defaults is empty string.
        """
        urn = Urn(remote_path)
        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        data = WebDavXmlUtils.create_set_property_batch_request_content(option)
        self.execute_request(action='set_property', path=urn.quote(), data=data)

    def resource(self, remote_path):
        urn = Urn(remote_path)
        return Resource(self, urn)

    def push(self, remote_directory, local_directory):

        def prune(src, exp):
            return [sub(exp, "", item) for item in src]

        updated = False
        urn = Urn(remote_directory, directory=True)
        self._validate_remote_directory(urn)
        self._validate_local_directory(local_directory)

        paths = self.list(urn.path())
        expression = "{begin}{end}".format(begin="^", end=urn.path())
        remote_resource_names = prune(paths, expression)

        for local_resource_name in listdir(local_directory):
            local_path = os.path.join(local_directory, local_resource_name)
            remote_path = "{remote_directory}{resource_name}".format(remote_directory=urn.path(), resource_name=local_resource_name)

            if os.path.isdir(local_path):
                if not self.check(remote_path=remote_path):
                    self.mkdir(remote_path=remote_path)
                result = self.push(remote_directory=remote_path, local_directory=local_path)
                updated = updated or result
            else:
                if local_resource_name in remote_resource_names and not self.is_local_more_recent(local_path, remote_path):
                    continue
                self.upload_file(remote_path=remote_path, local_path=local_path)
                updated = True
            return updated

    def pull(self, remote_directory, local_directory):
        def prune(src, exp):
            return [sub(exp, "", item) for item in src]

        updated = False
        urn = Urn(remote_directory, directory=True)
        self._validate_remote_directory(urn)
        self._validate_local_directory(local_directory)

        local_resource_names = listdir(local_directory)

        paths = self.list(urn.path())
        expression = "{begin}{end}".format(begin="^", end=remote_directory)
        remote_resource_names = prune(paths, expression)

        for remote_resource_name in remote_resource_names:
            if urn.path().endswith(remote_resource_name):
                continue
            local_path = os.path.join(local_directory, remote_resource_name)
            remote_path = "{remote_directory}{resource_name}".format(remote_directory=urn.path(), resource_name=remote_resource_name)
            remote_urn = Urn(remote_path)

            if remote_urn.path().endswith("/"):
                if not os.path.exists(local_path):
                    updated = True
                    os.mkdir(local_path)
                result = self.pull(remote_directory=remote_path, local_directory=local_path)
                updated = updated or result
            else:
                if remote_resource_name in local_resource_names and self.is_local_more_recent(local_path, remote_path):
                    continue

                self.download_file(remote_path=remote_path, local_path=local_path)
                updated = True
        return updated

    def is_local_more_recent(self, local_path, remote_path):
        """Tells if local resource is more recent that the remote on if possible

        :param local_path: the path to local resource.
        :param remote_path: the path to remote resource.

        :return: True if local resource is more recent, False if the remote one is
                 None if comparison is not possible
        """
        try:
            remote_info = self.info(remote_path)
            remote_last_mod_date = remote_info['modified']
            remote_last_mod_date = dateutil_parser.parse(remote_last_mod_date)
            remote_last_mod_date_unix_ts = int(remote_last_mod_date.timestamp())
            local_last_mod_date_unix_ts = int(os.stat(local_path).st_mtime)

            return remote_last_mod_date_unix_ts < local_last_mod_date_unix_ts
        except (ValueError, RuntimeWarning, KeyError):
            # If there is problem when parsing dates, or cannot get
            # last modified information, return None
            return None

    def sync(self, remote_directory, local_directory):
        self.pull(remote_directory=remote_directory, local_directory=local_directory)
        self.push(remote_directory=remote_directory, local_directory=local_directory)

    def _validate_remote_directory(self, urn):
        if not self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=urn.path())

    @staticmethod
    def _validate_local_directory(local_directory):
        if not os.path.isdir(local_directory):
            raise OptionNotValid(name="local_path", value=local_directory)

        if not os.path.exists(local_directory):
            raise LocalResourceNotFound(local_directory)


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
        self.client.upload_to(buff=buff, remote_path=self.urn.path())

    def read(self, local_path):
        return self.client.upload_sync(local_path=local_path, remote_path=self.urn.path())

    def read_async(self, local_path, callback=None):
        return self.client.upload_async(local_path=local_path, remote_path=self.urn.path(), callback=callback)

    def write_to(self, buff):
        return self.client.download_from(buff=buff, remote_path=self.urn.path())

    def write(self, local_path):
        return self.client.download_sync(local_path=local_path, remote_path=self.urn.path())

    def write_async(self, local_path, callback=None):
        return self.client.download_async(local_path=local_path, remote_path=self.urn.path(), callback=callback)

    def publish(self):
        return self.client.publish(self.urn.path())

    def unpublish(self):
        return self.client.unpublish(self.urn.path())

    def get_property(self, option):
        return self.client.get_property(remote_path=self.urn.path(), option=option)

    def set_property(self, option, value):
        option['value'] = value.__str__()
        self.client.set_property(remote_path=self.urn.path(), option=option)


class WebDavXmlUtils:
    def __init__(self):
        pass

    @staticmethod
    def parse_get_list_response(content):
        """Parses of response content XML from WebDAV server and extract file and directory names.

        :param content: the XML content of HTTP response from WebDAV server for getting list of files by remote path.
        :return: list of extracted file or directory names.
        """
        try:
            tree = etree.fromstring(content)
            urns = []
            for response in tree.findall(".//{DAV:}response"):
                href_el = next(iter(response.findall(".//{DAV:}href")), None)
                if href_el is None:
                    continue
                href = Urn.separate + unquote(urlsplit(href_el.text).path)
                is_dir = len(response.findall(".//{DAV:}collection")) > 0
                urns.append(Urn(href, is_dir))
            return urns
        except etree.XMLSyntaxError:
            return list()

    @staticmethod
    def create_free_space_request_content():
        """Creates an XML for requesting of free space on remote WebDAV server.

        :return: the XML string of request content.
        """
        root = etree.Element("propfind", xmlns="DAV:")
        prop = etree.SubElement(root, "prop")
        etree.SubElement(prop, "quota-available-bytes")
        etree.SubElement(prop, "quota-used-bytes")
        tree = etree.ElementTree(root)
        return WebDavXmlUtils.etree_to_string(tree)

    @staticmethod
    def parse_free_space_response(content, hostname):
        """Parses of response content XML from WebDAV server and extract an amount of free space.

        :param content: the XML content of HTTP response from WebDAV server for getting free space.
        :param hostname: the server hostname.
        :return: an amount of free space in bytes.
        """
        try:
            tree = etree.fromstring(content)
            node = tree.find('.//{DAV:}quota-available-bytes')
            if node is not None:
                return int(node.text)
            else:
                raise MethodNotSupported(name='free', server=hostname)
        except TypeError:
            raise MethodNotSupported(name='free', server=hostname)
        except etree.XMLSyntaxError:
            return str()

    @staticmethod
    def parse_info_response(content, path, hostname):
        """Parses of response content XML from WebDAV server and extract an information about resource.

        :param content: the XML content of HTTP response from WebDAV server.
        :param path: the path to resource.
        :param hostname: the server hostname.
        :return: a dictionary of information attributes and them values with following keys:
                 `created`: date of resource creation,
                 `name`: name of resource,
                 `size`: size of resource,
                 `modified`: date of resource modification,
                 `etag`: etag of resource.
        """
        response = WebDavXmlUtils.extract_response_for_path(content=content, path=path, hostname=hostname)
        find_attributes = {
            'created': ".//{DAV:}creationdate",
            'name': ".//{DAV:}displayname",
            'size': ".//{DAV:}getcontentlength",
            'modified': ".//{DAV:}getlastmodified",
            'etag': ".//{DAV:}getetag",
        }
        info = dict()
        for (name, value) in find_attributes.items():
            info[name] = response.findtext(value)
        return info

    @staticmethod
    def parse_is_dir_response(content, path, hostname):
        """Parses of response content XML from WebDAV server and extract an information about resource.

        :param content: the XML content of HTTP response from WebDAV server.
        :param path: the path to resource.
        :param hostname: the server hostname.
        :return: True in case the remote resource is directory and False otherwise.
        """
        response = WebDavXmlUtils.extract_response_for_path(content=content, path=path, hostname=hostname)
        resource_type = response.find(".//{DAV:}resourcetype")
        if resource_type is None:
            raise MethodNotSupported(name="is_dir", server=hostname)
        dir_type = resource_type.find("{DAV:}collection")

        return True if dir_type is not None else False

    @staticmethod
    def create_get_property_request_content(option):
        """Creates an XML for requesting of getting a property value of remote WebDAV resource.

        :param option: the property attributes as dictionary with following keys:
                       `namespace`: (optional) the namespace for XML property which will be get,
                       `name`: the name of property which will be get.
        :return: the XML string of request content.
        """
        root = etree.Element("propfind", xmlns="DAV:")
        prop = etree.SubElement(root, "prop")
        etree.SubElement(prop, option.get('name', ""), xmlns=option.get('namespace', ""))
        tree = etree.ElementTree(root)
        return WebDavXmlUtils.etree_to_string(tree)

    @staticmethod
    def parse_get_property_response(content, name):
        """Parses of response content XML from WebDAV server for getting metadata property value for some resource.

        :param content: the XML content of response as string.
        :param name: the name of property for finding a value in response
        :return: the value of property if it has been found or None otherwise.
        """
        tree = etree.fromstring(content)
        return tree.xpath('//*[local-name() = $name]', name=name)[0].text

    @staticmethod
    def create_set_property_batch_request_content(options):
        """Creates an XML for requesting of setting a property values for remote WebDAV resource in batch.

        :param options: the property attributes as list of dictionaries with following keys:
                       `namespace`: (optional) the namespace for XML property which will be set,
                       `name`: the name of property which will be set,
                       `value`: (optional) the value of property which will be set. Defaults is empty string.
        :return: the XML string of request content.
        """
        root_node = etree.Element('propertyupdate', xmlns='DAV:')
        set_node = etree.SubElement(root_node, 'set')
        prop_node = etree.SubElement(set_node, 'prop')
        for option in options:
            opt_node = etree.SubElement(prop_node, option['name'], xmlns=option.get('namespace', ''))
            opt_node.text = option.get('value', '')
        tree = etree.ElementTree(root_node)
        return WebDavXmlUtils.etree_to_string(tree)

    @staticmethod
    def etree_to_string(tree):
        """Creates string from lxml.etree.ElementTree with XML declaration and UTF-8 encoding.

        :param tree: the instance of ElementTree
        :return: the string of XML.
        """
        buff = BytesIO()
        tree.write(buff, xml_declaration=True, encoding='UTF-8')
        return buff.getvalue()

    @staticmethod
    def extract_response_for_path(content, path, hostname):
        """Extracts single response for specified remote resource.

        :param content: raw content of response as string.
        :param path: the path to needed remote resource.
        :param hostname: the server hostname.
        :return: XML object of response for the remote resource defined by path.
        """
        prefix = urlparse(hostname).path
        try:
            tree = etree.fromstring(content)
            responses = tree.findall("{DAV:}response")
            n_path = Urn.normalize_path(path)

            for resp in responses:
                href = resp.findtext("{DAV:}href")

                if Urn.compare_path(n_path, href) is True:
                    return resp
                href_without_prefix = href[len(prefix):] if href.startswith(prefix) else href
                if Urn.compare_path(n_path, href_without_prefix) is True:
                    return resp
            raise RemoteResourceNotFound(path)
        except etree.XMLSyntaxError:
            raise MethodNotSupported(name="is_dir", server=hostname)
