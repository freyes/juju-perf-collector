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
"""Collect pprof statistics in a tar file.

This depends on facilities added to juju >= 2.0. For more details see:
https://github.com/juju/juju/wiki/pprof-facility
"""
import argparse
import datetime
import io
import os
import socket
import sys
import tarfile
import time


__description__ = 'Collect pprof information from juju'


def setup_options():
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-o', '--output', dest='outputfile',
                        help='Save pprof output to FILE', metavar='FILE',
                        default='pprof.tar.xz')
    parser.add_argument('-i', '--interval', dest='interval', type=int,
                        help='Collect reports on the specified interval',
                        metavar='N', default=600)
    parser.add_argument('-s', '--socket', dest="socket_name", metavar="SOCKET",
                        help="socket to connect to",
                        default="@jujud-machine-0")
    parser.add_argument('-r', '--reports', dest="reports", metavar="REPORTS",
                        help="coma separated list of reports to collect",
                        default="goroutine,heap")
    parser.add_argument('-t', '--timeout', dest='timeout', metavar='N',
                        help='terminate the capture after N seconds',
                        type=int, default=0)
    return parser.parse_args()


def connect(socket_name):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if socket_name.startswith('@'):
        addr = '\0' + socket_name[1:]
    else:
        addr = socket_name

    sock.connect(addr)

    return sock


def get_report(sock, report_name):
    req = "GET /debug/pprof/%s?debug=1 HTTP/1.0\r\n\r\n" % report_name
    req = str.encode(req)
    sock.sendall(req)

    report = bytes()
    while True:
        recv = sock.recv(4096, socket.SOCK_NONBLOCK)
        if len(recv) == 0:
            break

        report += recv
    return report


def add_report(tar, report_name, content):
    timestamp = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    fname = "%s.%s" % (report_name, timestamp)

    sys.stdout.write('writing %s ...' % fname)
    sys.stdout.flush()

    info = tarfile.TarInfo(name=fname)

    f = io.BytesIO()
    f.write(content)
    f.seek(0, os.SEEK_END)
    info.size = f.tell()
    f.seek(0)

    tar.addfile(tarinfo=info, fileobj=f)


def main():
    opts = setup_options()
    if os.path.lexists(opts.outputfile):
        sys.stderr.write(('ERROR: File %s already exists, choose a different '
                          'file name\n') % opts.outputfile)
        sys.exit(1)

    tar = tarfile.open(opts.outputfile, "w:xz")
    print('report file: %s' % opts.outputfile)
    start = time.time()
    try:
        while True:
            for report in opts.reports.split(','):
                sys.stdout.write('collecting %s...' % report)
                sys.stdout.flush()
                sock = connect(opts.socket_name)
                content = get_report(sock, report)
                add_report(tar, report, content)
                sock.close()
                print('done')

            if opts.timeout > 0 and (time.time() - start > opts.timeout):
                # we have to exit
                print('Reached timeout, exiting')
                sys.exit(0)
            print('waiting %d secs' % opts.interval)
            time.sleep(opts.interval)
    finally:
        tar.close()


if __name__ == "__main__":
    main()
