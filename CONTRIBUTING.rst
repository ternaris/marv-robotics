==================
Contribution guide
==================

Thank you for considering to contribute to MARV. Below is information on how to report issues and submit your contributions to MARV.


Rights to and license of contributions
======================================

The MARV Community Edition is licensed under `AGPL-3.0`_ and `Ternaris`_ offers an Enterprise Edition with an extended feature set under the proprietary `MARV-License`_.

For one, we want to ensure that you have the rights to your contributions, for another we'd like to be able to use your contributions to either edition in both editions.

To this end, beyond what is required by the license of the MARV edition you are contributing to, your submission of an issue, merge request, comment, or code to us is:

1. If your employer has rights in your contributions, your representation that your employer has authorized you to enter into this agreement on its behalf;

2. Your agreement, or your employer's agreement, with the terms and conditions in this document;

3. Your signature of the `Developer Certificate of Origin`_ (details below); and

4. Your grant of a license to your contributions under:

   - `Apache-2.0`_ license for code,
   - `CC BY 4.0`_ license for documentation


Reporting issues / minimal working example
==========================================

In order to provide a minimal working example to reproduce issues you
are seeing, please:

1. Create a fork of this repository and clone it.

2. Create a site folder in `<./sites>`_ containing your configuration.

3. If there is custom code involved, please add a minimal working example based on it to a python package in `<./code>`_. We don't need to see your real code, but we cannot help without code. This will require a *sign-off*, which is explained below.

4. Create a ``scanroot`` folder within your site folder and add minimal bags or other files as needed.

5. Make sure the issues you are seeing are exposed by this setup.

6. Push your changes to your fork.

7. `Submit an issue`_ and add a link to the minimal working example.

.. _Submit an issue: https://gitlab.com/ternaris/marv-robotics/issues/new


Contributing code / merge requests
==================================

In order to contribute code there are a few noteworthy things:

1. Especially for non-trivial contributions, please **submit an issue first** to discuss your ideas.

2. If your merge requests relates to an existing issue, please reference it from your merge request.

3. When creating a merge request, please `allow collaboration`_. This enables us to make small adjustments and rebase the branch as needed. Please use dedicated branches for your merge request and don't give us access to a branch that is dear to you.

4. Stick to *The seven rules of a great Git commit message* (see below).

5. As part of your merge request, please **update the changelog** accordingly in one dedicated final commit.

6. We require you to **sign-off your commits** (see below). Your sign-off indicates that you agreed to the terms and conditions laid out in this document, if applicable on behalf of your employer.

.. _allow collaboration:
   https://docs.gitlab.com/ee/user/project/merge_requests/allow_collaboration.html


The seven rules of a great Git commit message
---------------------------------------------

We like `The seven rules of a great Git commit message`_, summarized here for completeness, follow links for further reading.

1. `Separate subject from body with a blank line <https://chris.beams.io/posts/git-commit/#separate>`_

2. `Limit the subject line to 50 characters <https://chris.beams.io/posts/git-commit/#limit-50>`_ (soft-limit 50, hard-limit 72)

3. `Start subject line with uppercase letter <https://chris.beams.io/posts/git-commit/#capitalize>`_

4. `Do not end the subject line with a period <https://chris.beams.io/posts/git-commit/#end>`_

5. `Use the imperative mood in the subject line <https://chris.beams.io/posts/git-commit/#imperative>`_

6. `Wrap the body at 72 characters <https://chris.beams.io/posts/git-commit/#wrap-72>`_

7. `Use the body to explain what and why vs. how <https://chris.beams.io/posts/git-commit/#why-not-how>`_

.. _The seven rules of a great Git commit message: https://chris.beams.io/posts/git-commit/#seven-rules


Update changelog
----------------

You know best what your changes are about, so please help us by updating the `changelog`_ right away. Please do this in one commit that only updates the changelog and builds the final commit, the HEAD of your branch.

The format of our changelog is based on `Keep a changelog`_. When writing changelog entries:

- imagine a novice person, another developer, and yourself as target audience;

- avoid using technical terms and only talking in general terms;

- write in terms of features, i.e. what, not how;

- reference relevant issues and merge requests.

Inspiration taken from `How to write a changelog and why it matters`_.

.. _changelog: ./CHANGES.rst
.. _Keep a changelog: https://keepachangelog.com/en/1.0.0/
.. _How to write a changelog and why it matters: https://www.itsupportguides.com/blog/how-to-write-changelog-and-why-it-matters/


Signing off a commit
--------------------

You sign off a commit by adding a line like the following to the bottom of its commit message, separated by an empty line.

::

   Signed-off-by: Fullname <email@example.net>

Make sure it reflects your real name and email address. Git does this automatically when using ``git commit -s``.

Except for the licenses granted herein, you reserve all right, title, and interest in and to your contributions.


Developer Certificate of Origin
===============================

Embedded and reformatted from `Developer Certificate of Origin`_:

Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors, 1 Letterman Drive, Suite D4700, San Francisco, CA, 94129

Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

1. The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or

2. The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications, whether created in whole or in part by me, under the same open source license (unless I am permitted to submit under a different license), as indicated in the file; or

3. The contribution was provided directly to me by some other person who certified (1), (2) or (3) and I have not modified it.

4. I understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information I submit with it, including my sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open source license(s) involved.


.. _AGPL-3.0: https://www.gnu.org/licenses/agpl-3.0.html
.. _Apache-2.0: ./LICENSES/Apache-2.0
.. _CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
.. _Developer Certificate of Origin: https://developercertificate.org/
.. _MARV-License: ./LICENSES/MARV-License
.. _Ternaris: https://ternaris.com
