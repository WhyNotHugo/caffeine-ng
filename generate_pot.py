#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Generate POT
    ~~~~~~~~~~~~

    Generate a pot file with all translations for PyGTK applications
    based on the organization idea I shared in my article about i18n
    in PyGTK applications.

    :copyright: 2006-2007 by Armin Ronacher.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
from xml.dom import minidom
from compiler import parse, ast
from datetime import datetime

PO_HEADER = """#
# %(name)s Language File
#
msgid ""
msgstr ""
"Project-Id-Version: %(name)s %(version)s\\n"
"POT-Creation-Date: %(time)s\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: utf-8\\n"
"Generated-By: %(filename)s\\n"\
"""

EMPTY_STRING = ''
EMPTY_LINE = ['""\n']
LINE_SHIFT = ['\\n"\n"']


class StringCollection(object):
    """Class for collecting strings."""

    def __init__(self, basename):
        self.db = {}
        self.order = []
        self.offset = len(basename)

    def feed(self, file, line, string):
        name = file[self.offset:].lstrip('/')
        if string not in self.db:
            self.db[string] = [(name, line)]
            self.order.append(string)
        else:
            self.db[string].append((name, line))

    def __iter__(self):
        for string in self.order:
            yield string, self.db[string]


def quote(s):
    """Quotes a given string so that it is useable in a .po file."""
    result = ['"']
    firstmatch = True
    for char in s:
        if char == '\n':
            if firstmatch:
                result = EMPTY_LINE + result
                firstmatch = False
            result += LINE_SHIFT
            continue
        if char in '\t"':
            result.append('\\')
        result.append(char)
    result.append('"')
    return EMPTY_STRING.join(result)


def scan_python_file(filename, calls):
    """Scan a python file for gettext calls."""
    def scan(nodelist):
        for node in nodelist:
            if isinstance(node, ast.CallFunc):
                handle = False
                for pos, n in enumerate(node):
                    if pos == 0:
                        if isinstance(n, ast.Name) and n.name in calls:
                            handle = True
                    elif pos == 1:
                        if handle:
                            if n.__class__ is ast.Const and \
                               isinstance(n.value, str):
                                yield n.lineno, n.value
                            break
                        else:
                            for line in scan([n]):
                                yield line
            elif hasattr(node, '__iter__'):
                for n in scan(node):
                    yield n

    fp = open(filename)
    try:
        try:
            return scan(parse(fp.read()))
        except:
            print('Syntax Error in file %r' % filename, file=sys.stderr)
    finally:
        fp.close()


def scan_glade_file(filename):
    """Scan a glade file for translatable strings."""
    try:
        doc = minidom.parse(filename)
    except:
        print('Syntax Error in file %r' % filename, file=sys.stderr)
    for element in doc.getElementsByTagName('property'):
        if element.getAttribute('translatable') == 'yes':
            data = element.firstChild.nodeValue
            if data and not data.startswith('gtk-'):
                yield data


def scan_tree(pathname, calls=['_']):
    """Scans a tree for translatable strings."""
    out = StringCollection(pathname)
    for folder, _, files in os.walk(pathname):
        for filename in files:
            filename = os.path.join(folder, filename)
            if filename.endswith('.py'):
                result = scan_python_file(filename, calls)
                if result is not None:
                    for lineno, string in result:
                        out.feed(filename, lineno, string)
            elif filename.endswith('.glade'):
                result = scan_glade_file(filename)
                if result is not None:
                    for string in result:
                        out.feed(filename, None, string)
    for line in out:
        yield line


def main():
    if len(sys.argv) != 5:
        print('usage: %s <basefolder> <name> <version> <outputfile>' %
              sys.argv[0])
        sys.exit()
    output = sys.argv[4]
    output = open(output, 'w')

    print(PO_HEADER % {
        'time':     datetime.now(),
        'filename': sys.argv[0],
        'name':     sys.argv[2],
        'version':  sys.argv[3]
    }, file=output)

    basepath = sys.argv[1]
    for string, occurrences in scan_tree(basepath):
        try:
            print('msgid %s' % quote(string.encode("utf_8")), file=output)
        except Exception as data:
            print(data)
        else:
            for path, lineno in occurrences:
                print('#. file %r, line %s' % (path, lineno or '?'),
                      file=output)
            print('msgstr ""', file=output)

    output.close()

if __name__ == '__main__':
    main()
