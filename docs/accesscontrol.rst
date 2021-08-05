.. Copyright 2021  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _accesscontrol:

Access Control
==============

MARV includes a full authentication, authorization and access control system. Depending on the edition there are different options.

- Local users and groups managed via CLI (CE)
- Web-based user, group and leaf management (EE)
- Single sign-on (SSO) using OAuth2 (EE)


Local accounts (CE)
-------------------

For the Community Edition, local accounts are managed via CLI (``marv user --help`` and ``marv group --help``). Accounts are securely stored inside the MARV database. A user account will be granted different permissions in MARV depending on its group memberships.

::

   # Add new user
   (server)$ marv user add john
   # Add user to admin group granting privileges like "delete"
   (server)$ marv group adduser john admin


.. _eeacl:

Web-based user, group, and leaf management (EE)
-----------------------------------------------

For the Enterprise Edition, user, group, and leave management happens through a web admin panel, available via the wrench icon on the top-left.

- Manage leaves to upload datasets directly to MARV, see also :ref:`upload`.
- Invite users to create an account in MARV (needs :ref:`cfg_marv_mail_footer`, :ref:`cfg_marv_smtp_from`, and :ref:`cfg_marv_smtp_url`).
- Add users to groups
- Give groups permissions to all datasets uploaded by a specific leaf

In addition for a specific dataset, inspect and override permissions in its detail view, with the *permission* button to the top-right.

Create an initial admin to get started, marv will prompt for the password::

  marv user add <username>
  marv group adduser <username> admin


.. _oauth2:

OAuth2 (EE)
-----------

Instead of inviting users individually, MARV integrates into a company single-sign on landscape through any service implementing OAuth2 webflow authorization. The following outlines the steps to configure the OAuth2 provider and MARV accordingly.


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
   The user part of the credentials generated for the MARV application. Use ``secret://<key>`` to read from top-level ``key`` from ``site/secrets.json``.

secret
   The secret part of the credentials generated for the MARV application. Use ``secret://<key>`` to read from top-level ``key`` from ``site/secrets.json``.

scope
   The scope MARV should request from the user. The selected scope should allow to read a user's name and email address.

firstname, *optional*
   Leave empty if user info contains ``name`` or ``given_name & family_name``, otherwise specify key containing the user's first name in user info.

secondname, *optional*
   Leave empty if user info contains ``name`` or ``given_name & family_name``, otherwise specify key containing the user's second name in user info.



The following snippets configure GitLab, GitHub, and Google as external providers and enforce the username to be taken from a specific oauth response key.

.. code-block:: ini

  [marv]
  oauth =
      GitLab | https://gitlab.example.com/oauth/authorize | https://gitlab.example.com/oauth/token | https://gitlab.example.com/oauth/userinfo | secret://gitlab_id | secret://gitlab_secret | openid email ||
  oauth_enforce_username = nickname
  # optionally require membership in any of the listed groups
  oauth_gitlab_groups = group a, group b

Optionally, for GitLab access to MARV can be limited to users that are members of at least one of several groups, specified as comma-separated list.


.. code-block:: ini

  [marv]
  oauth =
      GitHub | https://github.com/login/oauth/authorize | https://github.com/login/oauth/access_token | https://api.github.com/user | secret://github_id | secret://github_secret | read:user,user:email ||
  oauth_enforce_username = login

Beware, that GitHub separates scopes by comma, in contrast to space.


.. code-block:: ini

  [marv]
  oauth =
      Google | https://accounts.google.com/o/oauth2/v2/auth | https://accounts.google.com/o/oauth2/token | https://www.googleapis.com/oauth2/v1/userinfo | secret://google_id | secret://google_secret | openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile ||
  oauth_enforce_username = email


It is also possible to use multiple providers, but :ref:`cfg_marv_oauth_enforce_username` can only be used with a single provider.

Above examples look up secrets from ``site/secrets.json``:

.. code-block:: json

   {
     "gitlab_id": "...",
     "gitlab_secret": "..."
   }
