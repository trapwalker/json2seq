#! /usr/bin/python3
import ijson

import json
import sys
import argparse
import typing
from itertools import islice
from functools import reduce
from contextlib import suppress
from collections import Counter


parser = argparse.ArgumentParser(description='Convert JSON to JSON Text Sequence (RFC 7464).')
parser.add_argument(
    'infile',
    type=argparse.FileType('r'), nargs='?', default=sys.stdin, help='Input JSON file (STDIN by default).')
parser.add_argument(
    '-O', dest='outfile',
    type=argparse.FileType('w'), default=sys.stdout, help='File to write output (STDOUT by default).')
parser.add_argument('--select', dest='selector', type=str, default='item', help='Selector to locate items in JSON.')
parser.add_argument('--filter', dest='fltr', type=str, nargs='*', help='Boolean filtering expression.')
parser.add_argument('--update', dest='upd', type=str, nargs='*', help='Code blocks to update item.')
parser.add_argument('--reduce', dest='rdc', type=str, help='Function to reduce dataset (`a` and `b` is arguments).')
parser.add_argument('--skip', dest='skip', type=int, default=0, help='Count of items to skip.')
parser.add_argument('--first', dest='first', type=int, help='Count of items to keep after skipped.')
parser.add_argument(
    '--rs_delimiter',
    action='store_const', const=True, default=False, help='Whether to encode using RFC 7464 RS delimiters.')
parser.add_argument(
    '--ensure_ascii',
    action='store_const', const=True, default=False, help='Use ascii chars only to JSON encoding.')
parser.add_argument(
    '--filter_error',
    default='strict', help='Action by error while filtering: skip, keep, strict (by default).')
parser.add_argument(
    '--update_error',
    default='strict', help='Action by error while updating: skip, keep, strict (by default).')


class Skip(Exception):
    pass


class ConvertingError(Exception):
    pass


class FilteringError(ConvertingError):
    pass


class UpdatingError(ConvertingError):
    pass


def safe_stringify_json(js):
    with suppress(Exception):
        return json.dumps(js, indent=2)
    return repr(js)


def filter_func(*expressions, on_error='strict'):
    item_varname = '_rec_'
    ns_global = dict()

    def func(r):
        ns_local = dict(r)
        ns_global.update({item_varname: r})
        result = None
        for expr in expressions:
            try:
                result = eval(expr, ns_global, ns_local)
                if not result:
                    return result
            except Exception as e:
                if on_error == 'skip':
                    return False
                if on_error == 'keep':
                    return True
                raise FilteringError(f'Filtering ERROR in expression {expr!r}: {e}\nOn item:\n{safe_stringify_json(r)}')
        return result

    return func


def update_func(*codes, on_error: str = 'strict'):
    item_varname = '_rec_'
    ns_global = dict()

    def func(r):
        ns_local = dict(r)
        ns_global.update({item_varname: r})
        for f in codes:
            try:
                exec(f, ns_global, ns_local)
            except Skip:
                return None
            except Exception as e:
                if on_error == 'skip':
                    return None
                if on_error == 'keep':
                    continue
                raise UpdatingError(f'Updating ERROR in expression {f!r}: {e}\nOn item:\n{safe_stringify_json(r)}')

        return ns_local.get(item_varname, ns_global.get(item_varname, None))

    return func


def reduce_func(expression, on_error='strict'):
    ns_global = dict(Counter=Counter)

    def func(a, b):
        ns_local = dict()
        ns_global.update({'a': a, 'b': b})
        try:
            result = eval(expression, ns_global, ns_local)
        except Exception as e:
            if on_error == 'strict':
                raise FilteringError(f'Reduce ERROR: {expression!r}: {e}\nOn item:\n{safe_stringify_json([a, b])}')
        else:
            return result
        return a

    return func


def main(argv: list = None):
    args = parser.parse_args(argv)
    items = ijson.items(args.infile, args.selector)
    if args.fltr:
        items = filter(filter_func(*args.fltr, on_error=args.filter_error.lower()), items)

    if args.upd:
        items = (r for r in map(update_func(*args.upd, on_error=args.update_error.lower()), items) if r is not None)

    items = islice(items, args.skip, args.first and args.first + args.skip)

    if args.rdc:
        reduce_f = reduce_func(args.rdc, on_error=args.filter_error.lower())
        items = reduce(reduce_f, items)
        if not isinstance(items, typing.Iterable):
            items = [items]

    encoder = json.JSONEncoder(ensure_ascii=args.ensure_ascii)
    leader = u"\x1e" if args.rs_delimiter else ""

    try:
        for item in items:
            line = "{}{}\n".format(leader, encoder.encode(item))
            args.outfile.write(line)
    except ConvertingError as e:
        print(e, file=sys.stderr)


if __name__ == '__main__':
    main()
