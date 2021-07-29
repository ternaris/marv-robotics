.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _deploy:

Deployment
==========

MARV's frontend uses a service worker, which requires HTTPS for non-localhost access. You can either use a self-signed certificate or Let's Encrypt. The latter only if your webserver is accessible from the internet.

For production usage we **strongly recommend** to use nginx as a reverse-proxy. The increased setup overhead is justified by greatly increased performance for serving large files.

Two deployments are described here in short:

- NGINX as a reverse proxy with a Let's Encrypt certificate (recommended)
- Gunicorn with a self-signed certificate (development only)


.. _deploy_nginx:

Gunicorn behind NGINX
---------------------

References:

- https://certbot.eff.org/all-instructions/
- https://aiohttp.readthedocs.io/en/stable/deployment.html#nginx-gunicorn


When working behind a reverse proxy MARV's default Gunicorn config will work without change.

nginx config
^^^^^^^^^^^^
Nginx allows marv to offload serving data from disk which is especially useful for large files. Adjust the paths of the nested internal location block to point to your store, within the docker container and outside of the docker container, under the assumption, that nginx is running directly on your host system. In case you are running marv in a virtual environment also directly on the host system, the paths are identical.

.. code-block:: nginx

   server {
     server_name example.com;
     listen 80;
     listen [::]:80;
     return 301 https://$host$request_uri;
   }

   server {
     server_name example.com;
     listen 443 ssl http2;
     listen [::]:443 ssl http2;

     include /usr/lib/python3.7/site-packages/certbot_nginx/tls_configs/options-ssl-nginx.conf;
     ssl_stapling_verify on;
     ssl_stapling on;

     add_header Strict-Transport-Security "max-age=63072000" always;

     ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;
     ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
     ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;

     # Docker setup running at the root
     location / {
       # Attachments are EE-only, but the rule won't hurt CE
       location /docker/container/path/to/attachments {
         internal;
         alias /host/path/to/attachments;
       }
       location /docker/container/path/to/store {
         internal;
         alias /host/path/to/store;
       }
       location /docker/container/path/to/leavesdir {
         internal;
         alias /host/path/to/leavesdir;
       }
       location /docker/container/path/to/resources {
         internal;
         alias /host/path/to/resources;
       }
       location /docker/container/path/to/scanroot {
         internal;
         alias /host/path/to/scanroot;
       }
       client_max_body_size 10m;
       client_body_buffer_size 128k;
       proxy_set_header Host $http_host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_pass http://127.0.0.1:8000;
     }

     # Native installation running in different application root

     location = /approot {
       rewrite ^(.*)$ $1/ redirect;
     }

     location /approot/ {
       # Attachments are EE-only, but the rule won't hurt CE
       location /approot/path/to/attachments {
         internal;
         alias /path/to/attachments;
       }
       location /approot/path/to/store {
         internal;
         alias /path/to/store;
       }
       location /approot/path/to/leavesdir {
         internal;
         alias /path/to/leavesdir;
       }
       location /approot/path/to/resources {
         internal;
         alias /path/to/resources;
       }
       location /approot/path/to/scanroot {
         internal;
         alias /path/to/scanroot;
       }
       client_max_body_size 10m;
       client_body_buffer_size 128k;
       proxy_set_header Host $http_host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_pass http://127.0.0.1:8001;
     }
   }

For a **certificate signed by a custom CA** (see steps below) point ``ssl_trusted_certificate`` to the CA certificate and adjust ``ssl_certificate`` and ``ssl_certificate_key`` to the generated files accordingly.


.. _deploy_gunicorn:

Gunicorn with HTTPS
-------------------

.. note::

   Use this mode of deployment for development setups only.

Gunicorn supports HTTPS out of the box with the limitation that it cannot serve HTTP and HTTPS simultaneously. To activate HTTPS mode you only need to provide Gunicorn with a certificate and corresponding keyfile. Use the ``--keyfile`` and ``--certfile`` options of MARV to enable the HTTPS mode. The following example makes MARV run on the default HTTPS port:

::

   (venv) $ marv serve --port 443 \
              --certfile /etc/letsencrypt/live/example.com/fullchain.pem \
              --keyfile /etc/letsencrypt/live/example.com/privkey.pem



Use custom CA when Let's Encrypt is unavailable
-----------------------------------------------

When MARV is deployed on an internal network Let's Encrypt may not be an option for acquiring server certificates.

You can create a custom certification authority (CA) to properly secure communication with your MARV instance.

.. note::

   A simple self-signed certificate will not suffice, as browsers will still classify the connection as insecure without a properly established root of trust.

In the first step generate a certification authority (CA). You can adjust ``days`` (validity of CA in days) and ``subj`` (subject name for certificate) parameters if you like.

::

   openssl req \
       -x509 \
       -nodes \
       -days 1095 \
       -addext keyUsage="critical,digitalSignature,keyCertSign" \
       -addext extendedKeyUsage="serverAuth,clientAuth" \
       -subj "/CN=MarvCA" \
       -keyout CA-privkey.pem \
       -out chain.pem

The ``chain.pem`` file needs to be installed on all client machines that are going to interact with MARV.

In the second step generate the server private key and certificate signing request. Again you can adjust the ``subj`` parameter if you like.

::

   openssl req \
       -new \
       -nodes \
       -subj "/CN=MarvServer" \
       -keyout privkey.pem \
       -out certreq.csr

In the last step generate the server certificate from the certificate signing request. In the example below you can again adjust the ``days`` parameter to your liking. Be sure to adjust the ``subjectAltName`` value to match your needs. The value should be a comma separated list of entries starting with ``IP:`` or ``DNS:`` and reflect the addresses users will use to access MARV. In most cases a single DNS or IP entry should suffice.

::

   openssl x509 \
       -req \
       -days 365 \
       -extfile <(printf "
           keyUsage=critical,digitalSignature,keyEncipherment
           extendedKeyUsage=serverAuth,clientAuth
           basicConstraints=critical,CA:FALSE
           subjectKeyIdentifier=hash
           authorityKeyIdentifier=keyid,issuer
           subjectAltName=IP:192.168.0.42,DNS:marv.internal
       ") \
       -in certreq.csr \
       -CA chain.pem \
       -CAkey CA-privkey.pem \
       -CAcreateserial \
       -out fullchain.pem
