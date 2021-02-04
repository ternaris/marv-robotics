.. Copyright 2021  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _authentication:

Access Control
==============

MARV includes a full authentication, authorization and access control system. Users and groups can either be created locally inside of MARV or be provided by an external sign-on provider (EE).

Local accounts are managed via CLI (``marv user`` and ``marv group``) or the web admin interface (EE). Accounts are securely stored inside the MARV database. A user account will be granted different permissions in MARV depending on its group memberships.

::

   # Add new user
   (server)$ marv user add john
   # Add user to admin group granting privileges like "delete"
   (server)$ marv group adduser john admin

In addition to authentication against its local database MARV EE supports single sign-on (SSO) via external services. When a new user signs in for the first time via an external provider, MARV asks for a new username and links the remote account to a new local user entry.


OAuth2 (EE)
-----------

This plugin allows logging in with accounts from any service implementing OAuth2 webflow authorization.


Configuring external provider
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An external provider needs to be configured to allow a MARV instance to access webflow authorization. This usually requires to configure an "Application" at the external provider. Check your provider for instructions, here are some examples:

- Google: https://developers.google.com/identity/protocols/oauth2

- GitHub: https://developer.github.com/apps/building-oauth-apps/creating-an-oauth-app/

- GitLab: https://docs.gitlab.com/ee/integration/oauth_provider.html

Webflow authorization will require two URLs to be filled in. One is the *application url* where signin requests will be coming from and the other is the *callback url* which is the address a successful request will be redirected back to. For MARV both URLs should simply be the base URL of your MARV instance.

The MARV application should be granted as few permissions as possible (see ``scope`` parameter below).

.. note::

   Double-check your nginx config (:ref:`deploy_nginx`), it's essential that MARV knows how it's served in order to generate the correct redirect URI. In case an oauth service complains about an invalid redirect URI, check the URL displayed in the browser for debugging, it contains the redirect URI as query parameter.


Configuring MARV
^^^^^^^^^^^^^^^^

The ``marv.conf`` file supports the ``oauth`` key inside the ``[marv]`` section:

.. code-block:: ini

  [marv]
  oauth =
      name | auth | token | info | id | secret | scope | firstname | secondname

The value consists of one line per external provider. Each line consists of multiple fields separated by ``|``:

name
   The name of this provider, this can be freely chosen.

auth
   The authorization URL for webflow as given by the provider.

token
   The token URL for webflow as given by the provider.

info
   The URL for accessing a user's information as given by the provider.

id
   The user part of the credentials generated for the MARV application.

secret
   The secret part of the credentials generated for the MARV application.

scope
   The scope MARV should request from the user. The selected scope should allow to read a user's name and email address.

firstname, *optional*
   Leave empty if user info contains ``name`` or ``given_name & family_name``, otherwise specify key containing the user's first name in user info.

secondname, *optional*
   Leave empty if user info contains ``name`` or ``given_name & family_name``, otherwise specify key containing the user's second name in user info.



The following snippet configures Google, GitHub, and GitLab as external providers:

.. code-block:: ini

  [marv]
  oauth =
      Google | https://accounts.google.com/o/oauth2/v2/auth | https://accounts.google.com/o/oauth2/token | https://www.googleapis.com/oauth2/v1/userinfo | google_id | google_secret | openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile ||
      GitHub | https://github.com/login/oauth/authorize | https://github.com/login/oauth/access_token | https://api.github.com/user | github_id | github_secret | read:user,user:email ||
      GitLab | https://gitlab.example.com/oauth/authorize | https://gitlab.example.com/oauth/token | https://gitlab.example.com/oauth/userinfo | gitlab_id | gitlab_secret | openid email ||


Beware, that GitHub separates scopes by comma, in contrast to space.
