# -*- coding: utf-8

import functools
import logging
import os
import shutil
from io import BytesIO
from re import sub

import requests
import lxml.etree as etree

from webdav2.connection import *
from webdav2.exceptions import *
from webdav2.urn import Urn

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

__version__ = "0.1"
log = logging.getLogger(__name__)


def listdir(directory):

    file_names = list()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isdir(file_path):
            filename = "{filename}{separate}".format(filename=filename, separate=os.path.sep)
        file_names.append(filename)
    return file_names


def get_options(type, from_options):

    _options = dict()

    for key in type.keys:
        key_with_prefix = "{prefix}{key}".format(prefix=type.prefix, key=key)
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

    root = '/'
    large_size = 2 * 1024 * 1024 * 1024

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

    def get_header(self, method):

        if method in Client.http_header:
            try:
                header = Client.http_header[method].copy()
            except AttributeError:
                header = Client.http_header[method][:]
        else:
            header = list()

        if self.webdav.token:
            webdav_token = "Authorization: OAuth {token}".format(token=self.webdav.token)
            header.append(webdav_token)
        return dict([map(lambda s: s.strip(), i.split(':')) for i in header])

    requests = {
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

        webdav_options = get_options(type=WebDAVSettings, from_options=options)
        proxy_options = get_options(type=ProxySettings, from_options=options)

        self.webdav = WebDAVSettings(webdav_options)
        self.proxy = ProxySettings(proxy_options)
        self.default_options = {}

    def valid(self):
        return True if self.webdav.valid() and self.proxy.valid() else False


    @wrap_connection_error
    def list(self, remote_path=root):

        def parse(response):

            try:
                response_str = response.content
                tree = etree.fromstring(response_str)
                hrees = [unquote(hree.text) for hree in tree.findall(".//{DAV:}href")]
                return [Urn(hree) for hree in hrees]
            except etree.XMLSyntaxError:
                return list()

        directory_urn = Urn(remote_path, directory=True)

        if directory_urn.path() != Client.root:
            if not self.check(directory_urn.path()):
                raise RemoteResourceNotFound(directory_urn.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': directory_urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['list'],
            'HTTPHEADER': self.get_header('list'),
            'NOBODY': 0
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('list')
        )

        urns = parse(response)

        path = "{root}{path}".format(root=self.webdav.root, path=directory_urn.path())
        return [urn.filename() for urn in urns if urn.path() != path and urn.path() != path[:-1]]

    @wrap_connection_error
    def free(self):

        def parse(response):

            try:
                response_str = response.content
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

        options = {
            'CUSTOMREQUEST': Client.requests['free'],
            'HTTPHEADER': self.get_header('free'),
            'POSTFIELDS': data(),
            'NOBODY': 0
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            data=data(),
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('free')
        )

        return parse(response)

    @wrap_connection_error
    def check(self, remote_path=root):
        urn = Urn(remote_path)
        response = BytesIO()

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['check'],
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('check')
        )

        if int(response.status_code) == 200:
            return True
        return False

    @wrap_connection_error
    def mkdir(self, remote_path):

        directory_urn = Urn(remote_path, directory=True)

        if not self.check(directory_urn.parent()):
            raise RemoteParentNotFound(directory_urn.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': directory_urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
            'CUSTOMREQUEST': Client.requests['mkdir'],
        }

        response = requests.request(
            options["CUSTOMREQUEST"],
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('mkdir')
        )
        # TODO: check response status

    @wrap_connection_error
    def download_to(self, buff, remote_path):
        urn = Urn(remote_path)

        if self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_path)

        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
        }

        response = requests.request(
            "GET",
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('download_to')
        )
        buff.write(response.content)

    def download(self, remote_path, local_path, progress=None):

        urn = Urn(remote_path)
        if self.is_dir(urn.path()):
            self.download_directory(local_path=local_path, remote_path=remote_path, progress=progress)
        else:
            self.download_file(local_path=local_path, remote_path=remote_path, progress=progress)

    def download_directory(self, remote_path, local_path, progress=None):

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
    def download_file(self, remote_path, local_path):

        urn = Urn(remote_path)

        if self.is_dir(urn.path()):
            raise OptionNotValid(name="remote_path", value=remote_path)

        if os.path.isdir(local_path):
            raise OptionNotValid(name="local_path", value=local_path)

        if not self.check(urn.path()):
            raise RemoteResourceNotFound(urn.path())

        with open(local_path, 'wb') as local_file:

            url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
            options = {
                'URL': "{hostname}{root}{path}".format(**url),
                'HTTPHEADER': self.get_header('download_file'),
                'WRITEDATA': local_file,
                'NOBODY': 0
            }

            response = requests.request(
                "GET",
                options["URL"],
                auth=(self.webdav.login, self.webdav.password),
                headers=self.get_header('download_file')
            )
            for block in response.iter_content(1024):
                local_file.write(block)

    def download_sync(self, remote_path, local_path, callback=None):

        self.download(local_path=local_path, remote_path=remote_path)

        if callback:
            callback()

    # def download_async(self, remote_path, local_path, callback=None):

    #     target = (lambda: self.download_sync(local_path=local_path, remote_path=remote_path, callback=callback))
    #     threading.Thread(target=target).start()

    @wrap_connection_error
    def upload_from(self, buff, remote_path):

        urn = Urn(remote_path)

        if urn.is_dir():
            raise OptionNotValid(name="remote_path", value=remote_path)

        if not self.check(urn.parent()):
            raise RemoteParentNotFound(urn.path())

        url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}
        options = {
            'URL': "{hostname}{root}{path}".format(**url),
        }
        # import ipdb; ipdb.set_trace();
        #FIXME
        if buff.tell() == 0:
            data = buff.read()
        else:
            data = buff
        response = requests.request(
            'PUT',
            options["URL"],
            auth=(self.webdav.login, self.webdav.password),
            headers=self.get_header('upload_from'),
            data=data
        )
        if response.status_code == 507:
            raise NotEnoughSpace()
        log.debug("Response: %s", response)

    def upload(self, remote_path, local_path, progress=None):

        if os.path.isdir(local_path):
            self.upload_directory(local_path=local_path, remote_path=remote_path, progress=progress)
        else:
            self.upload_file(local_path=local_path, remote_path=remote_path)

    def upload_directory(self, remote_path, local_path, progress=None):

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
    def upload_file(self, remote_path, local_path):

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
            url = {'hostname': self.webdav.hostname, 'root': self.webdav.root, 'path': urn.quote()}

            file_size = os.path.getsize(local_path)
            if file_size > self.large_size:
                raise ResourceTooBig(path=local_path, size=file_size)

            response = requests.request(
                method='PUT',
                url="{hostname}{root}{path}".format(**url),
                auth=(self.webdav.login, self.webdav.password),
                headers=self.get_header('upload_file'),
                data=local_file
            )
            if response.status_code == 507:
                raise NotEnoughSpace()

    def upload_sync(self, remote_path, local_path, callback=None):

        self.upload(local_path=local_path, remote_path=remote_path)

        if callback:
            callback()

    # def upload_async(self, remote_path, local_path, callback=None):

    #     target = (lambda: self.upload_sync(local_path=local_path, remote_path=remote_path, callback=callback))
    #     threading.Thread(target=target).start()

    @wrap_connection_error
    def copy(self, remote_path_from, remote_path_to):

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
            remote_path = "{remote_directory}{resource_name}".format(remote_directory=urn.path(), resource_name=local_resource_name)

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
            remote_path = "{remote_directory}{resource_name}".format(remote_directory=urn.path(), resource_name=remote_resource_name)

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
