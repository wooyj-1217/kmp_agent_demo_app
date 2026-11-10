"""틈: dependency-free personal memo server. Run behind HTTPS outside localhost."""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

WEB = Path(__file__).resolve().parents[1] / "web"
MAX_BODY = 4 * 1024 * 1024


class ApiError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS notes(user_id TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
                    pinned INTEGER NOT NULL, deleted INTEGER NOT NULL, purged INTEGER NOT NULL DEFAULT 0,
                    revision INTEGER NOT NULL, updated_at INTEGER NOT NULL, created_at INTEGER NOT NULL, PRIMARY KEY(user_id,id));
                CREATE TABLE IF NOT EXISTS operations(user_id TEXT NOT NULL, id TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(user_id,id));
            """)
        os.chmod(self.path, 0o600)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def password_hash(password, salt):
        return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

    def authenticate(self, data, register=False):
        email, password = data.get("email"), data.get("password")
        if not isinstance(email, str) or not isinstance(password, str):
            raise ApiError(400, "이메일과 비밀번호를 입력해 주세요.")
        email = email.strip().lower()
        if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or not 10 <= len(password) <= 256:
            raise ApiError(400, "이메일 형식과 비밀번호 길이(10~256자)를 확인해 주세요.")
        with self.connect() as db:
            if register:
                salt, user_id = secrets.token_hex(16), str(uuid.uuid4())
                try:
                    db.execute("INSERT INTO users VALUES(?,?,?,?)", (user_id, email, salt, self.password_hash(password, salt)))
                except sqlite3.IntegrityError:
                    raise ApiError(409, "이미 등록된 이메일입니다. 로그인해 주세요.") from None
            row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            salt = row["salt"] if row else "00" * 16
            candidate = self.password_hash(password, salt)
            if not row or not hmac.compare_digest(candidate, row["password"]):
                raise ApiError(401, "이메일 또는 비밀번호를 확인해 주세요.")
            token = secrets.token_urlsafe(32)
            db.execute("DELETE FROM sessions WHERE expires < ?", (int(time.time()),))
            db.execute("INSERT INTO sessions VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), row["id"], int(time.time()) + 30 * 86400))
            return {"token": token, "userId": row["id"], "email": row["email"]}

    def user(self, token):
        with self.connect() as db:
            row = db.execute("SELECT user_id FROM sessions WHERE token=? AND expires>?", (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        if not row:
            raise ApiError(401, "로그인이 만료됐습니다. 다시 로그인해 주세요.")
        return row["user_id"]

    def logout(self, token):
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE token=?", (hashlib.sha256(token.encode()).hexdigest(),))

    @staticmethod
    def note(row):
        return {"id": row["id"], "title": row["title"], "body": row["body"], "pinned": bool(row["pinned"]),
                "deleted": bool(row["deleted"]), "purged": bool(row["purged"]), "revision": row["revision"], "updatedAt": row["updated_at"], "createdAt": row["created_at"]}

    def sync(self, user_id, data):
        ops = data.get("operations", [])
        if not isinstance(ops, list) or len(ops) > 500:
            raise ApiError(400, "한 번에 동기화할 수 있는 변경은 500개입니다.")
        # Validate whole batch before writing anything.
        for op in ops:
            if not isinstance(op, dict) or not all(isinstance(op.get(k), str) and 1 <= len(op[k]) <= 100 for k in ("opId", "id")):
                raise ApiError(400, "변경 식별자가 올바르지 않습니다.")
            if type(op.get("baseRevision")) is not int or op["baseRevision"] < 0 or op.get("kind") not in ("put", "purge"):
                raise ApiError(400, "변경 버전이 올바르지 않습니다.")
            if op["kind"] == "put":
                if not isinstance(op.get("title"), str) or len(op["title"]) > 300 or not isinstance(op.get("body"), str) or len(op["body"]) > 200000:
                    raise ApiError(400, "제목 300자, 본문 200,000자 이내로 입력해 주세요.")
                if type(op.get("pinned")) is not bool or type(op.get("deleted")) is not bool:
                    raise ApiError(400, "메모 상태가 올바르지 않습니다.")
        results = []
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for op in ops:
                old_result = db.execute("SELECT result FROM operations WHERE user_id=? AND id=?", (user_id, op["opId"])).fetchone()
                if old_result:
                    results.append(json.loads(old_result["result"]))
                    continue
                row = db.execute("SELECT * FROM notes WHERE user_id=? AND id=?", (user_id, op["id"])).fetchone()
                revision = row["revision"] if row else 0
                conflict = revision != op["baseRevision"] or bool(row and row["purged"])
                target, status = op["id"], "saved"
                now = int(time.time() * 1000)
                if op["kind"] == "purge":
                    if not row or row["purged"]:
                        status = "purged"
                    elif conflict or not row["deleted"]:
                        status = "purge_rejected"
                    else:
                        db.execute("UPDATE notes SET title='',body='',pinned=0,deleted=1,purged=1,revision=revision+1,updated_at=? WHERE user_id=? AND id=?", (now, user_id, target))
                        status = "purged"
                else:
                    title = op["title"]
                    if conflict:
                        target = str(uuid.uuid5(uuid.NAMESPACE_URL, user_id + ":" + op["opId"]))
                        title = title[:285] + " (충돌 사본)"
                        revision, status = 0, "conflict"
                    created = row["created_at"] if row and not conflict else now
                    db.execute("INSERT OR REPLACE INTO notes VALUES(?,?,?,?,?,?,?,?,?,?)", (user_id, target, title, op["body"], int(op["pinned"]), int(op["deleted"]) if not conflict else 0, 0, revision + 1, now, created))
                saved = db.execute("SELECT revision FROM notes WHERE user_id=? AND id=?", (user_id,target)).fetchone()
                result = {"opId": op["opId"], "noteId": target, "status": status, "revision": saved["revision"] if saved else 0}
                db.execute("INSERT INTO operations VALUES(?,?,?)", (user_id, op["opId"], json.dumps(result)))
                results.append(result)
            notes = [self.note(r) for r in db.execute("SELECT * FROM notes WHERE user_id=? ORDER BY updated_at DESC", (user_id,))]
        return {"results": results, "notes": notes}


class Handler(BaseHTTPRequestHandler):
    server_version = "Teum/1.0"

    def log_message(self, fmt, *args):
        # Avoid request bodies, credentials, query strings and token logs.
        pass

    def headers_common(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/v1/") else "no-cache")
        origin = self.headers.get("Origin", "")
        if origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def respond(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.headers_common()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.headers_common()
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/v1/health":
            return self.respond(200, {"status": "ok", "service": "teum", "version": 1})
        assets = {"/": ("index.html", "text/html"), "/index.html": ("index.html", "text/html"),
                  "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css"),
                  "/sw.js": ("sw.js", "text/javascript"), "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
                  "/icon.svg": ("icon.svg", "image/svg+xml")}
        if path not in assets:
            return self.respond(404, {"error": "페이지를 찾을 수 없습니다."})
        name, mime = assets[path]
        raw = (WEB / name).read_bytes()
        self.send_response(200)
        self.headers_common()
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https: http://localhost:* http://127.0.0.1:* http://10.0.2.2:*; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                raise ApiError(413, "요청 용량이 너무 큽니다.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ApiError(400, "요청 형식이 올바르지 않습니다.")
            path = urlparse(self.path).path
            if path in ("/v1/register", "/v1/login"):
                self.server.limit_auth(self.client_address[0])
                return self.respond(200, self.server.store.authenticate(data, path.endswith("register")))
            token = self.headers.get("Authorization", "").removeprefix("Bearer ")
            user = self.server.store.user(token)
            if path == "/v1/sync":
                return self.respond(200, self.server.store.sync(user, data))
            if path == "/v1/logout":
                self.server.store.logout(token)
                return self.respond(200, {"ok": True})
            raise ApiError(404, "API를 찾을 수 없습니다.")
        except ApiError as e:
            self.respond(e.status, {"error": e.message})
        except (ValueError, UnicodeDecodeError):
            self.respond(400, {"error": "요청 형식이 올바르지 않습니다."})
        except (sqlite3.Error, OSError):
            self.respond(503, {"error": "서버 저장에 실패했습니다. 잠시 후 다시 시도해 주세요."})


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store, allowed_origins=None):
        super().__init__(address, Handler)
        self.store = store
        self.allowed_origins = set(allowed_origins or ["null", "https://memo.local", "http://memo.local", "http://127.0.0.1:8910", "http://localhost:8910"])
        self.auth_attempts = {}
        self.auth_lock = threading.Lock()

    def limit_auth(self, ip):
        with self.auth_lock:
            now = time.monotonic()
            times = [t for t in self.auth_attempts.get(ip, []) if now - t < 60]
            if len(times) >= 20:
                raise ApiError(429, "로그인 시도가 많습니다. 1분 후 다시 시도해 주세요.")
            self.auth_attempts[ip] = times + [now]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8910)
    parser.add_argument("--db", default=str(Path(__file__).parent / "data/teum.sqlite3"))
    parser.add_argument("--origin", action="append", help="Additional allowed web origin")
    args = parser.parse_args()
    server = Server((args.host, args.port), Store(args.db))
    server.allowed_origins.update(args.origin or [])
    print(f"틈: http://{args.host}:{server.server_port}", flush=True)
    server.serve_forever()
