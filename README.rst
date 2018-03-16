webdavclient3
=============

Based on https://github.com/designerror/webdav-client-python
But uses `requests` instead of `PyCURL`


Release Notes
=============

Version 0.6.1 – 16.03.2018
* Fixed issue with wrong argument for resource creation

Version 0.6 – 21.02.2018
* Fixed issue with in extracting response for path

Version 0.5 – 03.12.2017
* Added method for setting of WebDAV resource property values in batch

Version 0.4 - 27.11.2017
* Refactoring of WebDAV client and making it works in following methods:
    - Checking is remote resource directory
    - Fixed problem when connection lost during request executing and nothing was happened, now it raises an exception

Version 0.3 - 18.10.2017
* Refactoring of WebDAV client and making it works in following methods:
    - Getting of WebDAV resource property value
    - Setting of WebDAV resource property value
    - Coping of resource on WebDAV server
    - Moving of resource on WebDAV server
    - Deleting of resource on WebDAV server
    - Getting of information about WebDAV resource

Version 0.2 - 11.09.2017
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