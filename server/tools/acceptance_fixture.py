"""Local acceptance fault proxy over the actual JVM/SQLite server, never the user's DB.

18080: product HTTP proxy; 18082: test control; 18081: real upstream server.
Every reset allocates a fresh DB; restart retains the current DB. JSONL retains
fault decisions, upstream commit responses, request keys and observed child exits.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import http.client
import json
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / '.harness/v1/acceptance-fixture'
FOLDER.mkdir(parents=True, exist_ok=True)
LOCK = threading.RLock()
LOG_LOCK = threading.Lock()
rules, requests = [], []
child = None
database = None

def log(value):
    with LOG_LOCK:
        with (FOLDER / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(at=time.time(), **value), ensure_ascii=False) + '\n')

def stop_child():
    global child
    if child is not None:
        child.terminate()
        code = child.wait(timeout=15)
        log({'kind': 'upstream_exit', 'pid': child.pid, 'returncode': code})
        child = None

def start_child(fresh=False):
    global child, database
    stop_child()
    if fresh:
        database = FOLDER / (str(uuid.uuid4()) + '.db')
    env = dict(os.environ, MEMO_DB=str(database), MEMO_PORT='18081',
               MEMO_WEB_ROOT=str(ROOT / 'web/build/dist/js/productionExecutable'))
    with (FOLDER / 'upstream.log').open('ab') as stream:
        child = subprocess.Popen([str(ROOT / 'server/build/install/server/bin/server')], cwd=ROOT,
                                 env=env, stdout=stream, stderr=stream)
    for _ in range(100):
        try:
            with urllib.request.urlopen('http://127.0.0.1:18081/api/v1/memos', timeout=1):
                break
        except Exception:
            time.sleep(.1)
    else:
        raise RuntimeError('upstream did not start')
    log({'kind': 'upstream_started', 'pid': child.pid, 'database': str(database), 'fresh': fresh})

def snapshot():
    with sqlite3.connect(database) as db:
        rows = [dict(zip(['id', 'attempt_id', 'body', 'created_at'], row)) for row in
                db.execute('SELECT id,attempt_id,body,created_at FROM memos ORDER BY created_at DESC,id DESC')]
    return {'rows': rows, 'requests': list(requests), 'rules': rules, 'database': str(database)}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, data, content_type='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        self.handle_request()

    def do_GET(self):
        self.handle_request()

    def handle_request(self):
        global rules, requests
        payload = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        if self.server.server_port == 18082:
            with LOCK:
                if self.command == 'POST':
                    control = json.loads(payload or b'{}')
                    if control.get('reset'):
                        rules, requests = [], []
                        start_child(fresh=True)
                    if control.get('restart'):
                        start_child()
                    if 'rules' in control:
                        rules = control['rules']
                    # Deterministic ordering fixture is real SQLite data, not a mock response.
                    if control.get('seed_order'):
                        with sqlite3.connect(database) as db:
                            for body, date in [('tie older id', '2026-01-01T00:00:00.000Z'),
                                               ('tie newer id', '2026-01-01T00:00:00.000Z'),
                                               ('newest date', '2026-01-02T00:00:00.000Z')]:
                                db.execute('INSERT INTO memos(attempt_id,body,created_at) VALUES(?,?,?)',
                                           (str(uuid.uuid4()), body, date))
                    log({'kind': 'control', 'value': control})
                self.reply(200, json.dumps(snapshot(), ensure_ascii=False).encode())
            return
        with LOCK:
            rule = next((r.copy() for r in rules if r.get('method') == self.command
                         and r.get('path') == self.path and r.get('remaining', -1) != 0), {})
            if rule and rule.get('remaining', -1) > 0:
                next(r for r in rules if r == rule)['remaining'] -= 1
            record = {'method': self.command, 'path': self.path, 'payload': payload.decode('utf-8', errors='replace'),
                      'fault': rule, 'started': time.time()}
            requests.append(record)
        time.sleep(rule.get('delay', 0))
        status, content, content_type = 0, b'', 'application/json'
        if rule.get('status'):
            status, content = rule['status'], b'{"code":"INJECTED","message":"controlled acceptance fault"}'
        else:
            connection = http.client.HTTPConnection('127.0.0.1', 18081, timeout=20)
            try:
                connection.request(self.command, self.path, payload or None, {'Content-Type': self.headers.get('Content-Type', 'application/json')})
                response = connection.getresponse()
                status, content = response.status, response.read()
                content_type = response.getheader('Content-Type', 'application/octet-stream')
            finally:
                connection.close()
        record.update(status=status, finished=time.time())
        log(dict(kind='proxy', **record))
        if rule.get('drop_after_commit'):
            assert self.command == 'POST' and status in (200, 201), 'drop requires actual committed save'
            self.close_connection = True
            self.connection.shutdown(2)
            self.connection.close()
            return
        self.reply(status, content, content_type)

if __name__ == '__main__':
    start_child(fresh=True)
    proxy = ThreadingHTTPServer(('127.0.0.1', 18080), Handler)
    control = ThreadingHTTPServer(('127.0.0.1', 18082), Handler)
    threading.Thread(target=control.serve_forever, daemon=True).start()
    def exit_signal(*_):
        stop_child()
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, exit_signal)
    signal.signal(signal.SIGINT, exit_signal)
    log({'kind': 'fixture_ready', 'proxy': 18080, 'control': 18082, 'pid': os.getpid()})
    print('Acceptance fixture ready :18080 / control :18082', flush=True)
    try:
        proxy.serve_forever()
    finally:
        stop_child()
