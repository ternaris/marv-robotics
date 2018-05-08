.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _deploy:

Deployment
==========

MARV's frontend uses a service worker, which requires HTTPS for non-localhost access. You can either use a self-signed certificate or Let's Encrypt. The latter only if your webserver is accessible from the internet.

For production usage we strongly recommend to use nginx as a reverse-proxy. The increased setup overhead is justified by greatly increased performance for serving large files.

Two deployments are described here in short:

- uWSGI with a self-signed certificate, and
- nginx as a proper front-facing webserver with a Let's Encrypt certificate


uWSGI with self-signed certificate
----------------------------------

For uWSGI to support HTTPS, it needs to be compiled from source with SSL headers being available. This should have already been handled by the installation and is listed here only for completeness sake:

.. code-block:: console

   $ sudo apt-get install libssl-dev
   (venv) $ pip install -U --force-reinstall --no-binary :all: uwsgi

Given that follow the steps outlined in the uWSGI documentation:

http://uwsgi-docs.readthedocs.io/en/latest/HTTPS.html#https-support-from-1-3


Generate self-signed certificate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

  openssl genrsa -out sites/example/uwsgi-ssl.key 2048
  openssl req -new -key sites/example/uwsgi-ssl.key -out sites/example/uwsgi-ssl.csr

::

  openssl x509 -req -days 3650 \
      -in sites/example/uwsgi-ssl.csr \
      -signkey sites/example/uwsgi-ssl.key \
      -out sites/example/uwsgi-ssl.crt

Adjust uwsgi.conf
^^^^^^^^^^^^^^^^^

Enable https in ``sites/example/uwsgi.conf``.

::

   [uwsgi]
   http = :8000
   https = :8443,%d/uwsgi-ssl.crt,%d/uwsgi-ssl.key
   ...


Restart uwsgi.

::

   (venv) $ uwsgi --ini sites/example/uwsgi.conf


**docker** Restart container and instruct it to also publish the port for https.

::

  ./scripts/run-container sites/example path/to/bags -p 127.0.0.1:8443:8443


Errors
^^^^^^

::

   [uwsgi-ssl] unable to assign certificate /home/marv/site/uwsgi-ssl.crt for context "http-:8443"

This means uwsgi could not find the SSL certificate which should be right next to ``sites/example/uwsgi.conf`` (see above).


.. _deploy_nginx:

uWSGI behind NGINX
------------------

References:

- https://certbot.eff.org/all-instructions/
- http://uwsgi-docs.readthedocs.io/en/latest/Nginx.html


uwsgi config
^^^^^^^^^^^^

.. code-block:: ini

   [uwsgi]
   ;http = :8000
   ;https = :8443,%d/uwsgi-ssl.crt,%d/uwsgi-ssl.key
   socket = :8000  ; behind nginx with uwsgi_pass
   processes = 8
   threads = 2
   ;enable-threads = true  ; needed if threads < 2
   manage-script-name = true
   if-env = MARV_APPLICATION_ROOT
     mount = $(MARV_APPLICATION_ROOT)=marv.app.wsgi:application
     env = MARV_APPLICATION_ROOT=$(MARV_APPLICATION_ROOT)
   end-if
   if-not-env = MARV_APPLICATION_ROOT
     mount = /=marv.app.wsgi:application
     env = MARV_APPLICATION_ROOT=/
   end-if
   ;marv.conf next to uwsgi.conf
   env = MARV_CONFIG=%d/marv.conf


nginx config
^^^^^^^^^^^^
Nginx allows marv to offload serving data from disk which is especially useful for large files. Adjust the paths of the nested internal location block to point to your store, within the docker container and outside of the docker container, under the assumption, that nginx is running directly on your host system. In case you are running marv in a virtual environment also directly on the host system, the paths are identical. For a **self-signed certificate** create it as above, remove ``ssl_trusted_certificate`` below and adjust ``ssl_certificate`` and ``ssl_certificate_key`` below accordingly.

.. code-block:: nginx

   server {
     server_name example.com;
     listen 80;
     return 301 https://$host$request_uri;
   }

   server {
     server_name example.com;
     listen 443 ssl http2;

     include /usr/lib/python3.6/site-packages/certbot_nginx/options-ssl-nginx.conf;
     ssl_stapling_verify on;
     ssl_stapling on;

     ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;
     ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
     ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;

     location / {
       location /docker/container/path/to/store {
         internal;
	 alias /host/path/to/store;
       }
       location /scanroot {
         internal;
	 alias /host/path/to/scanroot;
       }
       client_max_body_size 10m;
       client_body_buffer_size 128k;
       uwsgi_pass 127.0.0.1:8000;
       include uwsgi_params;
     }
     location /other_instance {
       location /other_instance/docker/container/path/to/store {
         internal;
	 alias /host/path/to/store;
       }
       location /other_instance/scanroot {
         internal;
	 alias /host/path/to/other/scanroot;
       }
       client_max_body_size 10m;
       client_body_buffer_size 128k;
       uwsgi_pass 127.0.0.1:8000;
       include uwsgi_params;
     }
   }

``uwsgi_params``:

.. code-block:: nginx

   uwsgi_param  QUERY_STRING       $query_string;
   uwsgi_param  REQUEST_METHOD     $request_method;
   uwsgi_param  CONTENT_TYPE       $content_type;
   uwsgi_param  CONTENT_LENGTH     $content_length;

   uwsgi_param  REQUEST_URI        $request_uri;
   uwsgi_param  PATH_INFO          $document_uri;
   uwsgi_param  DOCUMENT_ROOT      $document_root;
   uwsgi_param  SERVER_PROTOCOL    $server_protocol;
   uwsgi_param  REQUEST_SCHEME     $scheme;
   uwsgi_param  HTTPS              $https if_not_empty;

   uwsgi_param  REMOTE_ADDR        $remote_addr;
   uwsgi_param  REMOTE_PORT        $remote_port;
   uwsgi_param  SERVER_PORT        $server_port;
   uwsgi_param  SERVER_NAME        $server_name;
