"""Serve this source tree on loopback only; no browser launch or remote calls."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import argparse

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--port',type=int,default=8765)
 args=parser.parse_args()
 root=Path(__file__).resolve().parents[1]
 server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(SimpleHTTPRequestHandler,directory=str(root)))
 print(f'Logic preview: http://127.0.0.1:{args.port}/demo/',flush=True)
 print('Stop with Ctrl+C. No game accounts or original server connection.',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()

if __name__=='__main__':main()
