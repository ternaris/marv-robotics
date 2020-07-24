# Copyright 2016 - 2020  Ternaris, all rights reserved.
# SPDX-License-Identifier: AGPL-3.0-only

import re
from collections import namedtuple
from enum import Enum

INVALID_CHARS = tuple(chr(x) for x in range(0x20))
RESERVED_WORDS = (
    'inf', 'infinity', 'Inf', 'Infinity', 'nan', 'NaN', 'True', 'False', 'None',
)
STATE = Enum('ParserState', 'START LIST')
TOKEN_END = re.compile(r'[\s\)]', flags=re.UNICODE)
WHITESPACE = re.compile(r'\s', flags=re.UNICODE)
List = namedtuple('List', 'args start stop')
Literal = namedtuple('Literal', 'value start stop')
Identifier = namedtuple('Identifier', 'name start stop')


class SexpError(Exception):
    """Error scanning s-expression.

    SexpError(error_msg, sexp, idx)
    """


class InvalidCharacter(SexpError):
    """Invalid character within string.

    InvalidCharacter('\x00', sexp, idx)
    """


class InvalidNumber(SexpError):
    """Token is not a valid number but starts like one.

    InvalidNumber('1a', sexp, idx)
    """


class InvalidIdentifier(SexpError):
    """Identifier is invalid.

    InvalidIdentifier('a-b', sexp, idx)
    """


class InvalidStringEscape(SexpError):
    """Invalid string escape sequence.

    InvalidStringEscape('\\uXYZ', sexp, idx)
    """


class UnexpectedCharacter(SexpError):
    """Unexpected character encountered at given index.

    UnexpectedCharacter('+', sexp, idx)
    """


class ReservedWord(SexpError):
    """Identifier is a reserved word.

    ReservedWord('None', sexp, idx)
    """


def _scan_number(sexp, idx):
    start = idx
    string = ''
    while idx < len(sexp):
        char = sexp[idx]
        if TOKEN_END.match(char):
            idx -= 1
            break
        string += char
        idx += 1

    # pylint: disable=too-many-boolean-expressions
    if string[0] == '0' and len(string) > 1 or \
       string == '-0' or \
       string[:2] == '-0' and string[2] != '.' or \
       string[0] == '-' and string[1:] in RESERVED_WORDS:
        raise InvalidNumber(string, sexp, start)

    try:
        return Literal(int(string), start, idx), idx
    except ValueError:
        pass

    try:
        return Literal(float(string), start, idx), idx
    except ValueError:
        raise InvalidNumber(string, sexp, start)


def _scan_string(sexp, idx):
    start = idx
    idx += 1
    string = ''
    while idx < len(sexp):
        char = sexp[idx]
        if char == '"':
            break

        if char == '\\':
            esc, idx = _scan_string_escape(sexp, idx)
            string += esc

        elif char in INVALID_CHARS:
            raise InvalidCharacter(char, sexp, start)

        else:
            string += char

        idx += 1
    else:
        raise SexpError('Runaway string', sexp, start)

    return Literal(string, start, idx), idx


def _scan_string_escape(sexp, idx):
    start = idx
    idx += 1
    char = sexp[idx]
    esc = {
        '"': '"',
        'b': '\b',
        'f': '\f',
        'n': '\n',
        'r': '\r',
        't': '\t',
        '\\': '\\',
        '/': '/',
    }.get(char)

    if esc:
        return esc, idx

    if char == 'u':
        hexcode = sexp[idx+1:idx+5]
        try:
            if len(hexcode) != 4:
                raise ValueError()
            esc = chr(int(hexcode, 16))
        except ValueError:
            raise InvalidStringEscape(rf'\u{hexcode}', sexp, start)
        return esc, idx + 4

    raise InvalidStringEscape(f'\\{char}', sexp, start)


def _scan_identifier(sexp, idx):
    start = idx
    string = ''
    while idx < len(sexp):
        char = sexp[idx]
        if TOKEN_END.match(char):
            idx -= 1
            break

        string += char
        idx += 1

    if not string.isidentifier():
        raise InvalidIdentifier(string, start, idx)

    if string in RESERVED_WORDS:
        raise ReservedWord(string, start, idx)

    return Identifier(string, start, idx), idx


def scan(sexp):  # noqa: C901  # pylint: disable=too-many-branches
    """Scan sexp into (nested) list of tokens.

    An sexp is a space-separated list of tokens surrounded by
    parentheses. Tokens are lists or json literals.

    (null)
    (0 1 2)
    (true (false))
    (identifier ("foo" 1.2 -1e10 -100 "\u0022 \" \\ \b \f \n \r \t"))

    """
    if sexp[0:1] != '(':
        raise SexpError("Expected '('", sexp, 0)

    stack = [0]
    idx = 1
    while idx < len(sexp):
        char = sexp[idx]

        if char == '(':
            stack.append(idx)

        elif char == ')':
            tokens = []
            item = stack.pop()
            while not isinstance(item, int) and stack:
                tokens.insert(0, item)
                item = stack.pop()
            stack.append(List(tuple(tokens), item, idx))

        elif char == 'n' and sexp[idx:idx+4] == 'null':
            stack.append(Literal(None, idx, idx+3))
            idx += 3

        elif char == 't' and sexp[idx:idx+4] == 'true':
            stack.append(Literal(True, idx, idx+3))
            idx += 3

        elif char == 'f' and sexp[idx:idx+5] == 'false':
            stack.append(Literal(False, idx, idx+4))
            idx += 4

        elif char in '0123456789-':
            number, idx = _scan_number(sexp, idx)
            stack.append(number)

        elif char == '"':
            string, idx = _scan_string(sexp, idx)
            stack.append(string)

        elif char.isalpha():
            identifier, idx = _scan_identifier(sexp, idx)
            stack.append(identifier)

        elif WHITESPACE.match(char):
            pass

        else:
            raise UnexpectedCharacter(char, sexp, idx)

        idx += 1

        if isinstance(stack[-1], int):
            continue

        nextchar = sexp[idx:idx+1]
        if nextchar == ' ' and sexp[idx+1:idx+2] != ')':
            idx += 1

        elif nextchar and not TOKEN_END.match(nextchar):
            raise SexpError('Missing space between tokens', sexp, idx)

    if len(stack) > 1 or not isinstance(stack[0], List):
        raise SexpError('Unbalanced parentheses', sexp, -1)

    return stack[0]
