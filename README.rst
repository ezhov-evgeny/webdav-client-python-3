webdavclient
============

|PyPI version| |Requirements Status| |PullReview stats|

Package webdavclient provides easy and convenient work with
WebDAV-servers (Yandex.Drive, Dropbox, Google Drive, Box, 4shared,
etc.). The package includes the following components: webdav API,
resource API and wdc.

The source code of the project can be found
`here <https://github.com/designerror/webdavclient>`__ |Github|

Installation and upgrade
========================

**Installation**

- Linux

.. code:: bash

    $ sudo apt-get install libxml2-dev libxslt-dev python-dev
    $ sudo apt-get install libcurl4-openssl-dev python-pycurl 
    $ sudo easy_install webdavclient

- macOS

.. code:: bash

    $ curl https://bootstrap.pypa.io/ez_setup.py -o - | python
    $ python setup.py install --prefix=/opt/setuptools
    $ sudo easy_install webdavclient

**Update**

.. code:: bash

    $ sudo pip install -U webdavclient

Webdav API
==========

Webdav API is a set of webdav methods of work with cloud storage. This
set includes the following methods: ``check``, ``free``, ``info``,
``list``, ``mkdir``, ``clean``, ``copy``, ``move``, ``download``,
``upload``, ``publish`` and ``unpublish``.

**Configuring the client**

Required keys for configuring client connection with WevDAV-server are
webdav\_hostname and webdav\_login, webdav,\_password.

.. code:: python

    import webdav.client as wc
    options = {
     'webdav_hostname': "https://webdav.server.ru",
     'webdav_login':    "login",
     'webdav_password': "password"
    }
    client = wc.Client(options)

When a proxy server you need to specify settings to connect through it.

.. code:: python

    import webdav.client as wc
    options = {
     'webdav_hostname': "https://webdav.server.ru",
     'webdav_login':    "w_login",
     'webdav_password': "w_password", 
     'proxy_hostname':  "http://127.0.0.1:8080",
     'proxy_login':     "p_login",
     'proxy_password':  "p_password"
    }
    client = wc.Client(options)

If you want to use the certificate path to certificate and private key
is defined as follows:

.. code:: python

    import webdav.client as wc
    options = {
     'webdav_hostname': "https://webdav.server.ru",
     'webdav_login':    "w_login",
     'webdav_password': "w_password",
     'cert_path':       "/etc/ssl/certs/certificate.crt",
     'key_path':        "/etc/ssl/private/certificate.key"
    }
    client = wc.Client(options)

Or you want to limit the speed or turn on verbose mode:

.. code:: python

    options = {
     ...
     'recv_speed' : 3000000,
     'send_speed' : 3000000,
     'verbose'    : True
    }
    client = wc.Client(options)

| recv\_speed: rate limit data download speed in Bytes per second.
  Defaults to unlimited speed.
| send\_speed: rate limit data upload speed in Bytes per second.
  Defaults to unlimited speed.
| verbose: set verbose mode on/off. By default verbose mode is off.

**Synchronous methods**

.. code:: python

    // Checking existence of the resource

    client.check("dir1/file1")
    client.check("dir1")

.. code:: python

    // Get information about the resource

    client.info("dir1/file1")
    client.info("dir1/")

.. code:: python

    // Check free space

    free_size = client.free()

.. code:: python

    // Get a list of resources

    files1 = client.list()
    files2 = client.list("dir1")

.. code:: python

    // Create directory

    client.mkdir("dir1/dir2")

.. code:: python

    // Delete resource

    client.clean("dir1/dir2")

.. code:: python

    // Copy resource

    client.copy(remote_path_from="dir1/file1", remote_path_to="dir2/file1")
    client.copy(remote_path_from="dir2", remote_path_to="dir3")

.. code:: python

    // Move resource

    client.move(remote_path_from="dir1/file1", remote_path_to="dir2/file1")
    client.move(remote_path_from="dir2", remote_path_to="dir3")

.. code:: python

    // Move resource

    client.download_sync(remote_path="dir1/file1", local_path="~/Downloads/file1")
    client.download_sync(remote_path="dir1/dir2/", local_path="~/Downloads/dir2/")

.. code:: python

    // Unload resource

    client.upload_sync(remote_path="dir1/file1", local_path="~/Documents/file1")
    client.upload_sync(remote_path="dir1/dir2/", local_path="~/Documents/dir2/")

.. code:: python

    // Publish the resource

    link = client.publish("dir1/file1")
    link = client.publish("dir2")

.. code:: python

    // Unpublish resource

    client.unpublish("dir1/file1")
    client.unpublish("dir2")

.. code:: python

    // Exception handling

    from webdav.client import WebDavException
    try:
    ...
    except WebDavException as exception:
    ...

.. code:: python

    // Get the missing files

    client.pull(remote_directory='dir1', local_directory='~/Documents/dir1')

.. code:: python

    // Send missing files

    client.push(remote_directory='dir1', local_directory='~/Documents/dir1')

**Asynchronous methods**

.. code:: python

    // Load resource

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

.. code:: python

    // Unload resource

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

Resource API
============

Resource API using the concept of OOP that enables cloud-level
resources.

.. code:: python

    // Get a resource

    res1 = client.resource("dir1/file1")

.. code:: python

    // Work with the resource

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

wdc
===

wdc \-a cross-platform utility that provides convenient work with
WebDAV-servers right from your console. In addition to full
implementations of methods from webdav API, also added methods content
sync local and remote directories.

**Authentication**

- *Basic authentication*

.. code:: bash

   $ wdc login https://wedbav.server.ru -p http://127.0.0.1:8080
   webdav_login: w_login
   webdav_password: w_password
   proxy_login: p_login
   proxy_password: p_password
   success

- Authorize the application using OAuth token\*

.. code:: bash

   $ wdc login https://wedbav.server.ru -p http://127.0.0.1:8080 --token xxxxxxxxxxxxxxxxxx
   proxy_login: p_login
   proxy_password: p_password
   success

There are also additional keys ``--root[-r]``, ``--cert-path[-c]`` and
``--key-path[-k]``.

**Utility**

.. code:: bash

    $ wdc check
    success
    $ wdc check file1
    not success
    $ wdc free
    245234120344
    $ wdc ls dir1
    file1
    ...
    fileN
    $ wdc mkdir dir2
    $ wdc copy dir1/file1 -t dir2/file1
    $ wdc move dir2/file1 -t dir2/file2
    $ wdc download dir1/file1 -t ~/Downloads/file1
    $ wdc download dir1/ -t ~/Downloads/dir1/
    $ wdc upload dir2/file2 -f ~/Documents/file1
    $ wdc upload dir2/ -f ~/Documents/
    $ wdc publish di2/file2
    https://yadi.sk/i/vWtTUcBucAc6k
    $ wdc unpublish dir2/file2
    $ wdc pull dir1/ -t ~/Documents/dir1/
    $ wdc push dir1/ -f ~/Documents/dir1/
    $ wdc info dir1/file1
    {'name': 'file1', 'modified': 'Thu, 23 Oct 2014 16:16:37 GMT',
    'size': '3460064', 'created': '2014-10-23T16:16:37Z'}

WebDAV-server
=============

The most popular cloud-based repositories that support the Protocol
WebDAV can be attributed Yandex.Drive, Dropbox, Google Drive, Box and
4shared. Access to data repositories, operating with access to the
Internet. If necessary local locations and cloud storage, you can deploy
your own WebDAV-server.

**Local WebDAV-server**

To deploy a local WebDAV server, using Docker containers quite easily
and quickly. To see an example of a local deploymentWebDAV servers can
be on the project
`webdav-server-docker <https://github.com/designerror/webdav-server-docker>`__.

**Supported methods**

+----------------+--------+--------+--------+---------+---------+--------+--------+------------+----------+
| Servers        | free   | info   | list   | mkdir   | clean   | copy   | move   | download   | upload   |
+================+========+========+========+=========+=========+========+========+============+==========+
| Yandex.Disk    | \+     | \+     | \+     | \+      | \+      | \+     | \+     | \+         | \+       |
+----------------+--------+--------+--------+---------+---------+--------+--------+------------+----------+
| Dropbox        | \-     | \+     | \+     | \+      | \+      | \+     | \+     | \+         | \+       |
+----------------+--------+--------+--------+---------+---------+--------+--------+------------+----------+
| Google Drive   | \-     | \+     | \+     | \+      | \+      | \-     | \-     | \+         | \+       |
+----------------+--------+--------+--------+---------+---------+--------+--------+------------+----------+
| Box            | \+     | \+     | \+     | \+      | \+      | \+     | \+     | \+         | \+       |
+----------------+--------+--------+--------+---------+---------+--------+--------+------------+----------+
| 4shared        | \-     | \+     | \+     | \+      | \+      | \-     | \-     | \+         | \+       |
+----------------+--------+--------+--------+---------+---------+--------+--------+------------+----------+
| Webdavserver   | \-     | \+     | \+     | \+      | \+      | \-     | \-     | \+         | \+       |
+----------------+--------+--------+--------+---------+---------+--------+--------+------------+----------+

Publish and unpublish methods supports only Yandex.Disk.

**Configuring connections**

To work with cloud storage Dropbox and Google Drive via the WebDAV
Protocol, you must use a WebDAV-server DropDAV and DAV-pocket,
respectively.

A list of settings for WebDAV servers:

.. code:: yaml

    webdav-servers:
     - yandex
         hostname:  https://webdav.yandex.ru
         login:     #login_for_yandex
         password:  #pass_for_yandex
     - dropbox 
         hostname:  https://dav.dropdav.com
         login:     #login_for dropdav
         password:  #pass_for_dropdav
     - google
         hostname:  https://dav-pocket.appspot.com
         root:      docso
         login:     #login_for_dav-pocket
         password:  #pass_for_dav-pocket
     - box
         hostname:  https://dav.box.com
         root:      dav
         login:     #login_for_box
         password:  #pass_for_box
     - 4shared
         hostname:  https://webdav.4shared.com
         login:     #login_for_4shared
         password:  #pass_for_4shared

Autocompletion
==============

For macOS, or older Unix systems you need to update bash.

.. code:: bash

    $ brew install bash
    $ chsh
    $ brew install bash-completion

Autocompletion can be enabled globally

.. code:: bash

    $ sudo activate-global-python-argcomplete

or locally

.. code:: bash

    #.bashrc
    eval "$(register-python-argcomplete wdc)"

.. |PyPI version| image:: https://badge.fury.io/py/webdavclient.svg
   :target: http://badge.fury.io/py/webdavclient
.. |Requirements Status| image:: https://requires.io/github/designerror/webdav-client-python/requirements.svg?branch=master&style=flat
   :target: https://requires.io/github/designerror/webdav-client-python/requirements/?branch=master&style=flat
.. |PullReview stats| image:: https://www.pullreview.com/github/designerror/webdavclient/badges/master.svg?
   :target: https://www.pullreview.com/github/designerror/webdavclient/reviews/master
.. |Github| image:: https://github.com/favicon.ico

