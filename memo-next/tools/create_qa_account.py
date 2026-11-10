"""Disposable local QA fixture only. Never run this against production."""
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8910"
credentials = dict(email="qa@teum.test",password="Teum-local-qa-2026!")
def post(path, data):
    with urlopen(Request(BASE+path,json.dumps(data).encode(),{"Content-Type":"application/json"}),timeout=15) as r:
        return json.load(r)
try:
    result = post("/v1/register",credentials)
except HTTPError as error:
    if error.code != 409: raise
    error.close()
    result = post("/v1/login",credentials)
print("Local QA fixture ready:", result["email"])
