
from jsonseq.encode import JSONSeqEncoder
import ijson

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
# todo: STRICT filtering flag


def main(argv: list = None):
    args = parser.parse_args(argv)
    # print(args, file=sys.stderr)
    items = ijson.items(args.infile, args.selector)
    if args.fltr:
        items = filter(lambda r: eval(args.fltr, {}, r), items)

    if args.upd:
        for code in args.upd:
            items = map(lambda r: exec(code, {}, r) or r, items)

    items = islice(items, args.skip, args.first and args.first + args.skip)
    encoder = JSONSeqEncoder(with_rs=args.rs_delimiter, ensure_ascii=args.ensure_ascii).encode(items)

    for line in encoder:
        args.outfile.write(line)


if __name__ == '__main__':
    main()
