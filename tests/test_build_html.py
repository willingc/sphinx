# -*- coding: utf-8 -*-
"""
    test_build_html
    ~~~~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re

from six import PY3, iteritems
from six.moves import html_entities

from sphinx import __display_version__
from util import remove_unicode_literals, gen_with_app
from etree13 import ElementTree as ET


ENV_WARNINGS = """\
(%(root)s/autodoc_fodder.py:docstring of autodoc_fodder\\.MarkupError:2: \
WARNING: Explicit markup ends without a blank line; unexpected \
unindent\\.\\n?
)?%(root)s/images.txt:9: WARNING: image file not readable: foo.png
%(root)s/images.txt:23: WARNING: nonlocal image URI found: \
http://www.python.org/logo.png
%(root)s/includes.txt:\\d*: WARNING: Encoding 'utf-8-sig' used for \
reading included file u'.*?wrongenc.inc' seems to be wrong, try giving an \
:encoding: option\\n?
%(root)s/includes.txt:4: WARNING: download file not readable: .*?nonexisting.png
(%(root)s/markup.txt:\\d+: WARNING: Malformed :option: u'&option', does \
not contain option marker - or -- or / or \\+
%(root)s/undecodable.txt:3: WARNING: undecodable source characters, replacing \
with "\\?": b?'here: >>>(\\\\|/)xbb<<<'
)?"""

HTML_WARNINGS = ENV_WARNINGS + """\
%(root)s/images.txt:20: WARNING: no matching candidate for image URI u'foo.\\*'
None:\\d+: WARNING: citation not found: missing
%(root)s/markup.txt:: WARNING: invalid single index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u'keyword; '
"""

if PY3:
    ENV_WARNINGS = remove_unicode_literals(ENV_WARNINGS)
    HTML_WARNINGS = remove_unicode_literals(HTML_WARNINGS)


def tail_check(check):
    rex = re.compile(check)

    def checker(nodes):
        for node in nodes:
            if node.tail and rex.search(node.tail):
                return True
        assert False, '%r not found in tail of any nodes %s' % (check, nodes)
    return checker


HTML_XPATH = {
    'images.html': [
        (".//img[@src='_images/img.png']", ''),
        (".//img[@src='_images/img1.png']", ''),
        (".//img[@src='_images/simg.png']", ''),
        (".//img[@src='_images/svgimg.svg']", ''),
    ],
    'subdir/images.html': [
        (".//img[@src='../_images/img1.png']", ''),
        (".//img[@src='../_images/rimg.png']", ''),
    ],
    'subdir/includes.html': [
        (".//a[@href='../_downloads/img.png']", ''),
        (".//img[@src='../_images/img.png']", ''),
        (".//p", 'This is an include file.'),
        (".//pre/span", 'line 1'),
        (".//pre/span", 'line 2'),
    ],
    'includes.html': [
        (".//pre", u'Max Strauß'),
        (".//a[@href='_downloads/img.png']", ''),
        (".//a[@href='_downloads/img1.png']", ''),
        (".//pre", u'"quotes"'),
        (".//pre", u"'included'"),
        (".//pre/span[@class='s']", u'üöä'),
        (".//div[@class='inc-pyobj1 highlight-text']//pre",
            r'^class Foo:\n    pass\n\s*$'),
        (".//div[@class='inc-pyobj2 highlight-text']//pre",
            r'^    def baz\(\):\n        pass\n\s*$'),
        (".//div[@class='inc-lines highlight-text']//pre",
            r'^class Foo:\n    pass\nclass Bar:\n$'),
        (".//div[@class='inc-startend highlight-text']//pre",
            u'^foo = "Including Unicode characters: üöä"\\n$'),
        (".//div[@class='inc-preappend highlight-text']//pre",
            r'(?m)^START CODE$'),
        (".//div[@class='inc-pyobj-dedent highlight-python']//span",
            r'def'),
        (".//div[@class='inc-tab3 highlight-text']//pre",
            r'-| |-'),
        (".//div[@class='inc-tab8 highlight-python']//pre/span",
            r'-|      |-'),
    ],
    'autodoc.html': [
        (".//dt[@id='test_autodoc.Class']", ''),
        (".//dt[@id='test_autodoc.function']/em", r'\*\*kwds'),
        (".//dd/p", r'Return spam\.'),
    ],
    'extapi.html': [
        (".//strong", 'from function: Foo'),
        (".//strong", 'from class: Bar'),
    ],
    'markup.html': [
        (".//title", 'set by title directive'),
        (".//p/em", 'Section author: Georg Brandl'),
        (".//p/em", 'Module author: Georg Brandl'),
        # created by the meta directive
        (".//meta[@name='author'][@content='Me']", ''),
        (".//meta[@name='keywords'][@content='docs, sphinx']", ''),
        # a label created by ``.. _label:``
        (".//div[@id='label']", ''),
        # code with standard code blocks
        (".//pre", '^some code$'),
        # an option list
        (".//span[@class='option']", '--help'),
        # admonitions
        (".//p[@class='first admonition-title']", 'My Admonition'),
        (".//p[@class='last']", 'Note text.'),
        (".//p[@class='last']", 'Warning text.'),
        # inline markup
        (".//li/strong", r'^command\\n$'),
        (".//li/strong", r'^program\\n$'),
        (".//li/em", r'^dfn\\n$'),
        (".//li/code/span[@class='pre']", r'^kbd\\n$'),
        (".//li/span", u'File \N{TRIANGULAR BULLET} Close'),
        (".//li/code/span[@class='pre']", '^a/$'),
        (".//li/code/em/span[@class='pre']", '^varpart$'),
        (".//li/code/em/span[@class='pre']", '^i$'),
        (".//a[@href='https://www.python.org/dev/peps/pep-0008']"
            "[@class='pep reference external']/strong", 'PEP 8'),
        (".//a[@href='https://www.python.org/dev/peps/pep-0008']"
            "[@class='pep reference external']/strong",
            'Python Enhancement Proposal #8'),
        (".//a[@href='https://tools.ietf.org/html/rfc1.html']"
            "[@class='rfc reference external']/strong", 'RFC 1'),
        (".//a[@href='https://tools.ietf.org/html/rfc1.html']"
            "[@class='rfc reference external']/strong", 'Request for Comments #1'),
        (".//a[@href='objects.html#envvar-HOME']"
            "[@class='reference internal']/code/span[@class='pre']", 'HOME'),
        (".//a[@href='#with']"
            "[@class='reference internal']/code/span[@class='pre']", '^with$'),
        (".//a[@href='#grammar-token-try_stmt']"
            "[@class='reference internal']/code/span", '^statement$'),
        (".//a[@href='subdir/includes.html']"
            "[@class='reference internal']/span", 'Including in subdir'),
        (".//a[@href='objects.html#cmdoption-python-c']"
            "[@class='reference internal']/code/span[@class='pre']", '-c'),
        # abbreviations
        (".//abbr[@title='abbreviation']", '^abbr$'),
        # version stuff
        (".//div[@class='versionadded']/p/span", 'New in version 0.6: '),
        (".//div[@class='versionadded']/p/span",
         tail_check('First paragraph of versionadded')),
        (".//div[@class='versionchanged']/p/span",
         tail_check('First paragraph of versionchanged')),
        (".//div[@class='versionchanged']/p",
         'Second paragraph of versionchanged'),
        # footnote reference
        (".//a[@class='footnote-reference']", r'\[1\]'),
        # created by reference lookup
        (".//a[@href='contents.html#ref1']", ''),
        # ``seealso`` directive
        (".//div/p[@class='first admonition-title']", 'See also'),
        # a ``hlist`` directive
        (".//table[@class='hlist']/tr/td/ul/li", '^This$'),
        # a ``centered`` directive
        (".//p[@class='centered']/strong", 'LICENSE'),
        # a glossary
        (".//dl/dt[@id='term-boson']", 'boson'),
        # a production list
        (".//pre/strong", 'try_stmt'),
        (".//pre/a[@href='#grammar-token-try1_stmt']/code/span", 'try1_stmt'),
        # tests for ``only`` directive
        (".//p", 'A global substitution.'),
        (".//p", 'In HTML.'),
        (".//p", 'In both.'),
        (".//p", 'Always present'),
        # tests for ``any`` role
        (".//a[@href='#with']/span", 'headings'),
        (".//a[@href='objects.html#func_without_body']/code/span", 'objects'),
    ],
    'objects.html': [
        (".//dt[@id='mod.Cls.meth1']", ''),
        (".//dt[@id='errmod.Error']", ''),
        (".//dt/code", r'long\(parameter,\s* list\)'),
        (".//dt/code", 'another one'),
        (".//a[@href='#mod.Cls'][@class='reference internal']", ''),
        (".//dl[@class='userdesc']", ''),
        (".//dt[@id='userdesc-myobj']", ''),
        (".//a[@href='#userdesc-myobj'][@class='reference internal']", ''),
        # docfields
        (".//a[@class='reference internal'][@href='#TimeInt']/em", 'TimeInt'),
        (".//a[@class='reference internal'][@href='#Time']", 'Time'),
        # C references
        (".//span[@class='pre']", 'CFunction()'),
        (".//a[@href='#c.Sphinx_DoSomething']", ''),
        (".//a[@href='#c.SphinxStruct.member']", ''),
        (".//a[@href='#c.SPHINX_USE_PYTHON']", ''),
        (".//a[@href='#c.SphinxType']", ''),
        (".//a[@href='#c.sphinx_global']", ''),
        # test global TOC created by toctree()
        (".//ul[@class='current']/li[@class='toctree-l1 current']/a[@href='']",
            'Testing object descriptions'),
        (".//li[@class='toctree-l1']/a[@href='markup.html']",
            'Testing various markup'),
        # test unknown field names
        (".//th[@class='field-name']", 'Field_name:'),
        (".//th[@class='field-name']", 'Field_name all lower:'),
        (".//th[@class='field-name']", 'FIELD_NAME:'),
        (".//th[@class='field-name']", 'FIELD_NAME ALL CAPS:'),
        (".//th[@class='field-name']", 'Field_Name:'),
        (".//th[@class='field-name']", 'Field_Name All Word Caps:'),
        (".//th[@class='field-name']", 'Field_name:'),
        (".//th[@class='field-name']", 'Field_name First word cap:'),
        (".//th[@class='field-name']", 'FIELd_name:'),
        (".//th[@class='field-name']", 'FIELd_name PARTial caps:'),
        # custom sidebar
        (".//h4", 'Custom sidebar'),
        # docfields
        (".//td[@class='field-body']/strong", '^moo$'),
        (".//td[@class='field-body']/strong", tail_check(r'\(Moo\) .* Moo')),
        (".//td[@class='field-body']/ul/li/strong", '^hour$'),
        (".//td[@class='field-body']/ul/li/em", '^DuplicateType$'),
        (".//td[@class='field-body']/ul/li/em", tail_check(r'.* Some parameter')),
    ],
    'contents.html': [
        (".//meta[@name='hc'][@content='hcval']", ''),
        (".//meta[@name='hc_co'][@content='hcval_co']", ''),
        (".//meta[@name='testopt'][@content='testoverride']", ''),
        (".//td[@class='label']", r'\[Ref1\]'),
        (".//td[@class='label']", ''),
        (".//li[@class='toctree-l1']/a", 'Testing various markup'),
        (".//li[@class='toctree-l2']/a", 'Inline markup'),
        (".//title", 'Sphinx <Tests>'),
        (".//div[@class='footer']", 'Georg Brandl & Team'),
        (".//a[@href='http://python.org/']"
            "[@class='reference external']", ''),
        (".//li/a[@href='genindex.html']/span", 'Index'),
        (".//li/a[@href='py-modindex.html']/span", 'Module Index'),
        (".//li/a[@href='search.html']/span", 'Search Page'),
        # custom sidebar only for contents
        (".//h4", 'Contents sidebar'),
        # custom JavaScript
        (".//script[@src='file://moo.js']", ''),
        # URL in contents
        (".//a[@class='reference external'][@href='http://sphinx-doc.org/']",
         'http://sphinx-doc.org/'),
        (".//a[@class='reference external'][@href='http://sphinx-doc.org/latest/']",
         'Latest reference'),
    ],
    'bom.html': [
        (".//title", " File with UTF-8 BOM"),
    ],
    'extensions.html': [
        (".//a[@href='http://python.org/dev/']", "http://python.org/dev/"),
        (".//a[@href='http://bugs.python.org/issue1000']", "issue 1000"),
        (".//a[@href='http://bugs.python.org/issue1042']", "explicit caption"),
    ],
    '_static/statictmpl.html': [
        (".//project", 'Sphinx <Tests>'),
    ],
    'genindex.html': [
        # index entries
        (".//a/strong", "Main"),
        (".//a/strong", "[1]"),
        (".//a/strong", "Other"),
        (".//a", "entry"),
        (".//dt/a", "double"),
    ],
    'footnote.html': [
        (".//a[@class='footnote-reference'][@href='#id7'][@id='id1']", r"\[1\]"),
        (".//a[@class='footnote-reference'][@href='#id8'][@id='id2']", r"\[2\]"),
        (".//a[@class='footnote-reference'][@href='#foo'][@id='id3']", r"\[3\]"),
        (".//a[@class='reference internal'][@href='#bar'][@id='id4']", r"\[bar\]"),
        (".//a[@class='footnote-reference'][@href='#id9'][@id='id5']", r"\[4\]"),
        (".//a[@class='footnote-reference'][@href='#id10'][@id='id6']", r"\[5\]"),
        (".//a[@class='fn-backref'][@href='#id1']", r"\[1\]"),
        (".//a[@class='fn-backref'][@href='#id2']", r"\[2\]"),
        (".//a[@class='fn-backref'][@href='#id3']", r"\[3\]"),
        (".//a[@class='fn-backref'][@href='#id4']", r"\[bar\]"),
        (".//a[@class='fn-backref'][@href='#id5']", r"\[4\]"),
        (".//a[@class='fn-backref'][@href='#id6']", r"\[5\]"),
    ],
    'otherext.html': [
        (".//h1", "Generated section"),
    ]
}


class NslessParser(ET.XMLParser):
    """XMLParser that throws away namespaces in tag names."""

    def _fixname(self, key):
        try:
            return self._names[key]
        except KeyError:
            name = key
            br = name.find('}')
            if br > 0:
                name = name[br+1:]
            self._names[key] = name = self._fixtext(name)
            return name


def check_xpath(etree, fname, path, check, be_found=True):
    nodes = list(etree.findall(path))
    if check is None:
        assert nodes == [], ('found any nodes matching xpath '
                             '%r in file %s' % (path, fname))
        return
    else:
        assert nodes != [], ('did not find any node matching xpath '
                             '%r in file %s' % (path, fname))
    if hasattr(check, '__call__'):
        check(nodes)
    elif not check:
        # only check for node presence
        pass
    else:
        rex = re.compile(check)
        if be_found:
            if any(node.text and rex.search(node.text) for node in nodes):
                return
        else:
            if all(node.text and not rex.search(node.text) for node in nodes):
                return

        assert False, ('%r not found in any node matching '
                       'path %s in %s: %r' % (check, path, fname,
                                              [node.text for node in nodes]))


def check_static_entries(outdir):
    staticdir = outdir / '_static'
    assert staticdir.isdir()
    # a file from a directory entry in html_static_path
    assert (staticdir / 'README').isfile()
    # a directory from a directory entry in html_static_path
    assert (staticdir / 'subdir' / 'foo.css').isfile()
    # a file from a file entry in html_static_path
    assert (staticdir / 'templated.css').isfile()
    assert (staticdir / 'templated.css').text().splitlines()[1] == __display_version__
    # a file from _static, but matches exclude_patterns
    assert not (staticdir / 'excluded.css').exists()


def check_extra_entries(outdir):
    assert (outdir / 'robots.txt').isfile()


@gen_with_app(buildername='html',
              confoverrides={'html_context.hckey_co': 'hcval_co'},
              tags=['testtag'])
def test_html_output(app, status, warning):
    app.builder.build_all()
    html_warnings = warning.getvalue().replace(os.sep, '/')
    html_warnings_exp = HTML_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
    assert re.match(html_warnings_exp + '$', html_warnings), \
        'Warnings don\'t match:\n' + \
        '--- Expected (regex):\n' + html_warnings_exp + \
        '--- Got:\n' + html_warnings

    for fname, paths in iteritems(HTML_XPATH):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()
        for path, check in paths:
            yield check_xpath, etree, fname, path, check

    check_static_entries(app.builder.outdir)
    check_extra_entries(app.builder.outdir)


@gen_with_app(buildername='html', testroot='tocdepth')
def test_tocdepth(app, status, warning):
    # issue #1251
    app.builder.build_all()

    expects = {
        'index.html': [
            (".//li[@class='toctree-l3']/a", '1.1.1. Foo A1', True),
            (".//li[@class='toctree-l3']/a", '1.2.1. Foo B1', True),
            (".//li[@class='toctree-l3']/a", '2.1.1. Bar A1', False),
            (".//li[@class='toctree-l3']/a", '2.2.1. Bar B1', False),
        ],
        'foo.html': [
            (".//h1", '1. Foo', True),
            (".//h2", '1.1. Foo A', True),
            (".//h3", '1.1.1. Foo A1', True),
            (".//h2", '1.2. Foo B', True),
            (".//h3", '1.2.1. Foo B1', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '1.1. Foo A', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '1.1.1. Foo A1', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '1.2. Foo B', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '1.2.1. Foo B1', True),
        ],
        'bar.html': [
            (".//h1", '2. Bar', True),
            (".//h2", '2.1. Bar A', True),
            (".//h2", '2.2. Bar B', True),
            (".//h3", '2.2.1. Bar B1', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '2. Bar', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '2.1. Bar A', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '2.2. Bar B', True),
            (".//div[@class='sphinxsidebarwrapper']//li/a", '2.2.1. Bar B1', False),
        ],
        'baz.html': [
            (".//h1", '2.1.1. Baz A', True),
        ],
    }

    for fname, paths in iteritems(expects):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()

        for xpath, check, be_found in paths:
            yield check_xpath, etree, fname, xpath, check, be_found


@gen_with_app(buildername='singlehtml', testroot='tocdepth')
def test_tocdepth_singlehtml(app, status, warning):
    app.builder.build_all()

    expects = {
        'index.html': [
            (".//li[@class='toctree-l3']/a", '1.1.1. Foo A1', True),
            (".//li[@class='toctree-l3']/a", '1.2.1. Foo B1', True),
            (".//li[@class='toctree-l3']/a", '2.1.1. Bar A1', False),
            (".//li[@class='toctree-l3']/a", '2.2.1. Bar B1', False),

            # index.rst
            (".//h1", 'test-tocdepth', True),

            # foo.rst
            (".//h2", '1. Foo', True),
            (".//h3", '1.1. Foo A', True),
            (".//h4", '1.1.1. Foo A1', True),
            (".//h3", '1.2. Foo B', True),
            (".//h4", '1.2.1. Foo B1', True),

            # bar.rst
            (".//h2", '2. Bar', True),
            (".//h3", '2.1. Bar A', True),
            (".//h3", '2.2. Bar B', True),
            (".//h4", '2.2.1. Bar B1', True),

            # baz.rst
            (".//h4", '2.1.1. Baz A', True),
        ],
    }

    for fname, paths in iteritems(expects):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()

        for xpath, check, be_found in paths:
            yield check_xpath, etree, fname, xpath, check, be_found


@gen_with_app(buildername='html', testroot='numfig')
def test_numfig_disabled(app, status, warning):
    app.builder.build_all()

    assert 'WARNING: invalid numfig_format: invalid' not in warning.getvalue()
    assert 'WARNING: invalid numfig_format: Fig %s %s' not in warning.getvalue()

    expects = {
        'index.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", None, True),
            (".//table/caption/span[@class='caption-number']", None, True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", None, True),
            (".//li/code/span", '^fig1$', True),
            (".//li/code/span", '^Figure%s$', True),
            (".//li/code/span", '^table-1$', True),
            (".//li/code/span", '^Table:%s$', True),
            (".//li/code/span", '^CODE_1$', True),
            (".//li/code/span", '^Code-%s$', True),
        ],
        'foo.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", None, True),
            (".//table/caption/span[@class='caption-number']", None, True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", None, True),
        ],
        'bar.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", None, True),
            (".//table/caption/span[@class='caption-number']", None, True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", None, True),
        ],
        'baz.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", None, True),
            (".//table/caption/span[@class='caption-number']", None, True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", None, True),
        ],
    }

    for fname, paths in iteritems(expects):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()

        for xpath, check, be_found in paths:
            yield check_xpath, etree, fname, xpath, check, be_found


@gen_with_app(buildername='html', testroot='numfig',
              confoverrides={'numfig': True})
def test_numfig_without_numbered_toctree(app, status, warning):
    # remove :numbered: option
    index = (app.srcdir / 'index.rst').text()
    index = re.sub(':numbered:.*', '', index, re.MULTILINE)
    (app.srcdir / 'index.rst').write_text(index, encoding='utf-8')
    app.builder.build_all()

    assert 'WARNING: invalid numfig_format: invalid' in warning.getvalue()
    assert 'WARNING: invalid numfig_format: Fig %s %s' in warning.getvalue()

    expects = {
        'index.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 9 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 10 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 9 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 10 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 9 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 10 $', True),
            (".//li/a/span", '^Fig. 9$', True),
            (".//li/a/span", '^Figure6$', True),
            (".//li/a/span", '^Table 9$', True),
            (".//li/a/span", '^Table:6$', True),
            (".//li/a/span", '^Listing 9$', True),
            (".//li/a/span", '^Code-6$', True),
            ],
        'foo.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 3 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 4 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 3 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 4 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 3 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 4 $', True),
            ],
        'bar.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 5 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 7 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 8 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 5 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 7 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 8 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 5 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 7 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 8 $', True),
        ],
        'baz.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 6 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 6 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 6 $', True),
        ],
    }

    for fname, paths in iteritems(expects):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()

        for xpath, check, be_found in paths:
            yield check_xpath, etree, fname, xpath, check, be_found


@gen_with_app(buildername='html', testroot='numfig',
              confoverrides={'numfig': True})
def test_numfig_with_numbered_toctree(app, status, warning):
    app.builder.build_all()

    assert 'WARNING: invalid numfig_format: invalid' in warning.getvalue()
    assert 'WARNING: invalid numfig_format: Fig %s %s' in warning.getvalue()

    expects = {
        'index.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2 $', True),
            (".//li/a/span", '^Fig. 1$', True),
            (".//li/a/span", '^Figure2.2$', True),
            (".//li/a/span", '^Table 1$', True),
            (".//li/a/span", '^Table:2.2$', True),
            (".//li/a/span", '^Listing 1$', True),
            (".//li/a/span", '^Code-2.2$', True),
            ],
        'foo.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.2 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.3 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.4 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.3 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.4 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.3 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.4 $', True),
            ],
        'bar.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.3 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.4 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.3 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.4 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.3 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.4 $', True),
        ],
        'baz.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.2 $', True),
        ],
    }

    for fname, paths in iteritems(expects):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()

        for xpath, check, be_found in paths:
            yield check_xpath, etree, fname, xpath, check, be_found


@gen_with_app(buildername='html', testroot='numfig',
              confoverrides={'numfig': True,
                             'numfig_format': {'figure': 'Figure:%s',
                                               'table': 'Tab_%s',
                                               'code-block': 'Code-%s'}})
def test_numfig_with_prefix(app, status, warning):
    app.builder.build_all()

    assert 'WARNING: invalid numfig_format: invalid' in warning.getvalue()
    assert 'WARNING: invalid numfig_format: Fig %s %s' in warning.getvalue()

    expects = {
        'index.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-2 $', True),
            (".//li/a/span", '^Figure:1$', True),
            (".//li/a/span", '^Figure2.2$', True),
            (".//li/a/span", '^Tab_1$', True),
            (".//li/a/span", '^Table:2.2$', True),
            (".//li/a/span", '^Code-1$', True),
            (".//li/a/span", '^Code-2.2$', True),
            ],
        'foo.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:1.1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:1.2 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:1.3 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:1.4 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_1.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_1.2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_1.3 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_1.4 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-1.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-1.2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-1.3 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-1.4 $', True),
            ],
        'bar.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:2.1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:2.3 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:2.4 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_2.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_2.3 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_2.4 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-2.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-2.3 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-2.4 $', True),
        ],
        'baz.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Figure:2.2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Tab_2.2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Code-2.2 $', True),
        ],
    }

    for fname, paths in iteritems(expects):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()

        for xpath, check, be_found in paths:
            yield check_xpath, etree, fname, xpath, check, be_found


@gen_with_app(buildername='html', testroot='numfig',
              confoverrides={'numfig': True, 'numfig_secnum_depth': 2})
def test_numfig_with_secnum_depth(app, status, warning):
    app.builder.build_all()

    assert 'WARNING: invalid numfig_format: invalid' in warning.getvalue()
    assert 'WARNING: invalid numfig_format: Fig %s %s' in warning.getvalue()

    expects = {
        'index.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2 $', True),
            (".//li/a/span", '^Fig. 1$', True),
            (".//li/a/span", '^Figure2.1.2$', True),
            (".//li/a/span", '^Table 1$', True),
            (".//li/a/span", '^Table:2.1.2$', True),
            (".//li/a/span", '^Listing 1$', True),
            (".//li/a/span", '^Code-2.1.2$', True),
            ],
        'foo.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.1.1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.1.2 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 1.2.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.1.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.1.2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 1.2.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.1.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.1.2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 1.2.1 $', True),
            ],
        'bar.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.1.1 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.1.3 $', True),
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.2.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.1.1 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.1.3 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.2.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.1.1 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.1.3 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.2.1 $', True),
        ],
        'baz.html': [
            (".//div[@class='figure']/p[@class='caption']/"
             "span[@class='caption-number']", '^Fig. 2.1.2 $', True),
            (".//table/caption/span[@class='caption-number']",
             '^Table 2.1.2 $', True),
            (".//div[@class='code-block-caption']/"
             "span[@class='caption-number']", '^Listing 2.1.2 $', True),
        ],
    }

    for fname, paths in iteritems(expects):
        parser = NslessParser()
        parser.entity.update(html_entities.entitydefs)
        fp = open(os.path.join(app.outdir, fname), 'rb')
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()

        for xpath, check, be_found in paths:
            yield check_xpath, etree, fname, xpath, check, be_found
