Here are the steps on how to make a new release.

#. Create a ``release-VERSION`` branch from ``upstream/master``.
#. Update ``CHANGELOG.rst``.
#. Push a branch with the changes.
#. Wait for all builds to pass and at least one approval.
#. Push a tag ``VERSION`` to ``upstream``.
#. Merge the PR.
