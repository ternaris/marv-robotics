# Copyright 2016 - 2020  Ternaris, all rights reserved.
# SPDX-License-Identifier: AGPL-3.0-only

import math

import pytest

from marv.sexp import (RESERVED_WORDS, Identifier, InvalidNumber, InvalidStringEscape, List,
                       Literal, ReservedWord, SexpError, UnexpectedCharacter, scan)


def test_parse_malformed():  # pylint: disable=too-many-statements
    sexp = ''
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ("Expected '('", sexp, 0)

    sexp = ' '
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ("Expected '('", sexp, 0)

    sexp = 'malformed'
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ("Expected '('", sexp, 0)

    sexp = '('
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ('Unbalanced parentheses', sexp, -1)

    sexp = r'("\q")'
    with pytest.raises(InvalidStringEscape) as einfo:
        scan(sexp)
    assert einfo.value.args == (r'\q', sexp, 2)

    sexp = r'("\u)'
    with pytest.raises(InvalidStringEscape) as einfo:
        scan(sexp)
    assert einfo.value.args == (r'\u)', sexp, 2)

    sexp = r'("\ux1234")'
    with pytest.raises(InvalidStringEscape) as einfo:
        scan(sexp)
    assert einfo.value.args == (r'\ux123', sexp, 2)

    sexp = '(-a)'
    with pytest.raises(InvalidNumber) as einfo:
        scan(sexp)
    assert einfo.value.args == ('-a', sexp, 1)

    sexp = '(")'
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ('Runaway string', sexp, 1)

    sexp = '("foo)'
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ('Runaway string', sexp, 1)

    sexp = '(()())'
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ('Missing space between tokens', sexp, 3)

    sexp = '(() '
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ('Unbalanced parentheses', sexp, -1)

    sexp = '(a'
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ('Unbalanced parentheses', sexp, -1)

    sexp = '(1'
    with pytest.raises(SexpError) as einfo:
        scan(sexp)
    assert einfo.value.args == ('Unbalanced parentheses', sexp, -1)

    sexp = '(+)'
    with pytest.raises(UnexpectedCharacter) as einfo:
        scan(sexp)
    assert einfo.value.args == ('+', sexp, 1)

    sexp = '(01)'
    with pytest.raises(InvalidNumber):
        scan(sexp)

    sexp = '(-01)'
    with pytest.raises(InvalidNumber):
        scan(sexp)

    sexp = '(1-)'
    with pytest.raises(Exception):
        scan(sexp)

    sexp = '(1\f\v\u2000\u2001)'
    rv = scan(sexp)
    assert rv.args[0].stop == 1  # pylint: disable=no-member

    sexp = '(foo-bar)'
    with pytest.raises(Exception):
        scan(sexp)


@pytest.mark.parametrize('string', range(0x20))
def test_invalid_character(string):
    sexp = f'("{chr(string)}")'
    with pytest.raises(Exception):
        scan(sexp)


@pytest.mark.parametrize('string', [
    '-inf', '-infinity', '-Inf', '-Infinity', '-nan', '-NaN',
])
def test_invalid_number(string):
    sexp = f'({string})'
    with pytest.raises(InvalidNumber):
        scan(sexp)


@pytest.mark.parametrize('string', RESERVED_WORDS)
def test_reserved_word(string):
    sexp = f'({string})'
    with pytest.raises(ReservedWord):
        scan(sexp)


def test_parse_empty():
    rv = scan('()')
    assert rv == List((), 0, 1)

    rv = scan('(())')
    assert rv == List((List((), 1, 2),), 0, 3)

    rv = scan('(() \t ()\r\n)')
    assert rv == List((List((), 1, 2), List((), 6, 7)), 0, 10)

    rv = scan('((()) ())')
    assert rv == List((List((List((), 2, 3),), 1, 4), List((), 6, 7)), 0, 8)


def test_parse_literals():
    """Test support for JSON literals."""
    rv = scan(r'("foo \" \u0022 \/ \\ \b \f \n \r \t )(" "")')
    assert rv == List((Literal('foo " " / \\ \b \f \n \r \t )(', 1, 39),
                       Literal('', 41, 42)), 0, 43)

    rv = scan('(null)')
    assert rv == List((Literal(None, 1, 4),), 0, 5)

    rv = scan('(true false)')
    assert rv == List((Literal(True, 1, 4), Literal(False, 6, 10)), 0, 11)

    rv = scan('(0 -1 42)')
    assert rv == List((Literal(0, 1, 1), Literal(-1, 3, 4), Literal(42, 6, 7)), 0, 8)
    assert rv.args[1].value == -1  # pylint: disable=no-member

    rv = scan('(1.2 -1e10 -1E+10 -1.42e-10)')
    assert rv == List((Literal(1.2, 1, 3), Literal(-1e10, 5, 9), Literal(-1e10, 11, 16),
                       Literal(-1.42e-10, 18, 26)), 0, 27)

    rv = scan('(-0.0)')
    minus_one = math.copysign(1, rv.args[0].value)  # pylint: disable=no-member
    assert minus_one == -1


def test_parse_symbols():
    rv = scan('(foo bar)')
    assert rv == List((Identifier('foo', 1, 3), Identifier('bar', 5, 7)), 0, 8)
