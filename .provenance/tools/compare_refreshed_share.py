"""Decode supplied shared pages as JSON data and compare source content without JS execution."""
from pathlib import Path
from html.parser import HTMLParser
import collections
import datetime as dt
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD = json.loads((REPO / '.provenance/source/conversation.json').read_text())
LATER_ID = 'e4b8944c-7916-4302-8016-463828ec503e'


class ScriptText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.active = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = True
            self.buf = []

    def handle_data(self, data):
        if self.active:
            self.buf.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.scripts.append(''.join(self.buf))
            self.active = False


def decode(path):
    raw = path.read_bytes()
    parser = ScriptText()
    parser.feed(raw.decode('utf-8'))
    prefix = 'window.__reactRouterContext.streamController.enqueue('
    script = next(s for s in parser.scripts if s.startswith(prefix))
    flat = json.loads(json.loads(script[len(prefix):-2]))
    memo = {}

    def resolve(index):
        if index < 0:
            return None
        if index in memo:
            return memo[index]
        value = flat[index]
        if isinstance(value, dict):
            result = {}
            memo[index] = result
            for key, ref in value.items():
                result[resolve(int(key[1:]))] = resolve(ref)
            return result
        if isinstance(value, list):
            result = []
            memo[index] = result
            if value and isinstance(value[0], str):
                result.append({'stream_tag': value[0]})
                result.extend(resolve(v) if isinstance(v, int) else v for v in value[1:])
            else:
                result.extend(resolve(v) for v in value)
            return result
        memo[index] = value
        return value

    routes = resolve(0)['loaderData']
    route = next(v for k, v in routes.items() if k.startswith('routes/share.'))
    return raw, route['serverResponse']['data']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def iso(timestamp):
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).isoformat()


def file_refs(conversation):
    result = set()
    for node in conversation['linear_conversation']:
        message = node.get('message') or {}
        content = message.get('content') or {}
        text = '\n'.join(s for s in content.get('parts', []) if isinstance(s, str))
        for ref in re.findall(r'\[[^\]]*\]\((sandbox:[^)]*)\)', text):
            result.add((message['id'], ref))
    return result


reports = []
conversations = {}
for label, filename, requested_headers in [
    ('normal', 'shared-chat-updated.html', {}),
    ('no-cache', 'shared-chat-recheck.html', {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}),
]:
    path = ROOT / filename
    raw, new = decode(path)
    conversations[label] = new
    old_ids, new_ids = set(OLD['mapping']), set(new['mapping'])
    changed = sorted(i for i in old_ids & new_ids if OLD['mapping'][i] != new['mapping'][i])
    old_code = {i: n['message']['content'] for i, n in OLD['mapping'].items()
                if (n.get('message') or {}).get('content', {}).get('content_type') == 'code'}
    new_code = {i: n['message']['content'] for i, n in new['mapping'].items()
                if (n.get('message') or {}).get('content', {}).get('content_type') == 'code'}
    old_urls, new_urls = set(OLD['safe_urls']), set(new['safe_urls'])
    current = new['mapping'][new['current_node']]['message']
    refs_old, refs_new = file_refs(OLD), file_refs(new)
    report = {
        'request_kind': label, 'source_url': 'https://chatgpt.com/share/6ad6143e-d894-83e9-a306-302b4fc65c66',
        'http_status': 200, 'requested_headers': requested_headers,
        'captured_at_utc': iso(path.stat().st_mtime), 'raw_file': filename,
        'raw_bytes': len(raw), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'backing_conversation_id': new['backing_conversation_id'],
        'share_metadata_update_time_utc': iso(new['update_time']),
        'previous_share_metadata_update_time_utc': iso(OLD['update_time']),
        'nodes': len(new['mapping']), 'linear_nodes': len(new['linear_conversation']),
        'new_node_ids': sorted(new_ids - old_ids), 'removed_node_ids': sorted(old_ids - new_ids),
        'changed_node_ids': changed, 'mapping_equal': OLD['mapping'] == new['mapping'],
        'linear_conversation_equal': OLD['linear_conversation'] == new['linear_conversation'],
        'mapping_canonical_sha256': digest(new['mapping']),
        'previous_mapping_canonical_sha256': digest(OLD['mapping']),
        'code_message_count': len(new_code), 'code_messages_equal': old_code == new_code,
        'code_canonical_sha256': digest(new_code),
        'current_node': new['current_node'], 'current_node_timestamp_utc': iso(current['create_time']),
        'later_v1_6_message_present': LATER_ID in new['mapping'],
        'literal_version_1_6_0_present': '1.6.0' in json.dumps(new, ensure_ascii=False),
        'safe_url_count': len(new['safe_urls']), 'added_safe_urls': sorted(new_urls-old_urls),
        'removed_safe_urls': sorted(old_urls-new_urls),
        'safe_url_sequence_equal': OLD['safe_urls'] == new['safe_urls'],
        'safe_url_set_equal': old_urls == new_urls,
        'unique_literal_message_attachment_refs': len(refs_new),
        'new_literal_message_attachment_refs': [list(pair) for pair in sorted(refs_new-refs_old)],
        'removed_literal_message_attachment_refs': [list(pair) for pair in sorted(refs_old-refs_new)],
        'changed_conversation_fields': sorted(k for k in OLD.keys() | new.keys() if OLD.get(k) != new.get(k)),
    }
    reports.append(report)
    (ROOT / f'share-conversation-{label}-refreshed.json').write_text(json.dumps(new, ensure_ascii=False, indent=2) + '\n')

headers = []
allowed = {'date', 'age', 'cache-control', 'cf-cache-status', 'etag', 'last-modified', 'content-type', 'x-cache', 'location'}
for line in (ROOT / 'shared-chat-recheck.headers').read_text().splitlines():
    if line.lower().startswith('http/'):
        headers.append({'status_line': line})
    elif ':' in line:
        name, value = line.split(':', 1)
        if name.lower() in allowed:
            headers.append({'name': name.lower(), 'value': value.strip()})
assert all(r['mapping_equal'] and r['linear_conversation_equal'] and r['code_messages_equal'] for r in reports)
assert all(not r['later_v1_6_message_present'] and not r['new_literal_message_attachment_refs'] for r in reports)
summary = {
    'refresh_reason': 'User supplied the same shared URL after updating the share.',
    'original_capture_sha256': hashlib.sha256((REPO / '.provenance/source/shared-chat.html.txt').read_bytes()).hexdigest(),
    'requests': reports, 'filtered_no_cache_response_headers': headers,
    'fresh_message_content_recovered': False, 'new_artifact_revisions_recovered': 0,
    'evidence_conclusion': 'The server metadata records an update at 2026-10-19T14:55:52.628028Z, but both HTTP 200 responses still contain exactly the earlier 615 message nodes and 89 code messages. Safe URLs are the same set of 331 entries; only ordering changed. The v1.6.0 message and new file contents are not exposed in these public responses.',
    'remaining_blocker': 'Current public shared responses omit later message/file content. Original attachment bytes remain unavailable through the public capture. No authenticated-browser attempt or unlock assumption was made during this refresh.',
}
(ROOT / 'refresh-comparison-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
