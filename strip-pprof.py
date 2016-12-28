#!/usr/bin/python3
# Copyright 2016 Felipe Reyes <felipe.reyes@canonical.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Remove headers from pprof files captured from juju pprof.

A typicall report looks like:

HTTP/1.0 200 OK
Content-Type: text/plain; charset=utf-8
Date: Tue, 27 Dec 2016 22:41:02 GMT

goroutine profile: total 1014
1 @ 0x1dc8128 0x1dc7f03 0x1dc37f4 0x113d6ae 0x113d8c0 0xc68c6a 0xc6a61d ...
#       0x1dc8128       runtime/pprof.writeRuntimeProfile+0xb8          ...
#       0x1dc7f03       runtime/pprof.writeGoroutine+0x93               ...
#       0x1dc37f4       runtime/pprof.(*Profile).WriteTo+0xd4           ...
#       0x113d6ae       github.com/juju/juju/worker/introspection/pprof....
...
"""
import argparse
import sys


__description__ = 'Remove headers from pprof file'


def setup_options():
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-i', '--input', dest="input", metavar="FILE",
                        help="input file")
    parser.add_argument('-o', '--output', dest="output", metavar="FILE",
                        help="output file")
    return parser.parse_args()


def main():
    opts = setup_options()

    if opts.input == "-":
        infile = sys.stdin
    else:
        infile = open(opts.input, 'r')

    if opts.output == "-":
        outfile = sys.stdout
    else:
        outfile = open(opts.output, 'w')

    empty_line_found = False
    for line in infile:
        if empty_line_found:
            outfile.write(line)
        elif not empty_line_found and line == "\n":
            empty_line_found = True

    outfile.flush()
    if opts.output != "-":
        outfile.close()


if __name__ == "__main__":
    main()
