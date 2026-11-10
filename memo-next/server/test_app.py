import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import ApiError, Server, Store


def put(note_id="note-1", op="op-1", revision=0, title="오늘의 생각", body="원래 내용", deleted=False):
    return dict(id=note_id, opId=op, baseRevision=revision, kind="put", title=title, body=body, pinned=False, deleted=deleted)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "test.sqlite3")
        self.a = self.store.authenticate(dict(email="a@example.com", password="test-pass-2026"), True)
        self.b = self.store.authenticate(dict(email="b@example.com", password="test-pass-2026"), True)
        self.user = self.a["userId"]

    def tearDown(self):
        self.tmp.cleanup()

    def sync(self, *ops):
        return self.store.sync(self.user, {"operations": list(ops)})

    def test_account_isolation_and_user_scoped_ids(self):
        self.sync(put())
        self.assertEqual([], self.store.sync(self.b["userId"], {})["notes"])
        self.store.sync(self.b["userId"], {"operations": [put(title="다른 계정")]})
        self.assertEqual("오늘의 생각", self.sync()["notes"][0]["title"])

    def test_retries_are_idempotent_and_restart_persists(self):
        initial = self.sync(put())
        retry = self.sync(put())
        self.assertEqual(initial, retry)
        reloaded = Store(self.store.path).sync(self.user,{})
        self.assertEqual(initial["notes"], reloaded["notes"])

    def test_concurrent_offline_edits_preserve_both_versions(self):
        self.sync(put())
        self.sync(put(op="device-a", revision=1, body="A의 수정"))
        result = self.sync(put(op="device-b", revision=1, body="B의 오프라인 수정"))
        self.assertEqual("conflict", result["results"][0]["status"])
        self.assertEqual({"A의 수정", "B의 오프라인 수정"}, {n["body"] for n in result["notes"]})
        self.assertEqual(2, len(self.sync(put(op="device-b", revision=1, body="B의 오프라인 수정"))["notes"]))

    def test_trash_restore_and_purge_remove_content(self):
        self.sync(put())
        self.sync(put(op="trash",revision=1,deleted=True))
        restored = self.sync(put(op="restore",revision=2))
        self.assertFalse(restored["notes"][0]["deleted"])
        self.sync(put(op="trash-again",revision=3,deleted=True))
        result = self.sync(dict(opId="purge",id="note-1",kind="purge",baseRevision=4))
        note = result["notes"][0]
        self.assertTrue(note["purged"])
        self.assertEqual(("",""),(note["title"],note["body"]))

    def test_stale_purge_never_deletes_newer_remote_work(self):
        self.sync(put(deleted=True))
        self.sync(put(op="other-device-restores", revision=1, body="새 작업"))
        result = self.sync(dict(opId="stale-purge", id="note-1",kind="purge",baseRevision=1))
        self.assertEqual("purge_rejected",result["results"][0]["status"])
        self.assertEqual("새 작업",result["notes"][0]["body"])

    def test_stale_device_after_purge_creates_recovery_copy(self):
        self.sync(put(deleted=True))
        self.sync(dict(opId="purge",id="note-1",kind="purge",baseRevision=1))
        result = self.sync(put(op="offline",revision=1,body="남아 있던 오프라인 편집"))
        live = [n for n in result["notes"] if not n["purged"]]
        self.assertEqual(1,len(live))
        self.assertEqual("남아 있던 오프라인 편집",live[0]["body"])

    def test_batch_validation_does_not_partially_commit(self):
        with self.assertRaises(ApiError):
            self.sync(put(),put(note_id="bad",op="bad",body="x"*200001))
        self.assertEqual([],self.sync()["notes"])

    def test_password_validation_token_revocation(self):
        with self.assertRaises(ApiError):
            self.store.authenticate(dict(email="a@example.com",password="incorrect-pass"))
        self.assertEqual(self.user,self.store.user(self.a["token"]))
        self.store.logout(self.a["token"])
        with self.assertRaises(ApiError):
            self.store.user(self.a["token"])

    def test_password_and_tokens_are_not_stored_as_plaintext(self):
        with self.store.connect() as db:
            user = db.execute("SELECT * FROM users WHERE id=?",(self.user,)).fetchone()
            token = db.execute("SELECT token FROM sessions WHERE user_id=?",(self.user,)).fetchone()[0]
        self.assertNotEqual("test-pass-2026",user["password"])
        self.assertNotEqual(self.a["token"],token)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.server = Server(("127.0.0.1",0),Store(Path(cls.tmp.name)/"http.sqlite3"))
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.tmp.cleanup()

    def test_http_auth_sync_and_unauthorized(self):
        def post(path, data, token=None):
            headers = {"Content-Type":"application/json"}
            if token: headers["Authorization"] = "Bearer "+token
            with urlopen(Request(self.url+path,json.dumps(data).encode(),headers),timeout=5) as response:
                self.assertEqual("no-store",response.headers["Cache-Control"])
                return json.load(response)
        account = post("/v1/register",dict(email="http@example.com",password="test-pass-2026"))
        response = post("/v1/sync",{"operations":[put()]},account["token"])
        self.assertEqual("오늘의 생각",response["notes"][0]["title"])
        with self.assertRaises(HTTPError) as error: post("/v1/sync",{})
        self.assertEqual(401,error.exception.code)

    def test_static_path_traversal_and_shell(self):
        with urlopen(self.url+"/") as response:
            self.assertIn("생각이 머무는".encode(),response.read())
            self.assertIn("frame-ancestors 'none'",response.headers["Content-Security-Policy"])
        with self.assertRaises(HTTPError) as error: urlopen(self.url+"/../server/app.py")
        self.assertEqual(404,error.exception.code)

    def test_malformed_json_returns_clear_error(self):
        with self.assertRaises(HTTPError) as error: urlopen(Request(self.url+"/v1/register",b'{',{"Content-Type":"application/json"}))
        self.assertEqual(400,error.exception.code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
