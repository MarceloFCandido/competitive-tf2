"""Receive or decode verified transfer data; never execute recovered files."""
import base64
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

PENDING = Path(__file__).resolve().with_name('pending-user-upload-turn-2.json')
EXPECTED = {
    'setup_tf2_bazzite(2).py': 'ce6883d6b426a157ea6a5ace9e8857e914618d133817343daf5545da769ab8db',
    'test_setup_tf2_bazzite(2).py': 'c20f3436dd4d1f1d7610277c4dbe57495d6e4e6bf2062ec7c10bdcbf693b63c2',
    'TF2_HUD_Update_README(6).md': 'f638856ff114a7253afad964726d87be20558074a81366b2acab244142634f2a',
    'TF2_HUD_Visual_Comparison(1).html': '789a50f33928747f428955464f953f0bab6353c93dec11933083be0f62975b5f',
}


def main():
    record = json.loads(PENDING.read_text())
    folder = Path(record['incoming_directory'])
    parts = folder / 'transfer-parts'
    parts.mkdir(exist_ok=True)
    manifest_path = parts / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'total_parts': 12, 'parts': {}}
    assert manifest['total_parts'] == 12
    record['expected_hashes'] = EXPECTED
    record['total_parts'] = 12
    if sys.argv[1] == 'decode':
        assert sorted(map(int, manifest['parts'])) == list(range(1, 13))
        blocks = []
        for index in range(1, 13):
            part = manifest['parts'][str(index)]
            data = (parts / f'part-{index:02d}.b64').read_bytes()
            assert hashlib.sha256(data).hexdigest() == part['sha256']
            assert len(data) == part['bytes']
            blocks.append(data)
        packed = base64.b64decode(b''.join(blocks), validate=True)
        payload = json.loads(gzip.decompress(packed))
        assert isinstance(payload, dict) and set(payload) == set(EXPECTED)
        verified = []
        decoded = {}
        for name, expected in EXPECTED.items():
            raw = base64.b64decode(payload[name], validate=True)
            actual = hashlib.sha256(raw).hexdigest()
            assert actual == expected, (name, actual, expected)
            decoded[name] = raw
            verified.append({'upload_name': name, 'bytes': len(raw), 'sha256': actual})
        output = folder / 'decoded-originals'
        output.mkdir(exist_ok=True)
        for name, raw in decoded.items():
            destination = output / name
            if destination.exists():
                assert destination.read_bytes() == raw
            else:
                with destination.open('xb') as stream:
                    stream.write(raw)
        result = {'total_parts': 12, 'verified_files': verified, 'packed_sha256': hashlib.sha256(packed).hexdigest(), 'decoded_as_data_only': True, 'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        (folder / 'transfer-verified.json').write_text(json.dumps(result, indent=2) + '\n')
        record.update(status='all_original_bytes_verified_pending_static_inspection', files_received=4, files=verified)
    else:
        index = int(sys.argv[1])
        expected = sys.argv[2]
        assert 1 <= index <= 12 and re.fullmatch('[0-9a-f]{64}', expected)
        data = sys.stdin.read().strip().encode('ascii')
        assert re.fullmatch(rb'[A-Za-z0-9+/=]+', data)
        actual = hashlib.sha256(data).hexdigest()
        assert actual == expected, (index, len(data), actual, expected)
        destination = parts / f'part-{index:02d}.b64'
        if destination.exists():
            assert destination.read_bytes() == data
        else:
            with destination.open('xb') as stream:
                stream.write(data)
        manifest['parts'][str(index)] = {'filename': destination.name, 'bytes': len(data), 'sha256': actual, 'verified': True, 'received_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        record.update(status='receiving_verified_transfer_parts', verified_parts=sorted(map(int, manifest['parts'])))
        result = {'part': index, 'of': 12, 'bytes': len(data), 'sha256': actual, 'verified': True, 'decoded': False, 'verified_parts': record['verified_parts']}
    PENDING.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
