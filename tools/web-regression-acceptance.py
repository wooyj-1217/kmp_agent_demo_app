"""Own the Web build/static server; reuse the existing real Playwright scenario."""
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = ROOT / 'verification/web-regression' / uuid.uuid4().hex
    evidence.mkdir(parents=True)
    metadata = {'authority': 'UNTRUSTED_OBSERVATION', 'scope': 'demo local-storage browser UI',
                'phase': 'DEPENDENCY_CHECK', 'started_at': time.time()}
    server = thread = None
    try:
        declared = json.loads((ROOT / 'tools/package.json').read_text())['dependencies']['playwright']
        module = Path(os.environ.get('PLAYWRIGHT_MODULE', str(ROOT / 'tools/node_modules/playwright'))).resolve()
        actual = json.loads((module / 'package.json').read_text())['version']
        if actual != declared:
            raise RuntimeError(f'Playwright version mismatch: installed {actual}, declared {declared}')
        metadata.update(playwright_version=actual, playwright_module=str(module))
        metadata['phase'] = 'BUILD'
        build = ['rtk', 'proxy', './gradlew', ':composeApp:packageOfflineWeb', '--console=plain']
        metadata['build_command'] = build
        with (evidence / 'build.log').open('wb') as log:
            subprocess.run(build, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1200)
        distribution = ROOT / 'composeApp/build/dist/wasmJs/productionExecutable'
        if not (distribution / 'index.html').is_file():
            raise RuntimeError('Web build produced no index.html')
        metadata['distribution_sha256'] = {str(p.relative_to(distribution)): hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in sorted(distribution.rglob('*')) if p.is_file()}
        metadata['phase'] = 'SERVER_READY'
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(distribution))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}'
        with urllib.request.urlopen(url + '/index.html', timeout=5) as response:
            if response.status != 200 or b'<html' not in response.read().lower():
                raise RuntimeError('Static server did not serve the expected Web build')
        metadata.update(phase='PLAYWRIGHT_SCENARIO', url=url)
        command = ['rtk', 'proxy', 'node', 'tools/web-memo-acceptance.cjs']
        metadata['scenario_command'] = command
        environment = {**os.environ, 'MEMO_URL': url, 'PLAYWRIGHT_MODULE': str(module)}
        with (evidence / 'playwright.log').open('wb') as log:
            subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=300)
        metadata.update(result='OBSERVED_PASS', phase='FINISHED')
        return 0
    except Exception as error:
        # Missing/old result files cannot pass the outer verification runner.
        metadata.update(result='NOT_RUN' if metadata['phase'] == 'DEPENDENCY_CHECK' else 'FAIL', error=str(error))
        return 1
    finally:
        if server:
            server.shutdown()
            server.server_close()
        if thread:
            thread.join(timeout=5)
        metadata['finished_at'] = time.time()
        path = evidence / 'execution.json'
        path.write_text(json.dumps(metadata, indent=2) + '\n')
        print(json.dumps({'metadata': str(path.relative_to(ROOT)),
                          'metadata_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'result': metadata['result'], 'phase': metadata['phase']}))


if __name__ == '__main__':
    raise SystemExit(main())
