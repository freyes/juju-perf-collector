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
"""Collect mongostat output

  /usr/lib/juju/mongo3.2/bin/mongostat --host=127.0.0.1:37017 \
      --authenticationDatabase admin \
      --ssl --sslAllowInvalidCertificates \
      --username "admin" \
      --password "PASSWORD" 5
"""

import argparse
import gzip
import json
import os
import sys
import subprocess
import threading
import time
import yaml
from datetime import datetime
from queue import Queue, Empty  # python 3.x


TS_FMT = "%Y-%m-%dT%H:%M:%S"
MONGOSTAT = "/usr/lib/juju/mongo3.2/bin/mongostat"

if not os.path.exists(MONGOSTAT):
    sys.stderr.write(('%s is not available, please run '
                      '"apt-get install juju-mongo-tools3.2"\n') % MONGOSTAT)
    sys.exit(1)


def setup_options():
    parser = argparse.ArgumentParser(description="collect mongostat output")
    parser.add_argument('-c', '--agent-conf', dest='agent_conf',
                        default='/var/lib/juju/agents/machine-0/agent.conf',
                        help="juju agent configuration", metavar="FILE")
    parser.add_argument('-o', '--output', dest='output',
                        default='mongostat.txt.gz',
                        help=('file name where to write mongostat output, '
                              'Note: if FILE exist the data will be appended'),
                        metavar='FILE')
    parser.add_argument('-i', '--interval', dest='interval', type=int,
                        help='Collect reports on the specified interval',
                        metavar='N', default=10)
    parser.add_argument('--host', dest='host', default="127.0.0.1:37017")
    parser.add_argument('--username', dest='username', default='admin')
    parser.add_argument('-t', '--timeout', dest='timeout', metavar='N',
                        help='terminate the capture after N seconds',
                        type=int, default=0)
    return parser.parse_args()


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


def get_cmd(opts):
    with open(opts.agent_conf, 'r') as f:
        config = yaml.safe_load(f.read())

    cmd = [MONGOSTAT,
           '--host', opts.host, '--noheaders', '--json',
           '--authenticationDatabase', 'admin',
           '--ssl', '--sslAllowInvalidCertificates',
           '--username', opts.username,
           '--password', config['oldpassword'], "%d" % opts.interval]
    return cmd


def main():
    opts = setup_options()
    report = gzip.open(opts.output, 'ab')
    cmd = get_cmd(opts)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,
                         close_fds=True)
    q = Queue()
    t = threading.Thread(target=enqueue_output, args=(p.stdout, q))
    t.daemon = True  # thread dies with the program
    t.start()

    start = time.time()
    try:
        while True:
            # read line without blocking
            try:
                line = q.get_nowait()
            except Empty:
                # no output yet
                pass
            else:
                str_line = bytes.decode(line)
                sys.stdout.write(str_line)
                item = json.loads(str_line)
                ts = datetime.utcnow().strftime(TS_FMT)
                for k in item:
                    item[k]['ts'] = ts
                report.write(str.encode(json.dumps(item) + '\n'))

            if opts.timeout > 0 and (time.time() - start > opts.timeout):
                # we have to exit
                print('Reached timeout, exiting')
                sys.exit(0)
            time.sleep(opts.interval)
    except KeyboardInterrupt:
        pass
    finally:
        report.close()


if __name__ == "__main__":
    main()
