webdavclient3  
=============

.. image:: https://travis-ci.com/ezhov-evgeny/webdav-client-python-3.svg?branch=master
    :target: https://travis-ci.com/ezhov-evgeny/webdav-client-python-3


Based on https://github.com/designerror/webdav-client-python
But uses `requests` instead of `PyCURL`

Sample Usage
____________

>>> from webdav3.client
>>> options = {
... webdav_hostname : <hostname>
... webdav_login    : <login>
... webdav_password : <password>
... }
>>> client = Client(options)
>>> client.verify = False # To not check SSL certificates (Default = True)
>>> client.session.proxies(...) # To set proxy directly into the session (Optional)
>>> client.session.auth(...) # To set proxy auth directly into the session (Optional)
>>> client.execute_request("mkdir", <directory_name>)



Release Notes
=============
**Version 0.13 – TBD**
 * Main version of Python is updated up to 3.7
 * Switch to use python sessions rather than requests by https://github.com/delrey1

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
