Here are the steps on how to make a new release.

#. Create a ``release-VERSION`` branch from ``origin/master``.
#. Update ``CHANGELOG.rst``.
#. Push a branch with the changes.
#. Wait for all builds to pass and at least one approval.
#. Start the ``deploy`` workflow:

   .. code-block:: console

        gh workflow run deploy.yml -R esss/pytest-regressions --ref release-VERSION --field version=VERSION

   The PR will be automatically merged.

After this, the package should be published directly to PyPI. After a few hours, it should be picked up by the conda-forge bot, where one of the maintainers need to merge it so the package can be published (another couple of hours after that).
