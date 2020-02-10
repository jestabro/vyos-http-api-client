#!/usr/bin/env python3

import argparse
import socket
import certifi
import urllib3
import json
import sys

op_endpoint = {
'configure':   ['set', 'delete', 'comment'],
'retrieve':    ['returnValue', 'returnValues', 'exists', 'showConfig'],
'config-file': ['save', 'load'],
'image':       ['add', 'delete']
}

def check_host(host):
    try:
        test = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise argparse.ArgumentTypeError('First positional argument must '
                                         'be hostname or ip address.')
    return host

def check_op(op):
    endpoint = None
    for end, ops in op_endpoint.items():
        if op in ops:
            endpoint = end
            break
    if endpoint == None:
        raise argparse.ArgumentTypeError('op is not one of the currently '
                                         'supported values.')
    return op

parser = argparse.ArgumentParser(description="A client for the VyOS HTTP API",
        formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('host', action="store", type=check_host)
parser.add_argument('op', action="store", type=check_op,
        help='[configure ops:]\n'+', '.join(op_endpoint['configure']) +
        '\n\n[retrieve ops:]\n'+', '.join(op_endpoint['retrieve'])  +
        '\n\n[config file ops:]\n'+', '.join(op_endpoint['config-file']) +
        '\n\n[image ops:]\n'+', '.join(op_endpoint['image']))
parser.add_argument('op_arg', nargs='*', metavar='path|file|url|name')
parser.add_argument('--id', action="store", type=str, default='testapp',
        help="api_keys id")
parser.add_argument('--key', action="store", type=str, default='qwerty',
        help="api_keys key")
parser.add_argument('--insecure', action="store_true",
        help="do not check SSL certificate")

args = vars(parser.parse_args())

if not args['insecure']:
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())
else:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    http = urllib3.PoolManager()

for end, ops in op_endpoint.items():
    if args['op'] in ops:
        endpoint = end
        break

if endpoint in ('configure', 'retrieve'):
    data = { "op": args['op'], "path": args['op_arg'] }
elif endpoint == 'config-file':
    file_arg = ''.join(args['op_arg'])
    if file_arg:
        data = { 'op': args['op'], 'file': file_arg }
    else:
        data = { 'op': args['op'] }
elif endpoint == 'image':
    file_arg = ''.join(args['op_arg'])
    if file_arg:
        if args['op'] == 'add':
            data = { 'op': args['op'], 'url': file_arg }
        if args['op'] == 'delete':
            data = { 'op': args['op'], 'name': file_arg }
    else:
        sys.exit("add/delete requires a url, respectively, image name")

enc_data = json.dumps(data).encode('utf-8')

fields = { 'id': args['id'], 'key': args['key'], 'data': enc_data }

r = http.request('POST',
        'https://{0}/{1}'.format(args['host'], endpoint),
        fields)

print(r.status)
print(r.data)

