Extra checkers for Pylint

*This code is unmaintained and does not work with recent versions of pylint.*

### Setup

Once installed, these can be added to pylintrc on the load-plugins line:

    load-plugins=ec_pylint_checkers.import_checker

### Available checkers

#### `ec_pylint_checkers.import_checker`

An import checker for Pylint.

Below are descriptions of the messages:

- C7001: Imports should be on separate lines
- C7002: Imports should be at the top of the file
- C7003: Imports are out of order
- C7004: Stricter version of C7003 which also checks that imports are sorted
    alphabetically within each group
- C7005: Relative imports for intra-package imports are highly discouraged
- C7006: Variant of C7004 which expects each group's from imports to be after
    the bare non-from imports
