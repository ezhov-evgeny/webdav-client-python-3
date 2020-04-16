Release Notes
-------------
**Version 3.14.3**
 * Added the etag property in the get info method by https://github.com/huangganggui

**Version 3.14.2**
 * Use a content type for determining is the resource a directory or not in the `list` method
 * Fixed the issue with duplicated path segments in `download_sync` and `pull` methods by https://github.com/jotbe
 * An ability to use certificates for authenticating by https://github.com/ajordanBBN
 * Removing of tailing slashes in `web_hostname`
 * An ability to use custom `Auth` methods in the `Session` by https://github.com/matrixx567

**Version 3.14.1**
 * Fixed issue during coping and moving files with cyrillic names
 * Support OAuth2 bearer tokens by https://github.com/danielloader

**Version 3.14**
 * Override methods for customizing communication with WebDAV servers
 * Support multiple clients simultaneously
 * Sync modified files during pull and push by https://github.com/mont5piques

**Version 0.14**
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