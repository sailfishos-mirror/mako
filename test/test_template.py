import os

import pytest

from mako import exceptions
from mako import runtime
from mako import util
from mako.ext.preprocessors import convert_comments
from mako.lookup import TemplateLookup
from mako.template import ModuleInfo
from mako.template import ModuleTemplate
from mako.template import Template
from mako.testing.assertions import assert_raises
from mako.testing.assertions import assert_raises_message
from mako.testing.assertions import eq_
from mako.testing.config import config
from mako.testing.fixtures import TemplateTest
from mako.testing.helpers import flatten_result
from mako.testing.helpers import result_lines
from mako.testing.helpers import result_raw_lines


class ctx:
    def __init__(self, a, b):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *arg):
        pass


class MiscTest(TemplateTest):
    def test_crlf_linebreaks(self):
        crlf = r"""
<%
    foo = True
    bar = True
%>
% if foo and \
     bar:
     foo and bar
%endif
"""
        crlf = crlf.replace("\n", "\r\n")
        self._do_test(Template(crlf), "\r\n\r\n     foo and bar\r\n")


class EncodingTest(TemplateTest):
    def test_escapes_html_tags(self):
        from mako.exceptions import html_error_template

        x = Template(
            """
        X:
        <% raise Exception('<span style="color:red">Foobar</span>') %>
        """
        )

        try:
            x.render()
        except:
            # <h3>Exception: <span style="color:red">Foobar</span></h3>
            markup = html_error_template().render(full=False, css=False)
            assert (
                '<span style="color:red">Foobar</span></h3>'.encode("ascii")
                not in markup
            )
            assert (
                "&lt;span style=&#34;color:red&#34;"
                "&gt;Foobar&lt;/span&gt;".encode("ascii") in markup
            )

    def test_unicode(self):
        self._do_memory_test(
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
        )

    def test_encoding_doesnt_conflict(self):
        self._do_memory_test(
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
            output_encoding="utf-8",
        )

    def test_unicode_arg(self):
        val = (
            "Alors vous imaginez ma surprise, au lever du jour, quand "
            "une drôle de petite voix m’a réveillé. Elle disait: "
            "« S’il vous plaît… dessine-moi un mouton! »"
        )
        self._do_memory_test(
            "${val}",
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
            template_args={"val": val},
        )

    def test_unicode_file(self):
        self._do_file_test(
            "unicode.html",
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
        )

    def test_unicode_file_code(self):
        self._do_file_test(
            "unicode_code.html",
            ("""hi, drôle de petite voix m’a réveillé."""),
            filters=flatten_result,
        )

    def test_unicode_file_lookup(self):
        lookup = TemplateLookup(
            directories=[config.template_base],
            output_encoding="utf-8",
            default_filters=["decode.utf8"],
        )
        template = lookup.get_template("/chs_unicode_py3k.html")
        eq_(
            flatten_result(template.render_unicode(name="毛泽东")),
            ("毛泽东 是 新中国的主席<br/> Welcome 你 to 北京."),
        )

    def test_unicode_bom(self):
        self._do_file_test(
            "bom.html",
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
        )

        self._do_file_test(
            "bommagic.html",
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
        )

        assert_raises(
            exceptions.CompileException,
            Template,
            filename=self._file_path("badbom.html"),
            module_directory=config.module_base,
        )

    def test_unicode_memory(self):
        val = (
            "Alors vous imaginez ma surprise, au lever du jour, quand "
            "une drôle de petite voix m’a réveillé. Elle disait: "
            "« S’il vous plaît… dessine-moi un mouton! »"
        )
        self._do_memory_test(
            ("## -*- coding: utf-8 -*-\n" + val).encode("utf-8"),
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
        )

    def test_unicode_text(self):
        val = (
            "<%text>Alors vous imaginez ma surprise, au lever du jour, quand "
            "une drôle de petite voix m’a réveillé. Elle disait: "
            "« S’il vous plaît… dessine-moi un mouton! »</%text>"
        )
        self._do_memory_test(
            ("## -*- coding: utf-8 -*-\n" + val).encode("utf-8"),
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
        )

    def test_unicode_text_ccall(self):
        val = """
        <%def name="foo()">
            ${capture(caller.body)}
        </%def>
        <%call expr="foo()">
        <%text>Alors vous imaginez ma surprise, au lever du jour,
quand une drôle de petite voix m’a réveillé. Elle disait:
« S’il vous plaît… dessine-moi un mouton! »</%text>
        </%call>"""
        self._do_memory_test(
            ("## -*- coding: utf-8 -*-\n" + val).encode("utf-8"),
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
            filters=flatten_result,
        )

    def test_unicode_literal_in_expr(self):
        self._do_memory_test(
            (
                "## -*- coding: utf-8 -*-\n"
                '${"Alors vous imaginez ma surprise, au lever du jour, '
                "quand une drôle de petite voix m’a réveillé. "
                "Elle disait: "
                '« S’il vous plaît… dessine-moi un mouton! »"}\n'
            ).encode("utf-8"),
            (
                "Alors vous imaginez ma surprise, au lever du jour, "
                "quand une drôle de petite voix m’a réveillé. "
                "Elle disait: « S’il vous plaît… dessine-moi un mouton! »"
            ),
            filters=lambda s: s.strip(),
        )

    def test_unicode_literal_in_expr_file(self):
        self._do_file_test(
            "unicode_expr.html",
            (
                "Alors vous imaginez ma surprise, au lever du jour, "
                "quand une drôle de petite voix m’a réveillé. "
                "Elle disait: « S’il vous plaît… dessine-moi un mouton! »"
            ),
            lambda t: t.strip(),
        )

    def test_unicode_literal_in_code(self):
        self._do_memory_test(
            (
                """## -*- coding: utf-8 -*-
            <%
                context.write("Alors vous imaginez ma surprise, au """
                """lever du jour, quand une drôle de petite voix m’a """
                """réveillé. Elle disait: """
                """« S’il vous plaît… dessine-moi un mouton! »")
            %>
            """
            ).encode("utf-8"),
            (
                "Alors vous imaginez ma surprise, au lever du jour, "
                "quand une drôle de petite voix m’a réveillé. "
                "Elle disait: « S’il vous plaît… dessine-moi un mouton! »"
            ),
            filters=lambda s: s.strip(),
        )

    def test_unicode_literal_in_controlline(self):
        self._do_memory_test(
            (
                """## -*- coding: utf-8 -*-
            <%
                x = "drôle de petite voix m’a réveillé."
            %>
            % if x=="drôle de petite voix m’a réveillé.":
                hi, ${x}
            % endif
            """
            ).encode("utf-8"),
            ("""hi, drôle de petite voix m’a réveillé."""),
            filters=lambda s: s.strip(),
        )

    def test_unicode_literal_in_tag(self):
        self._do_file_test(
            "unicode_arguments.html",
            [
                ("x is: drôle de petite voix m’a réveillé"),
                ("x is: drôle de petite voix m’a réveillé"),
                ("x is: drôle de petite voix m’a réveillé"),
                ("x is: drôle de petite voix m’a réveillé"),
            ],
            filters=result_lines,
        )

        self._do_memory_test(
            util.read_file(self._file_path("unicode_arguments.html")),
            [
                ("x is: drôle de petite voix m’a réveillé"),
                ("x is: drôle de petite voix m’a réveillé"),
                ("x is: drôle de petite voix m’a réveillé"),
                ("x is: drôle de petite voix m’a réveillé"),
            ],
            filters=result_lines,
        )

    def test_unicode_literal_in_def(self):
        self._do_memory_test(
            (
                """## -*- coding: utf-8 -*-
            <%def name="bello(foo, bar)">
            Foo: ${ foo }
            Bar: ${ bar }
            </%def>
            <%call expr="bello(foo='árvíztűrő tükörfúrógép', """
                """bar='ÁRVÍZTŰRŐ TÜKÖRFÚRÓGÉP')">
            </%call>"""
            ).encode("utf-8"),
            (
                """Foo: árvíztűrő tükörfúrógép """
                """Bar: ÁRVÍZTŰRŐ TÜKÖRFÚRÓGÉP"""
            ),
            filters=flatten_result,
        )

        self._do_memory_test(
            (
                "## -*- coding: utf-8 -*-\n"
                """<%def name="hello(foo='árvíztűrő tükörfúrógép', """
                """bar='ÁRVÍZTŰRŐ TÜKÖRFÚRÓGÉP')">\n"""
                "Foo: ${ foo }\n"
                "Bar: ${ bar }\n"
                "</%def>\n"
                "${ hello() }"
            ).encode("utf-8"),
            (
                """Foo: árvíztűrő tükörfúrógép Bar: """
                """ÁRVÍZTŰRŐ TÜKÖRFÚRÓGÉP"""
            ),
            filters=flatten_result,
        )

    def test_input_encoding(self):
        """test the 'input_encoding' flag on Template, and that unicode
        objects arent double-decoded"""

        self._do_memory_test(
            ("hello ${f('śląsk')}"),
            ("hello śląsk"),
            input_encoding="utf-8",
            template_args={"f": lambda x: x},
        )

        self._do_memory_test(
            ("## -*- coding: utf-8 -*-\nhello ${f('śląsk')}"),
            ("hello śląsk"),
            template_args={"f": lambda x: x},
        )

    def test_encoding(self):
        self._do_memory_test(
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ),
            (
                "Alors vous imaginez ma surprise, au lever du jour, quand "
                "une drôle de petite voix m’a réveillé. Elle disait: "
                "« S’il vous plaît… dessine-moi un mouton! »"
            ).encode("utf-8"),
            output_encoding="utf-8",
            unicode_=False,
        )

    def test_encoding_errors(self):
        self._do_memory_test(
            (
                """KGB (transliteration of "КГБ") is the Russian-language """
                """abbreviation for Committee for State Security, """
                """(Russian: Комит́ет Госуд́арственной Безоп́асности """
                """(help·info); Komitet Gosudarstvennoy Bezopasnosti)"""
            ),
            (
                """KGB (transliteration of "КГБ") is the Russian-language """
                """abbreviation for Committee for State Security, """
                """(Russian: Комит́ет Госуд́арственной Безоп́асности """
                """(help·info); Komitet Gosudarstvennoy Bezopasnosti)"""
            ).encode("iso-8859-1", "replace"),
            output_encoding="iso-8859-1",
            encoding_errors="replace",
            unicode_=False,
        )

    def test_read_unicode(self):
        lookup = TemplateLookup(
            directories=[config.template_base],
            filesystem_checks=True,
            output_encoding="utf-8",
        )
        template = lookup.get_template("/read_unicode_py3k.html")
        # TODO: I've no idea what encoding this file is, Python 3.1.2
        # won't read the file even with open(...encoding='utf-8') unless
        # errors is specified.   or if there's some quirk in 3.1.2
        # since I'm pretty sure this test worked with py3k when I wrote it.
        template.render(path=self._file_path("internationalization.html"))


class PageArgsTest(TemplateTest):
    def test_basic(self):
        template = Template(
            """
            <%page args="x, y, z=7"/>

            this is page, ${x}, ${y}, ${z}
"""
        )

        assert (
            flatten_result(template.render(x=5, y=10))
            == "this is page, 5, 10, 7"
        )
        assert (
            flatten_result(template.render(x=5, y=10, z=32))
            == "this is page, 5, 10, 32"
        )
        assert_raises(TypeError, template.render, y=10)

    def test_inherits(self):
        lookup = TemplateLookup()
        lookup.put_string(
            "base.tmpl",
            """
        <%page args="bar" />
        ${bar}
        ${pageargs['foo']}
        ${self.body(**pageargs)}
        """,
        )
        lookup.put_string(
            "index.tmpl",
            """
        <%inherit file="base.tmpl" />
        <%page args="variable" />
        ${variable}
        """,
        )

        self._do_test(
            lookup.get_template("index.tmpl"),
            "bar foo var",
            filters=flatten_result,
            template_args={"variable": "var", "bar": "bar", "foo": "foo"},
        )

    def test_includes(self):
        lookup = TemplateLookup()
        lookup.put_string(
            "incl1.tmpl",
            """
        <%page args="bar" />
        ${bar}
        ${pageargs['foo']}
        """,
        )
        lookup.put_string(
            "incl2.tmpl",
            """
        ${pageargs}
        """,
        )
        lookup.put_string(
            "index.tmpl",
            """
        <%include file="incl1.tmpl" args="**pageargs"/>
        <%page args="variable" />
        ${variable}
        <%include file="incl2.tmpl" />
        """,
        )

        self._do_test(
            lookup.get_template("index.tmpl"),
            "bar foo var {}",
            filters=flatten_result,
            template_args={"variable": "var", "bar": "bar", "foo": "foo"},
        )

    def test_context_small(self):
        ctx = runtime.Context([].append, x=5, y=4)
        eq_(sorted(ctx.keys()), ["caller", "capture", "x", "y"])

    def test_with_context(self):
        template = Template(
            """
            <%page args="x, y, z=7"/>

            this is page, ${x}, ${y}, ${z}, ${w}
"""
        )
        # print template.code
        assert (
            flatten_result(template.render(x=5, y=10, w=17))
            == "this is page, 5, 10, 7, 17"
        )

    def test_overrides_builtins(self):
        template = Template(
            """
            <%page args="id"/>

            this is page, id is ${id}
        """
        )

        assert (
            flatten_result(template.render(id="im the id"))
            == "this is page, id is im the id"
        )

    def test_canuse_builtin_names(self):
        template = Template(
            """
            exception: ${Exception}
            id: ${id}
        """
        )
        assert (
            flatten_result(
                template.render(id="some id", Exception="some exception")
            )
            == "exception: some exception id: some id"
        )

    def test_builtin_names_dont_clobber_defaults_in_includes(self):
        lookup = TemplateLookup()
        lookup.put_string(
            "test.mako",
            """
        <%include file="test1.mako"/>

        """,
        )

        lookup.put_string(
            "test1.mako",
            """
        <%page args="id='foo'"/>

        ${id}
        """,
        )

        for template in ("test.mako", "test1.mako"):
            assert (
                flatten_result(lookup.get_template(template).render()) == "foo"
            )
            assert (
                flatten_result(lookup.get_template(template).render(id=5))
                == "5"
            )
            assert (
                flatten_result(lookup.get_template(template).render(id=id))
                == "<built-in function id>"
            )

    def test_dict_locals(self):
        template = Template(
            """
            <%
                dict = "this is dict"
                locals = "this is locals"
            %>
            dict: ${dict}
            locals: ${locals}
        """
        )
        assert (
            flatten_result(template.render())
            == "dict: this is dict locals: this is locals"
        )


class IncludeTest(TemplateTest):
    def test_basic(self):
        lookup = TemplateLookup()
        lookup.put_string(
            "a",
            """
            this is a
            <%include file="b" args="a=3,b=4,c=5"/>
        """,
        )
        lookup.put_string(
            "b",
            """
            <%page args="a,b,c"/>
            this is b.  ${a}, ${b}, ${c}
        """,
        )
        assert (
            flatten_result(lookup.get_template("a").render())
            == "this is a this is b. 3, 4, 5"
        )

    def test_localargs(self):
        lookup = TemplateLookup()
        lookup.put_string(
            "a",
            """
            this is a
            <%include file="b" args="a=a,b=b,c=5"/>
        """,
        )
        lookup.put_string(
            "b",
            """
            <%page args="a,b,c"/>
            this is b.  ${a}, ${b}, ${c}
        """,
        )
        assert (
            flatten_result(lookup.get_template("a").render(a=7, b=8))
            == "this is a this is b. 7, 8, 5"
        )

    def test_viakwargs(self):
        lookup = TemplateLookup()
        lookup.put_string(
            "a",
            """
            this is a
            <%include file="b" args="c=5, **context.kwargs"/>
        """,
        )
        lookup.put_string(
            "b",
            """
            <%page args="a,b,c"/>
            this is b.  ${a}, ${b}, ${c}
        """,
        )
        # print lookup.get_template("a").code
        assert (
            flatten_result(lookup.get_template("a").render(a=7, b=8))
            == "this is a this is b. 7, 8, 5"
        )

    def test_include_withargs(self):
        lookup = TemplateLookup()
        lookup.put_string(
            "a",
            """
            this is a
            <%include file="${i}" args="c=5, **context.kwargs"/>
        """,
        )
        lookup.put_string(
            "b",
            """
            <%page args="a,b,c"/>
            this is b.  ${a}, ${b}, ${c}
        """,
        )
        assert (
            flatten_result(lookup.get_template("a").render(a=7, b=8, i="b"))
            == "this is a this is b. 7, 8, 5"
        )

    def test_within_ccall(self):
        lookup = TemplateLookup()
        lookup.put_string("a", """this is a""")
        lookup.put_string(
            "b",
            """
        <%def name="bar()">
            bar: ${caller.body()}
            <%include file="a"/>
        </%def>
        """,
        )
        lookup.put_string(
            "c",
            """
        <%namespace name="b" file="b"/>
        <%b:bar>
            calling bar
        </%b:bar>
        """,
        )
        assert (
            flatten_result(lookup.get_template("c").render())
            == "bar: calling bar this is a"
        )

    def test_include_error_handler(self):
        def handle(context, error):
            context.write("include error")
            return True

        lookup = TemplateLookup(include_error_handler=handle)
        lookup.put_string(
            "a",
            """
            this is a.
            <%include file="b"/>
        """,
        )
        lookup.put_string(
            "b",
            """
            this is b ${1/0} end.
        """,
        )
        assert (
            flatten_result(lookup.get_template("a").render())
            == "this is a. this is b include error"
        )


class UndefinedVarsTest(TemplateTest):
    @pytest.mark.parametrize(
        "filters",
        [
            ["str", "n"],
            ["n"],
            ["str", "h"],
            ["h"],
            [],
        ],
    )
    def test_140_regression(self, filters):
        """test #415, regression on #140"""

        t1 = Template(
            "hello world ${x}",
            strict_undefined=True,
            default_filters=filters,
        )

        t1.render_unicode(x="hi")

    def test_undefined(self):
        t = Template(
            """
            % if x is UNDEFINED:
                undefined
            % else:
                x: ${x}
            % endif
        """
        )

        assert result_lines(t.render(x=12)) == ["x: 12"]
        assert result_lines(t.render(y=12)) == ["undefined"]

    def test_strict(self):
        t = Template(
            """
            % if x is UNDEFINED:
                undefined
            % else:
                x: ${x}
            % endif
        """,
            strict_undefined=True,
        )

        assert result_lines(t.render(x=12)) == ["x: 12"]

        assert_raises(NameError, t.render, y=12)

        l = TemplateLookup(strict_undefined=True)
        l.put_string("a", "some template")
        l.put_string(
            "b",
            """
            <%namespace name='a' file='a' import='*'/>
            % if x is UNDEFINED:
                undefined
            % else:
                x: ${x}
            % endif
        """,
        )

        assert result_lines(t.render(x=12)) == ["x: 12"]

        assert_raises(NameError, t.render, y=12)

    def test_expression_declared(self):
        t = Template(
            """
            ${",".join([t for t in ("a", "b", "c")])}
        """,
            strict_undefined=True,
        )

        eq_(result_lines(t.render()), ["a,b,c"])

        t = Template(
            """
            <%self:foo value="${[(val, n) for val, n in [(1, 2)]]}"/>

            <%def name="foo(value)">
                ${value}
            </%def>

        """,
            strict_undefined=True,
        )

        eq_(result_lines(t.render()), ["[(1, 2)]"])

        t = Template(
            """
            <%call expr="foo(value=[(val, n) for val, n in [(1, 2)]])" />

            <%def name="foo(value)">
                ${value}
            </%def>

        """,
            strict_undefined=True,
        )

        eq_(result_lines(t.render()), ["[(1, 2)]"])

        l = TemplateLookup(strict_undefined=True)
        l.put_string("i", "hi, ${pageargs['y']}")
        l.put_string(
            "t",
            """
            <%include file="i" args="y=[x for x in range(3)]" />
        """,
        )
        eq_(result_lines(l.get_template("t").render()), ["hi, [0, 1, 2]"])

        l.put_string(
            "q",
            """
            <%namespace name="i" file="${(str([x for x in range(3)][2]) + """
            """'i')[-1]}" />
            ${i.body(y='x')}
        """,
        )
        eq_(result_lines(l.get_template("q").render()), ["hi, x"])

        t = Template(
            """
            <%
                y = lambda q: str(q)
            %>
            ${y('hi')}
        """,
            strict_undefined=True,
        )
        eq_(result_lines(t.render()), ["hi"])

    def test_list_comprehensions_plus_undeclared_nonstrict(self):
        # traditional behavior.  variable inside a list comprehension
        # is treated as an "undefined", so is pulled from the context.
        t = Template(
            """
            t is: ${t}

            ${",".join([t for t in ("a", "b", "c")])}
        """
        )

        eq_(result_lines(t.render(t="T")), ["t is: T", "a,b,c"])

    def test_traditional_assignment_plus_undeclared(self):
        t = Template(
            """
            t is: ${t}

            <%
                t = 12
            %>
        """
        )
        assert_raises(UnboundLocalError, t.render, t="T")

    def test_list_comprehensions_plus_undeclared_strict(self):
        # with strict, a list comprehension now behaves
        # like the undeclared case above.
        t = Template(
            """
            t is: ${t}

            ${",".join([t for t in ("a", "b", "c")])}
        """,
            strict_undefined=True,
        )

        eq_(result_lines(t.render(t="T")), ["t is: T", "a,b,c"])

    def test_dict_comprehensions_in_function_plus_undeclared_strict(self):
        t = Template(
            """
<%
    def foo():
        return {s[0]: s for s in ('foo',)}
%>

${ foo()['f'] }
""",
            strict_undefined=True,
        )

        eq_(result_lines(t.render()), ["foo"])

    def test_nested_list_comprehensions_in_function_plus_undeclared_strict(
        self,
    ):
        t = Template(
            """
<%foo = lambda b : sum(f for s in b for f in s)%>\
${ foo(([1,2],[3,4]))}
""",
            strict_undefined=True,
        )

        eq_(result_lines(t.render()), ["10"])


class StopRenderingTest(TemplateTest):
    def test_return_in_template(self):
        t = Template(
            """
           Line one
           <% return STOP_RENDERING %>
           Line Three
        """,
            strict_undefined=True,
        )

        eq_(result_lines(t.render()), ["Line one"])


class ReservedNameTest(TemplateTest):
    def test_names_on_context(self):
        for name in ("context", "loop", "UNDEFINED", "STOP_RENDERING"):
            assert_raises_message(
                exceptions.NameConflictError,
                r"Reserved words passed to render\(\): %s" % name,
                Template("x").render,
                **{name: "foo"},
            )

    def test_names_in_template(self):
        for name in ("context", "loop", "UNDEFINED", "STOP_RENDERING"):
            assert_raises_message(
                exceptions.NameConflictError,
                r"Reserved words declared in template: %s" % name,
                Template,
                "<%% %s = 5 %%>" % name,
            )

    def test_exclude_loop_context(self):
        self._do_memory_test(
            "loop is ${loop}",
            "loop is 5",
            template_args=dict(loop=5),
            enable_loop=False,
        )

    def test_exclude_loop_template(self):
        self._do_memory_test(
            "<% loop = 12 %>loop is ${loop}", "loop is 12", enable_loop=False
        )


class ControlTest(TemplateTest):
    def test_control(self):
        t = Template(
            """
    ## this is a template.
    % for x in y:
    %   if 'test' in x:
        yes x has test
    %   else:
        no x does not have test
    %endif
    %endfor
"""
        )
        assert result_lines(
            t.render(
                y=[
                    {"test": "one"},
                    {"foo": "bar"},
                    {"foo": "bar", "test": "two"},
                ]
            )
        ) == ["yes x has test", "no x does not have test", "yes x has test"]

    def test_blank_control_1(self):
        self._do_memory_test(
            """
            % if True:
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_blank_control_2(self):
        self._do_memory_test(
            """
            % if True:
            % elif True:
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_blank_control_3(self):
        self._do_memory_test(
            """
            % if True:
            % else:
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_blank_control_4(self):
        self._do_memory_test(
            """
            % if True:
            % elif True:
            % else:
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_blank_control_5(self):
        self._do_memory_test(
            """
            % for x in range(10):
            % endfor
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_blank_control_6(self):
        self._do_memory_test(
            """
            % while False:
            % endwhile
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_blank_control_7(self):
        self._do_memory_test(
            """
            % try:
            % except:
            % endtry
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_blank_control_8(self):
        self._do_memory_test(
            """
            % with ctx('x', 'w') as fp:
            % endwith
            """,
            "",
            filters=lambda s: s.strip(),
            template_args={"ctx": ctx},
        )

    def test_blank_control_9(self):
        self._do_memory_test(
            """
            % if True:
            % elif False:
            false
            % else:
            broken
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
            template_args={"ctx": ctx},
        )

    def test_blank_control_10(self):
        self._do_memory_test(
            """
            % if True:
            % else:
            test
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
            template_args={"ctx": ctx},
        )

    def test_blank_control_11(self):
        self._do_memory_test(
            """
            % try:
            % except:
            error
            % endtry
            """,
            "",
            filters=lambda s: s.strip(),
            template_args={"ctx": ctx},
        )

    def test_commented_blank_control_1(self):
        self._do_memory_test(
            """
            % if True:
            ## comment
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_commented_blank_control_2(self):
        self._do_memory_test(
            """
            % if True:
            ## comment
            % elif True:
            ## comment
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_commented_blank_control_3(self):
        self._do_memory_test(
            """
            % if True:
            ## comment
            % else:
            ## comment
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_commented_blank_control_4(self):
        self._do_memory_test(
            """
            % if True:
            ## comment
            % elif True:
            ## comment
            % else:
            ## comment
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_commented_blank_control_5(self):
        self._do_memory_test(
            """
            % for x in range(10):
            ## comment
            % endfor
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_commented_blank_control_6(self):
        self._do_memory_test(
            """
            % while False:
            ## comment
            % endwhile
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_commented_blank_control_7(self):
        self._do_memory_test(
            """
            % try:
            ## comment
            % except:
            ## comment
            % endtry
            """,
            "",
            filters=lambda s: s.strip(),
        )

    def test_commented_blank_control_8(self):
        self._do_memory_test(
            """
            % with ctx('x', 'w') as fp:
            ## comment
            % endwith
            """,
            "",
            filters=lambda s: s.strip(),
            template_args={"ctx": ctx},
        )

    def test_commented_blank_control_9(self):
        self._do_memory_test(
            """
            % if True:
            ## comment
            % elif False:
            false
            % else:
            broken
            % endif
            """,
            "",
            filters=lambda s: s.strip(),
            template_args={"ctx": ctx},
        )

    def test_commented_blank_control_10(self):
        self._do_memory_test(
            """
            % try:
            ## comment
            % except:
            error
            % endtry
            """,
            "",
            filters=lambda s: s.strip(),
            template_args={"ctx": ctx},
        )

    def test_multiline_control(self):
        t = Template(
            """
    % for x in \\
        [y for y in [1,2,3]]:
        ${x}
    % endfor
"""
        )
        # print t.code
        assert flatten_result(t.render()) == "1 2 3"


class GlobalsTest(TemplateTest):
    def test_globals(self):
        self._do_memory_test(
            """
                <%!
                    y = "hi"
                %>
            y is ${y}
            """,
            "y is hi",
            filters=lambda t: t.strip(),
        )


class RichTracebackTest(TemplateTest):
    def _do_test_traceback(self, utf8, memory, syntax):
        if memory:
            if syntax:
                source = (
                    '## coding: utf-8\n<% print "m’a réveillé. '
                    "Elle disait: « S’il vous plaît… dessine-moi "
                    "un mouton! » %>"
                )
            else:
                source = (
                    '## coding: utf-8\n<% print u"m’a réveillé. '
                    "Elle disait: « S’il vous plaît… dessine-moi un "
                    'mouton! »" + str(5/0) %>'
                )
            if utf8:
                source = source.encode("utf-8")
            else:
                source = source
            templateargs = {"text": source}
        else:
            if syntax:
                filename = "unicode_syntax_error.html"
            else:
                filename = "unicode_runtime_error.html"
            source = util.read_file(self._file_path(filename), "rb")
            if not utf8:
                source = source.decode("utf-8")
            templateargs = {"filename": self._file_path(filename)}
        try:
            template = Template(**templateargs)
            if not syntax:
                template.render_unicode()
            assert False
        except Exception:
            tback = exceptions.RichTraceback()
            if utf8:
                assert tback.source == source.decode("utf-8")
            else:
                assert tback.source == source


for utf8 in (True, False):
    for memory in (True, False):
        for syntax in (True, False):

            def _do_test(self):
                self._do_test_traceback(utf8, memory, syntax)

            name = "test_%s_%s_%s" % (
                utf8 and "utf8" or "unicode",
                memory and "memory" or "file",
                syntax and "syntax" or "runtime",
            )
            _do_test.__name__ = name
            setattr(RichTracebackTest, name, _do_test)
            del _do_test


class ModuleDirTest(TemplateTest):
    def teardown_method(self):
        import shutil

        shutil.rmtree(config.module_base, True)

    def test_basic(self):
        t = self._file_template("modtest.html")
        t2 = self._file_template("subdir/modtest.html")

        eq_(
            t.module.__file__,
            os.path.join(config.module_base, "modtest.html.py"),
        )
        eq_(
            t2.module.__file__,
            os.path.join(config.module_base, "subdir", "modtest.html.py"),
        )

    def test_callable(self):
        def get_modname(filename, uri):
            return os.path.join(
                config.module_base,
                os.path.dirname(uri)[1:],
                "foo",
                os.path.basename(filename) + ".py",
            )

        lookup = TemplateLookup(
            config.template_base, modulename_callable=get_modname
        )
        t = lookup.get_template("/modtest.html")
        t2 = lookup.get_template("/subdir/modtest.html")
        eq_(
            t.module.__file__,
            os.path.join(config.module_base, "foo", "modtest.html.py"),
        )
        eq_(
            t2.module.__file__,
            os.path.join(
                config.module_base, "subdir", "foo", "modtest.html.py"
            ),
        )

    def test_custom_writer(self):
        canary = []

        def write_module(source, outputpath):
            f = open(outputpath, "wb")
            canary.append(outputpath)
            f.write(source)
            f.close()

        lookup = TemplateLookup(
            config.template_base,
            module_writer=write_module,
            module_directory=config.module_base,
        )
        lookup.get_template("/modtest.html")
        lookup.get_template("/subdir/modtest.html")
        eq_(
            canary,
            [
                os.path.join(config.module_base, "modtest.html.py"),
                os.path.join(config.module_base, "subdir", "modtest.html.py"),
            ],
        )


class FilenameToURITest(TemplateTest):
    def test_windows_paths(self):
        """test that windows filenames are handled appropriately by
        Template."""

        current_path = os.path
        import ntpath

        os.path = ntpath
        try:

            class NoCompileTemplate(Template):
                def _compile_from_file(self, path, filename):
                    self.path = path
                    return Template("foo bar").module

            t1 = NoCompileTemplate(
                filename="c:\\foo\\template.html",
                module_directory="c:\\modules\\",
            )

            eq_(t1.uri, "/foo/template.html")
            eq_(t1.path, "c:\\modules\\foo\\template.html.py")

            t1 = NoCompileTemplate(
                filename="c:\\path\\to\\templates\\template.html",
                uri="/bar/template.html",
                module_directory="c:\\modules\\",
            )

            eq_(t1.uri, "/bar/template.html")
            eq_(t1.path, "c:\\modules\\bar\\template.html.py")

        finally:
            os.path = current_path

    def test_posix_paths(self):
        """test that posixs filenames are handled appropriately by Template."""

        current_path = os.path
        import posixpath

        os.path = posixpath
        try:

            class NoCompileTemplate(Template):
                def _compile_from_file(self, path, filename):
                    self.path = path
                    return Template("foo bar").module

            t1 = NoCompileTemplate(
                filename="/var/www/htdocs/includes/template.html",
                module_directory="/var/lib/modules",
            )

            eq_(t1.uri, "/var/www/htdocs/includes/template.html")
            eq_(
                t1.path,
                "/var/lib/modules/var/www/htdocs/includes/template.html.py",
            )

            t1 = NoCompileTemplate(
                filename="/var/www/htdocs/includes/template.html",
                uri="/bar/template.html",
                module_directory="/var/lib/modules",
            )

            eq_(t1.uri, "/bar/template.html")
            eq_(t1.path, "/var/lib/modules/bar/template.html.py")

        finally:
            os.path = current_path

    def test_dont_accept_relative_outside_of_root(self):
        assert_raises_message(
            exceptions.TemplateLookupException,
            'Template uri "../../foo.html" is invalid - it '
            "cannot be relative outside of the root path",
            Template,
            "test",
            uri="../../foo.html",
        )

        assert_raises_message(
            exceptions.TemplateLookupException,
            'Template uri "/../../foo.html" is invalid - it '
            "cannot be relative outside of the root path",
            Template,
            "test",
            uri="/../../foo.html",
        )

        # normalizes in the root is OK
        t = Template("test", uri="foo/bar/../../foo.html")
        eq_(t.uri, "foo/bar/../../foo.html")


class ModuleTemplateTest(TemplateTest):
    def test_module_roundtrip(self):
        lookup = TemplateLookup()

        template = Template(
            """
        <%inherit file="base.html"/>

        % for x in range(5):
            ${x}
        % endfor
""",
            lookup=lookup,
        )

        base = Template(
            """
        This is base.
        ${self.body()}
""",
            lookup=lookup,
        )

        lookup.put_template("base.html", base)
        lookup.put_template("template.html", template)

        assert result_lines(template.render()) == [
            "This is base.",
            "0",
            "1",
            "2",
            "3",
            "4",
        ]

        lookup = TemplateLookup()
        template = ModuleTemplate(template.module, lookup=lookup)
        base = ModuleTemplate(base.module, lookup=lookup)

        lookup.put_template("base.html", base)
        lookup.put_template("template.html", template)

        assert result_lines(template.render()) == [
            "This is base.",
            "0",
            "1",
            "2",
            "3",
            "4",
        ]


class TestTemplateAPI:
    def test_metadata(self):
        t = Template(
            """
Text
Text
% if bar:
    ${expression}
% endif

<%include file='bar'/>

""",
            uri="/some/template",
        )
        eq_(
            ModuleInfo.get_module_source_metadata(t.code, full_line_map=True),
            {
                "full_line_map": [
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    1,
                    4,
                    5,
                    5,
                    5,
                    7,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                ],
                "source_encoding": "utf-8",
                "filename": None,
                "line_map": {
                    35: 29,
                    15: 0,
                    22: 1,
                    23: 4,
                    24: 5,
                    25: 5,
                    26: 5,
                    27: 7,
                    28: 8,
                    29: 8,
                },
                "uri": "/some/template",
            },
        )

    def test_metadata_two(self):
        t = Template(
            """
Text
Text
% if bar:
    ${expression}
% endif

    <%block name="foo">
        hi block
    </%block>


""",
            uri="/some/template",
        )
        eq_(
            ModuleInfo.get_module_source_metadata(t.code, full_line_map=True),
            {
                "full_line_map": [
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    1,
                    4,
                    5,
                    5,
                    5,
                    7,
                    7,
                    7,
                    7,
                    7,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                ],
                "source_encoding": "utf-8",
                "filename": None,
                "line_map": {
                    34: 10,
                    40: 8,
                    46: 8,
                    15: 0,
                    52: 46,
                    24: 1,
                    25: 4,
                    26: 5,
                    27: 5,
                    28: 5,
                    29: 7,
                },
                "uri": "/some/template",
            },
        )


class PreprocessTest(TemplateTest):
    def test_old_comments(self):
        t = Template(
            """
        im a template
# old style comment
    # more old style comment

    ## new style comment
    - # not a comment
    - ## not a comment
""",
            preprocessor=convert_comments,
        )

        assert (
            flatten_result(t.render())
            == "im a template - # not a comment - ## not a comment"
        )


class LexerTest(TemplateTest):
    def _fixture(self):
        from mako.parsetree import TemplateNode, Text

        class MyLexer:
            encoding = "ascii"

            def __init__(self, *arg, **kw):
                pass

            def parse(self):
                t = TemplateNode("foo")
                t.nodes.append(
                    Text(
                        "hello world",
                        source="foo",
                        lineno=0,
                        pos=0,
                        filename=None,
                    )
                )
                return t

        return MyLexer

    def _test_custom_lexer(self, template):
        eq_(result_lines(template.render()), ["hello world"])

    def test_via_template(self):
        t = Template("foo", lexer_cls=self._fixture())
        self._test_custom_lexer(t)

    def test_via_lookup(self):
        tl = TemplateLookup(lexer_cls=self._fixture())
        tl.put_string("foo", "foo")
        t = tl.get_template("foo")
        self._test_custom_lexer(t)


class FuturesTest(TemplateTest):
    def test_future_import(self):
        t = Template("foobar", future_imports=["annotations"])
        assert t.code.startswith("from __future__ import annotations")


class EscapeTest(TemplateTest):
    def test_percent_escape(self):
        t = Template(
            """%% do something
%%% do something
if <some condition>:
    %%%% do something
"""
        )
        assert result_raw_lines(t.render()) == [
            "% do something",
            "%% do something",
            "if <some condition>:",
            "    %%% do something",
        ]

    def test_percent_escape2(self):
        t = Template(
            """
% for i in [1, 2, 3]:
    %% do something ${i}
% endfor
"""
        )
        assert result_raw_lines(t.render()) == [
            "    % do something 1",
            "    % do something 2",
            "    % do something 3",
        ]

    def test_inline_percent(self):
        t = Template(
            """
% for i in [1, 2, 3]:
%% foo
bar %% baz
% endfor
"""
        )
        assert result_raw_lines(t.render()) == [
            "% foo",
            "bar %% baz",
            "% foo",
            "bar %% baz",
            "% foo",
            "bar %% baz",
        ]

    def test_listcomp_in_func_strict(self):
        t = Template(
            """
<%
    mydict = { 'foo': 1 }
    def getkeys(x):
        return [ k for k in x.keys() ]
%>

${ ','.join( getkeys(mydict) ) }
""",
            strict_undefined=True,
        )
        assert result_raw_lines(t.render()) == ["foo"]

    def test_setcomp_in_func_strict(self):
        t = Template(
            """
<%
    mydict = { 'foo': 1 }
    def getkeys(x):
        return { k for k in x.keys() }
%>

${ ','.join( getkeys(mydict) ) }
""",
            strict_undefined=True,
        )
        assert result_raw_lines(t.render()) == ["foo"]

    def test_generator_in_func_strict(self):
        t = Template(
            """
<%
    mydict = { 'foo': 1 }
    def getkeys(x):
        return ( k for k in x.keys())
%>

${ ','.join( getkeys(mydict) ) }
""",
            strict_undefined=True,
        )
        assert result_raw_lines(t.render()) == ["foo"]

    def test_dictcomp_in_func_strict(self):
        t = Template(
            """
<%
    def square():
        return {i: i**2 for i in range(10)}
%>

${ square()[3] }
""",
            strict_undefined=True,
        )
        assert result_raw_lines(t.render()) == ["9"]
