"""An import checker for Pylint.

Below are descriptions of the messages and excerpts from PEP8
(http://www.python.org/dev/peps/pep-0008/#imports):

C7001: Imports should be on separate lines:

    Imports should usually be on separate lines, e.g.:

    Yes: import os
         import sys

    No:  import sys, os

    It's okay to say this though:

    from subprocess import Popen, PIPE

C7002: Imports should be at the top of the file:

    Imports are always put at the top of the file, just after any module
    comments and docstrings, and before module globals and constants.

C7003: Imports are out of order:

    Imports should be grouped in the following order:

    standard library imports
    related third party imports
    local application/library specific imports

    You should put a blank line between each group of imports.

    [This checker assumes that any module that exists in the current directory
    is part of the local application and all others are standard library or
    related third party.]

C7004: Imports are out of order:

    [Stricter version of C7003 which also checks that imports are sorted
    alphabetically within each group.]

C7005: Relative imports for intra-package imports are highly discouraged:

    Relative imports for intra-package imports are highly discouraged. Always
    use the absolute package path for all imports. Even now that PEP 328 is
    fully implemented in Python 2.5, its style of explicit relative imports is
    actively discouraged; absolute imports are more portable and usually more
    readable.
"""

import difflib
import imp
import os
import sys

from logilab import astng
from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker

MSGS = {
    'C7001': ('Imports should be on separate lines',
              'PEP8: "Imports should usually be on separate lines", '
              'No: "import sys, os", '
              'Okay: "from subprocess import Popen, PIPE".'),
    'C7002': ('Imports should be at the top of the file',
              'PEP8: "Imports are always put at the top of the file", '
              'Checks that imports do not happen inside functions.'),
    'C7003': ('Imports are out of order.\n\n'
              'Found:\n%s\n\nExpected:\n%s\n\nDiff:\n%s',
              'PEP8: "Imports should be grouped in the following order: '
              'standard library imports, related third party imports, '
              'local application/library specific imports".'),
    'C7005': ('Relative imports are highly discouraged',
              'PEP8: "Relative imports for intra-package imports are highly '
              'discouraged. Always use the absolute package path for all '
              'imports."'),
}
MSGS['C7004'] = (
    MSGS['C7003'][0],
    MSGS['C7003'][1] + ' This is a stricter version of C7003 which also '
    'checks that imports are sorted alphabetically within each group.'
)

_STDLIB_PREFIX = os.path.realpath(getattr(sys, 'real_prefix', sys.prefix)) + '/'
_APP_PREFIX = os.path.realpath(os.getcwd()) + '/'

_GROUP_STDLIB = 0
_GROUP_THIRD_PARTY = 1
_GROUP_APP_SPECIFIC = 2


def _module_group(name):
    if name in sys.builtin_module_names:
        return _GROUP_STDLIB
    try:
        path = imp.find_module(name)[1]
    except ImportError:
        return _GROUP_THIRD_PARTY
    real_path = os.path.realpath(path)
    path_pieces = set(real_path.split('/'))
    if real_path.startswith(_APP_PREFIX):
        return _GROUP_APP_SPECIFIC
    elif (real_path.startswith(_STDLIB_PREFIX) and
          'site-packages' not in path_pieces and
          'dist-packages' not in path_pieces):
        return _GROUP_STDLIB
    else:
        return _GROUP_THIRD_PARTY


class ImportChecker(BaseChecker):
    __implements__ = (IASTNGChecker,)

    name = 'ec_imports'
    msgs = MSGS
    priority = -2
    options = ()

    def __init__(self, linter=None):
        super(ImportChecker, self).__init__(linter)
        self._imports = []

    def visit_import(self, node):
        if len(node.names) > 1:
            self.add_message('C7001', node=node)
        self._handle_import(node)

    def visit_from(self, node):
        if node.level:
            self.add_message('C7005', node=node)
        self._handle_import(node)

    def _handle_import(self, node):
        if isinstance(node.parent, astng.Module):
            self._imports.append(node)
        else:
            self.add_message('C7002', node=node)

    def leave_module(self, node):
        actual = []
        expected1 = []
        expected2 = []

        # Determine sort keys for each top-level import.
        # expected1 (for C7003) contains:
        #   (group_idx, idx, import_str)
        # expected2 (for C7004) contains:
        #   (group_idx, module_name_pieces, import_str)
        for i, import_node in enumerate(self._imports):
            if isinstance(import_node, astng.Import):
                pieces = tuple(import_node.names[0][0].split('.'))
            else:
                pieces = (
                    tuple(node.name.split('.')[:-import_node.level]) +
                    tuple(filter(None, import_node.modname.split('.'))) +
                    (import_node.names[0][0],)
                )
            import_str = import_node.as_string()
            actual.append(import_str)

            group = _module_group(pieces[0])
            expected1.append((group, i, import_str))
            expected2.append((group, pieces, import_str))

        # Complain about C7003 or C7004 (but not both) if appropriate.
        for msg, expected in [('C7003', expected1), ('C7004', expected2)]:
            expected.sort()
            expected_strs = [data[-1] for data in expected]
            if actual != expected_strs:
                self.add_message(
                    msg,
                    args=(
                        '\n'.join('  %s' % line for line in actual),
                        '\n'.join('  %s' % line for line in expected_strs),
                        ''.join(
                            difflib.unified_diff(
                                ['%s\n' % line for line in actual],
                                ['%s\n' % line for line in expected_strs],
                                fromfile='actual',
                                tofile='expected',
                            )
                        ),
                    )
                )
                break

        # Reset our state for the next module.
        self._imports[:] = []


def register(linter):
    """Register this checker."""
    linter.register_checker(ImportChecker(linter))
