"""Run a fresh simulator XCTest, then convert its actual xcresult cases to JUnit."""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
output = root / 'verification/memo-evidence'
output.mkdir(parents=True, exist_ok=True)
token = uuid.uuid4().hex
bundle = output / ('ios-' + token + '.xcresult')
junit = output / 'ios-result.xml'
device = os.environ.get('MEMO_IOS_DEVICE')
if not device:
    inventory = json.loads(subprocess.check_output(['rtk', 'proxy', 'xcrun', 'simctl', 'list', 'devices', 'booted', '--json'], text=True))
    booted = [item['udid'] for items in inventory['devices'].values() for item in items if item['state'] == 'Booted']
    if len(booted) != 1:
        raise RuntimeError('Set MEMO_IOS_DEVICE or boot exactly one simulator')
    device = booted[0]
command = ['rtk', 'proxy', 'xcodebuild', '-project', 'iosApp/Moa.xcodeproj',
           '-scheme', 'Moa', '-configuration', 'Debug', '-destination',
           'platform=iOS Simulator,id=' + device,
           '-derivedDataPath', str(output / 'ios-derived'), '-resultBundlePath', str(bundle),
           '-only-testing:MoaUITests/YeobackUITests/testCreateDiscardAndPersistAcrossLaunch',
           'CODE_SIGNING_ALLOWED=NO', 'test']
with (output / ('ios-' + token + '.log')).open('w') as log:
    result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
metadata = {'command': command, 'exit_code': result.returncode, 'xcresult': str(bundle)}
try:
    parsed = subprocess.run(['rtk', 'proxy', 'xcrun', 'xcresulttool', 'get', 'test-results', 'tests',
                             '--path', str(bundle), '--compact'], cwd=root, capture_output=True, text=True, check=True)
    data = json.loads(parsed.stdout)
    (output / ('ios-' + token + '-tests.json')).write_text(json.dumps(data, indent=2))
    cases = []
    def visit(node):
        if node.get('nodeType') == 'Test Case':
            cases.append(node)
        else:
            for child in node.get('children', []):
                visit(child)
    for node in data['testNodes']:
        visit(node)
    suite = ET.Element('testsuite', name='MoaUITests', tests=str(len(cases)))
    failures = skipped = 0
    for case in cases:
        identifier = case.get('nodeIdentifier', case['name'])
        classname, _, name = identifier.rpartition('/')
        element = ET.SubElement(suite, 'testcase', classname=classname, name=name,
                                time=str(case.get('durationInSeconds', 0)))
        status = case.get('result')
        if status == 'Skipped':
            skipped += 1
            ET.SubElement(element, 'skipped', message=case.get('details', 'Skipped by XCTest'))
        elif status != 'Passed':
            failures += 1
            ET.SubElement(element, 'failure', message=str(status)).text = json.dumps(case)
    suite.set('failures', str(failures))
    suite.set('skipped', str(skipped))
    ET.ElementTree(suite).write(junit, encoding='utf-8', xml_declaration=True)
    metadata.update(tests=len(cases), failures=failures, skipped=skipped, junit=str(junit))
except Exception as exc:
    metadata.update(status='NOT_RUN', reason='XCRESULT_PARSE_UNAVAILABLE', error=str(exc))
    (output / 'ios-execution.json').write_text(json.dumps(metadata, indent=2))
    sys.exit(2)
(output / 'ios-execution.json').write_text(json.dumps(metadata, indent=2))
sys.exit(result.returncode or (1 if failures or not cases else 0))
