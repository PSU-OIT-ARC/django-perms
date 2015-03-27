# Change Log for django-perms

## [Unreleased] - [unreleased]

### Deprecated
- Object-notation access to permissions will be removed in 2.0. All views
  should be decorated using `@permissions.require('perm_name')` instead of
  `@permissions.perm_name`.

## [1.1.0] - 2015-03-27

### Fixed
- Template filters now bypass the call to the permission function when
  appropriate (e.g., when `allow_staff=True` and the user is staff). The
  logic for this was already in place but was broken due to operator
  precedence.
- Tests now run on Python 2.6.
- Tests no longer cause warnings under Django 1.7 (due to missing
  `MIDDLEWARE_CLASSES` setting).

### Added
- `PermissionsRegistry.entry_for_view(view, permission_name)` can be used to
  whether a view requires a permission. This is intended for use in testing.
- Travis CI config was added.

## [1.0.0] - 2015-03-25

Initial version.
