webdavclient3
=========
[![Build Status](https://travis-ci.com/ezhov-evgeny/webdav-client-python-3.svg?branch=develop)](https://travis-ci.com/ezhov-evgeny/webdav-client-python-3)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ezhov-evgeny_webdav-client-python-3&metric=alert_status)](https://sonarcloud.io/dashboard?id=ezhov-evgeny_webdav-client-python-3)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=ezhov-evgeny_webdav-client-python-3&metric=coverage)](https://sonarcloud.io/dashboard?id=ezhov-evgeny_webdav-client-python-3)
[![PyPI](https://img.shields.io/pypi/v/webdavclient3)](https://pypi.org/project/webdavclient3/) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/webdavclient3)  

Package webdavclient3 based on https://github.com/designerror/webdav-client-python but uses `requests` instead of `PyCURL`.
It provides easy way to work with WebDAV-servers.

Installation
------------
```bash
$ pip install webdavclient3
```

Sample Usage
------------
```python
from webdav3.client import Client
options = {
 'webdav_hostname': "https://webdav.server.ru",
 'webdav_login':    "login",
 'webdav_password': "password"
}
client = Client(options)
client.verify = False # To not check SSL certificates (Default = True)
client.session.proxies(...) # To set proxy directly into the session (Optional)
client.session.auth(...) # To set proxy auth directly into the session (Optional)
client.execute_request("mkdir", 'directory_name')
```

Webdav API
==========

Webdav API is a set of webdav methods of work with cloud storage. This set includes the following methods:
`check`, `free`, `info`, `list`, `mkdir`, `clean`, `copy`, `move`, `download`, `upload`, `publish` and `unpublish`.

**Configuring the client**

Required keys for configuring client connection with WevDAV-server are webdav\_hostname and webdav\_login, webdav\_password.

```python
from webdav3.client import Client

options = {
 'webdav_hostname': "https://webdav.server.ru",
 'webdav_login':    "login",
 'webdav_password': "password"
}
client = Client(options)
```

When a proxy server you need to specify settings to connect through it.

```python
from webdav3.client import Client
options = {
 'webdav_hostname': "https://webdav.server.ru",
 'webdav_login':    "w_login",
 'webdav_password': "w_password", 
 'proxy_hostname':  "http://127.0.0.1:8080",
 'proxy_login':     "p_login",
 'proxy_password':  "p_password"
}
client = Client(options)
```

If you want to use the certificate path to certificate and private key is defined as follows:

```python
from webdav3.client import Client
options = {
 'webdav_hostname': "https://webdav.server.ru",
 'webdav_login':    "w_login",
 'webdav_password': "w_password",
 'cert_path':       "/etc/ssl/certs/certificate.crt",
 'key_path':        "/etc/ssl/private/certificate.key"
}
client = Client(options)
```

Or you want to limit the speed or turn on verbose mode:

```python
options = {
 ...
 'recv_speed' : 3000000,
 'send_speed' : 3000000,
 'verbose'    : True
}
client = Client(options)
```

recv_speed: rate limit data download speed in Bytes per second. Defaults to unlimited speed.  
send_speed: rate limit data upload speed in Bytes per second. Defaults to unlimited speed.  
verbose:    set verbose mode on/off. By default verbose mode is off.

Also if your server does not support `check` it is possible to disable it:

```python
options = {
 ...
 'disable_check': True
}
client = Client(options)
```

By default checking of remote resources is enabled.

**Synchronous methods**

```python
# Checking existence of the resource

client.check("dir1/file1")
client.check("dir1")
```

```python
# Get information about the resource

client.info("dir1/file1")
client.info("dir1/")
```

```python
# Check free space

free_size = client.free()
```

```python
# Get a list of resources

files1 = client.list()
files2 = client.list("dir1")
```

```python
# Create directory

client.mkdir("dir1/dir2")
```

```python
# Delete resource

client.clean("dir1/dir2")
```

```python
# Copy resource

client.copy(remote_path_from="dir1/file1", remote_path_to="dir2/file1")
client.copy(remote_path_from="dir2", remote_path_to="dir3")
```

```python
# Move resource

client.move(remote_path_from="dir1/file1", remote_path_to="dir2/file1")
client.move(remote_path_from="dir2", remote_path_to="dir3")
```

```python
# Move resource

client.download_sync(remote_path="dir1/file1", local_path="~/Downloads/file1")
client.download_sync(remote_path="dir1/dir2/", local_path="~/Downloads/dir2/")
```

```python
# Unload resource

client.upload_sync(remote_path="dir1/file1", local_path="~/Documents/file1")
client.upload_sync(remote_path="dir1/dir2/", local_path="~/Documents/dir2/")
```

```python
# Publish the resource

link = client.publish("dir1/file1")
link = client.publish("dir2")
```

```python
# Unpublish resource

client.unpublish("dir1/file1")
client.unpublish("dir2")
```

```python
# Exception handling

from webdav3.client import WebDavException
try:
...
except WebDavException as exception:
...
```

```python
# Get the missing files

client.pull(remote_directory='dir1', local_directory='~/Documents/dir1')
```

```python
# Send missing files

client.push(remote_directory='dir1', local_directory='~/Documents/dir1')
```

**Asynchronous methods**

```python
# Load resource

kwargs = {
 'remote_path': "dir1/file1",
 'local_path':  "~/Downloads/file1",
 'callback':    callback
}
client.download_async(**kwargs)

kwargs = {
 'remote_path': "dir1/dir2/",
 'local_path':  "~/Downloads/dir2/",
 'callback':    callback
}
client.download_async(**kwargs)
```

```python
# Unload resource

kwargs = {
 'remote_path': "dir1/file1",
 'local_path':  "~/Downloads/file1",
 'callback':    callback
}
client.upload_async(**kwargs)

kwargs = {
 'remote_path': "dir1/dir2/",
 'local_path':  "~/Downloads/dir2/",
 'callback':    callback
}
client.upload_async(**kwargs)
```

Resource API
============

Resource API using the concept of OOP that enables cloud-level resources.

```python
# Get a resource

res1 = client.resource("dir1/file1")
```

```python
# Work with the resource

res1.rename("file2")
res1.move("dir1/file2")
res1.copy("dir2/file1")
info = res1.info()
res1.read_from(buffer)
res1.read(local_path="~/Documents/file1")
res1.read_async(local_path="~/Documents/file1", callback)
res1.write_to(buffer)
res1.write(local_path="~/Downloads/file1")
res1.write_async(local_path="~/Downloads/file1", callback)
```

Release Notes
-------------
**Version 0.14 – TBD**
 * Fixed an issue with checking resources on Yandex WebDAV server

**Version 0.13 – 27.11.2019**
 * Main version of Python is updated up to 3.7
 * Switch to use python sessions rather than requests by https://github.com/delrey1
 * Stripping suburl from paths in extract_response_for_path by https://github.com/Skeen
 * Added Docker Web DAV for CI
 * Changed HEAD to GET method for 'check' request due of not all servers support HEAD by request of https://github.com/danieleTrimarchi
 * Removed a costy is_dir-check on obvious directories to speed up a pull by https://github.com/jolly-jump
 * Added an option to disable check in case WebDAV server is not support it by request of https://github.com/dzhuang

**Version 0.12 - 21.06.2019**
 * Added depth argument in copy method in client.py by https://github.com/JesperHakansson
 * Added verify attribute to execute_request method by https://github.com/JesperHakansson

**Version 0.11 – 30.03.2019**
 * Fixed MemoryError if a large file is downloaded with a 32 bit python by https://github.com/bboehmke
 * Fixed argcomplete is required to run wdc but was not included in the requirements by https://github.com/evanhorn
 * Fixed wdc tries to import webdav instead of webdav3 by https://github.com/evanhorn

**Version 0.10 – 31.01.2019**
 * AssertEquals deprecation warnings by https://github.com/StefanZi
 * Problems with byte/UTF strings and xml library by https://github.com/StefanZi
 * Add some Eclipse specific files to gitignore by https://github.com/StefanZi
 * Remove filesize limit by https://github.com/StefanZi

**Version 0.9 – 10.05.2018**
 * Client.mkdir now accepts 201 HTTP-code by https://github.com/a1ezzz
 * Tests are updated
 * Added Travis-CI

**Version 0.8 – 07.05.2018**
 * Fixed issue in extract_response_for_path when a link in "href" attribute is an absolute link by https://github.com/a1ezzz

**Version 0.7 – 16.03.2018**
 * Fixed issue with wrong argument for resource creation by https://github.com/janLo

**Version 0.6 – 21.02.2018**
 * Fixed issue with in extracting response for path by https://github.com/mightydok

**Version 0.5 – 03.12.2017**
 * Added method for setting of WebDAV resource property values in batch

**Version 0.4 - 27.11.2017**
 * Refactoring of WebDAV client and making it works in following methods:
    - Checking is remote resource directory
    - Fixed problem when connection lost during request executing and nothing was happened, now it raises an exception

**Version 0.3 - 18.10.2017**
 * Refactoring of WebDAV client and making it works in following methods:
    - Getting of WebDAV resource property value
    - Setting of WebDAV resource property value
    - Coping of resource on WebDAV server
    - Moving of resource on WebDAV server
    - Deleting of resource on WebDAV server
    - Getting of information about WebDAV resource

**Version 0.2 - 11.09.2017**
 * Refactoring of WebDAV client and making it works in following methods:
    - Constructor with connecting to WebDAV
    - Getting a list of resources on WebDAV
    - Getting an information about free space on WebDAV
    - Checking of existence of resource on WebDAV
    - Making a directory on WebDAV
    - Downloading of files and directories from WebDAV
    - Asynchronously downloading of files and directories from WebDAV
    - Uploading of files and directories to WebDAV
    - Asynchronously uploading of files and directories to WebDAV
