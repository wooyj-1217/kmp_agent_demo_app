#!/usr/bin/env python3
"""Loopback only; serve derived report tree, never the repository or symlinks."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote, urlsplit
import argparse
ROOT=Path(__file__).resolve().parents[2]/'reports/v1'
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_GET(self):
  p=(ROOT/unquote(urlsplit(self.path).path).lstrip('/')).resolve()
  if not p.is_relative_to(ROOT.resolve()) or not p.is_file() and p!=ROOT:
   self.send_error(404); return
  if p.is_file() and p.suffix not in ['.html','.json','.svg','.png']:
   self.send_error(404); return
  super().do_GET()
 def list_directory(self,path): self.send_error(404)
 def end_headers(self):
  self.send_header('Cache-Control','no-store')
  self.send_header('X-Content-Type-Options','nosniff')
  super().end_headers()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8773);args=parser.parse_args()
 print(f'Report only: http://127.0.0.1:{args.port}/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
