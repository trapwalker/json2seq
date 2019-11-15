#! /usr/bin/python3
import ijson

import json
import sys
import argparse
from itertools import islice


parser = argparse.ArgumentParser(description='Convert JSON to JSON Text Sequence.')
parser.add_argument(
    'infile',
    type=argparse.FileType('r'), nargs='?', default=sys.stdin, help='Input JSON file (STDIN by default).')
parser.add_argument(
    '-O', dest='outfile',
    type=argparse.FileType('w'), default=sys.stdout, help='File to write output (STDOUT by default).')
parser.add_argument('--select', dest='selector', type=str, default='item', help='Selector to locate items in JSON.')
parser.add_argument('--filter', dest='fltr', type=str, help='Boolean filtering expression.')
parser.add_argument('--update', dest='upd', type=str, nargs='*', help='Code blocks to update item.')
parser.add_argument('--skip', dest='skip', type=int, default=0, help='Count of items to skip.')
parser.add_argument('--first', dest='first', type=int, help='Count of items to keep after skipped.')
parser.add_argument(
    '--rs_delimiter',
    action='store_const', const=True, default=False, help='Whether to encode using RFC 7464 RS delimiters')
parser.add_argument(
    '--ensure_ascii',
    action='store_const', const=True, default=False, help='Use ascii chars only to JSON encoding.')
parser.add_argument(
    '--filter_error',
    default='strict', help='Action by error while filtering: skip, keep, strict (by default)/')
parser.add_argument(
    '--update_error',
    default='strict', help='Action by error while updating: skip, keep, strict (by default)/')
# todo: STRICT filtering flag


class Skip(Exception):
    pass


class ConvertingError(Exception):
    pass


class FilteringError(ConvertingError):
    pass


class UpdatingError(ConvertingError):
    pass


def safe_stringify_json(js):
    try:
        return json.dumps(js, indent=2)
    except:
        return repr(js)


def filter_func(args):
    fltr = args.fltr
    filter_error = args.filter_error.lower()

    def func(r):
        try:
            res = eval(fltr, {}, r)
        except Exception as e:
            if filter_error == 'skip':
                return False
            if filter_error == 'keep':
                return True
            raise FilteringError(f'Filtering ERROR in expression {fltr!r}: {e}\nOn item:\n{safe_stringify_json(r)}')
        else:
            return res

    return func


def update_func(args):
    upd = args.upd
    update_error = args.update_error.lower()

    def func(r):
        for f in upd:
            try:
                exec(f, {}, r)
            except Skip as e:
                return None
            except Exception as e:
                if update_error == 'skip':
                    return None
                if update_error == 'keep':
                    return r
                raise UpdatingError(f'Updating ERROR in expression {f!r}: {e}\nOn item:\n{safe_stringify_json(r)}')
            else:
                return r

    return func


def main(argv: list = None):
    args = parser.parse_args(argv)
    # print(args, file=sys.stderr)
    items = ijson.items(args.infile, args.selector)
    if args.fltr:
        items = filter(filter_func(args), items)

    if args.upd:
        items = filter(lambda r: r is not None, map(update_func(args), items))

    items = islice(items, args.skip, args.first and args.first + args.skip)

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
