#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package helper

Usage:
    helper.py serve
    helper.py docstrings [-d <dir> | --directory=<dir>]
    helper.py whitespace [-d <dir> | --directory=<dir>]
    helper.py utf8_headers [-d <dir> | --directory=<dir>]
    helper.py migrate
    helper.py docs
    helper.py test
    helper.py release

Options:
    -h --help  This screen
    -v --version  Get version number
    -d --directory <dir>  The directory to search in. [default: .]

"""
from __future__ import print_function, with_statement
import os
import sys
import operator
from fnmatch import fnmatch
from docopt import docopt
from colorama import init, deinit, Fore

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)


def find_python_files(directory):
    """ Given a `directory`, find all `*.py` files within the heirarchy

    Expects a valid file system path for to iterate over, as a string.
    """
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch(basename, '*.py'):
                yield os.path.join(root, basename)

def find_no_docstrings(file):
    """ Given a single file, opens it and checks for docstrings.

    Finds all lines beginning with `def` (once trimmed appropriately)
    and ensures that the next line starts with either of the valid
    docstring symbols.
    """
    docstring_formats = (r'"""', r"'''")
    marked = {}
    with open(file) as f:
        for lineno, line in enumerate(f.readlines()):
            line = line.strip()
            if line and line.startswith('def'):
                marked[lineno] = line

            # if it has a docstring, delete it.
            if lineno-1 in marked and line.startswith(docstring_formats):
                del marked[lineno-1]
    return file, marked

def find_tabs_trailing_whitespace(file):
    marked = {}
    with open(file) as f:
        for lineno, line in enumerate(f.readlines()):
            if "\t" in line or line.endswith(' '):
                marked[lineno] = line
    return file, marked


utf8s = '# -*- coding: utf-8 -*-'
def find_no_utf8_headers(file):
    marked = {}
    with open(file) as f:
        for lineno, line in enumerate(f.readlines()):
            if line.strip() == utf8s:
                marked[lineno] = line
    return file, marked

def dispatch_docstrings(directory):
    """ Simple dispatch function to call find_python_files and find_no_docstrings """
    dir = os.path.realpath(directory)
    for file in find_python_files(dir):
        file, results = find_no_docstrings(file)
        if len(results.keys()) > 0:
            sorted_results = sorted(results.items(), key=operator.itemgetter(0))
            for k,v in sorted_results:
                print('%(color_file)s%(file)s%(color_reset)s @ %(color_line)sline %(line)d%(color_reset)s: %(function)s' % {
                    'color_file': Fore.YELLOW,
                    'color_reset': Fore.RESET,
                    'color_line': Fore.RED,
                    'file': file,
                    'line': k,
                    'function': v
                })


def dispatch_tabs_spaces(directory):
    dir = os.path.realpath(directory)
    for file in find_python_files(dir):
        file, results = find_tabs_trailing_whitespace(file)
        if len(results.keys()) > 0:
            sorted_results = sorted(results.items(), key=operator.itemgetter(0))
            for k,v in sorted_results:
                print('%(color_file)s%(file)s%(color_reset)s @ %(color_line)sline %(lineno)d%(color_reset)s: %(line)s' % {
                    'color_file': Fore.YELLOW,
                    'color_reset': Fore.RESET,
                    'color_line': Fore.RED,
                    'file': file,
                    'lineno': k,
                    'line': v.strip(),
                })
        else:
            print('%(color_success)sNo whitespace issues found in %(color_file)s%(file)s%(color_reset)s' % {
                'color_success': Fore.GREEN,
                'color_reset': Fore.RESET,
                'color_file': Fore.YELLOW,
                'file': file,
            })

def dispatch_utf8_headers(directory, do_update=True):
    dir = os.path.realpath(directory)
    print('{color}the following files are missing {fmt}{reset}'.format(
        fmt=utf8s, color=Fore.GREEN, reset=Fore.RESET))

    for filename in find_python_files(dir):
        filename, results = find_no_utf8_headers(filename)
        if len(results.keys()) < 1:
            print('%(color_file)s%(file)s%(color_reset)s%(color_reset)s has no utf8 comment' % {
                'color_file': Fore.YELLOW,
                'color_reset': Fore.RESET,
                'color_line': Fore.RED,
                'file': filename,
            })
            if do_update:
                with open(filename, 'r') as original:
                    data = original.read()
                with open(filename, 'w') as modified:
                    modified.write(utf8s + "\n" + data)

def dispatch_django_server(directory):
    import settings
    from django.core import management
    dir = os.path.realpath(directory)
    try:
        from tornado import httpserver, ioloop, wsgi, autoreload
        from django.core.handlers.wsgi import WSGIHandler
        use_tornado = True
    except ImportError:
        use_tornado = False
    management.setup_environ(settings)
    arguments = []
    if use_tornado:
        try:
            application = WSGIHandler()
            autoreload.start(check_time=100)
            container = wsgi.WSGIContainer(application)
            http_server = httpserver.HTTPServer(container)
            http_server.listen(8080)
            #autoreload.watch(dir)
            the_loop = ioloop.IOLoop.instance()
            the_loop.start()
        except KeyboardInterrupt:
            sys.exit(0)
    else:
        command = 'runserver'
    return management.call_command(command, verbosity=2, addrport='0.0.0.0:8080')

def dispatch_migrate():
    import settings
    from django.core import management
    management.setup_environ(settings)
    management.call_command('syncdb')
    management.call_command('migrate')

if __name__ == '__main__':
    arguments = docopt(__doc__)
    if arguments.get('--help'):
        print(__doc__)
    if arguments['docstrings']:
        dispatch_docstrings(arguments['--directory'])
    if arguments['whitespace']:
        dispatch_tabs_spaces(arguments['--directory'])
    if arguments['utf8_headers']:
        dispatch_utf8_headers(arguments['--directory'])
    if arguments['serve']:
        dispatch_django_server(arguments['--directory'])
    if arguments['migrate']:
        dispatch_migrate()

