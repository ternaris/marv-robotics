.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _deploy:

Deployment
==========

HTTP is sufficient for serving marv on localhost. To access marv via network, it requires https. You can either use a self-signed certificate or letsencrypt, if your webserver is accessible from the internet.

Two deployments are described here in short:

- uWSGI with a self-signed certificate, and
- nginx as a proper front-facing webserver with a letsencrypt certificate


uWSGI with self-signed certificate
----------------------------------

For uwsgi to support https, it needs to be compile from source with ssl headers being available:

.. code-block:: console

   sudo apt-get install libssl-dev
   pip install -U --force-reinstall --no-binary :all: uwsgi

Given that follow the steps outline in the uwsgi documentation:

http://uwsgi-docs.readthedocs.io/en/latest/HTTPS.html#https-support-from-1-3


uWSGI behind NGINX with letsencrypt
-----------------------------------

References:

- https://certbot.eff.org/all-instructions/
- http://uwsgi-docs.readthedocs.io/en/latest/Nginx.html


uwsgi config
^^^^^^^^^^^^

.. code-block:: ini

   [uwsgi]
   ;http = :8000
   ;http-socket = :8000
   ;plugin = python
   socket = :8000
   processes = 8
   threads = 2
   ;enable-threads = true  ; needed if threads < 2
   manage-script-name = true
   mount = /=marv.app.wsgi:application
   env = MARV_APPLICATION_ROOT=/
   ;marv.conf next to uwsgi.conf
   env = MARV_CONFIG=%d/marv.conf


nginx config
^^^^^^^^^^^^

**Make sure to disable uwsgi buffering.** Otherwise the files will be buffered to hard disk by nginx instead of being served directly from marv to the client. A failure to disable buffering will result in failed download for files `bigger than 1GB <https://github.com/ternaris/marv-robotics/issues/24>`_.

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
       client_max_body_size 10m;
       client_body_buffer_size 128k;
       uwsgi_pass 127.0.0.1:8000;
       uwsgi_buffering off;
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
