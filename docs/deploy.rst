.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _deploy:

Deployment
==========

MARV's frontend uses a service worker, which requires HTTPS for non-localhost access. You can either use a self-signed certificate or Let's Encrypt. The latter only if your webserver is accessible from the internet.

For production usage we strongly recommend to use nginx as a reverse-proxy. The increased setup overhead is justified by greatly increased performance for serving large files.

Two deployments are described here in short:

- Gunicorn with a self-signed certificate, and
- nginx as a proper front-facing webserver with a Let's Encrypt certificate


Gunicorn with self-signed certificate
-------------------------------------

Gunicorn supports HTTPS out of the box with the limitation that it cannot serve
HTTP and HTTPS simultaneously. To activate HTTPS mode you only need to provide
Gunicorn with a certificate and corresponding keyfile.

Generate self-signed certificate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

   openssl genrsa -out sites/example/gunicorn-ssl.key 2048
   openssl req -new -key sites/example/gunicorn-ssl.key \
       -out sites/example/gunicorn-ssl.csr

::

   openssl x509 -req -days 3650 \
       -in sites/example/gunicorn-ssl.csr \
       -signkey sites/example/gunicorn-ssl.key \
       -out sites/example/gunicorn-ssl.crt

Adjust gunicorn_cfg.py
^^^^^^^^^^^^^^^^^^^^^^

Enable https in ``sites/example/gunicorn_cfg.py`` by adding.

::

   ...
   certfile = 'gunicorn-ssl.crt'
   keyfile = 'gunicorn-ssl.key'
   ...


Restart Gunicorn.

::

   (venv) $ gunicorn --config sites/example/gunicorn_cfg.py marv.app.wsgi:create_app


Errors
^^^^^^

::

   ValueError: certfile "gunicorn-ssl.crt" does not exist

This means Gunicorn could not find the SSL certificate which should be right
next to ``sites/example/gunicorn_cfg.py`` (see above).


.. _deploy_nginx:

Gunicorn behind NGINX
---------------------

References:

- https://certbot.eff.org/all-instructions/
- https://aiohttp.readthedocs.io/en/stable/deployment.html#nginx-gunicorn


When working behind a revese proxy MARV's default Gunicorn config will work
without change.

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

     include /usr/lib/python3.7/site-packages/certbot_nginx/tls_configs/options-ssl-nginx.conf;
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
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_pass 127.0.0.1:8000;
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
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_pass 127.0.0.1:8000;
     }
   }
