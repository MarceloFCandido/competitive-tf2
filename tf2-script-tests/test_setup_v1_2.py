#!/usr/bin/env python3
"""Regression tests. All game files, HUDs and downloads are local fixtures."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

HERE = Path(__file__).resolve().parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

new = load('tf2_new', HERE.parent / 'setup_tf2_bazzite.py')
old = load('tf2_old', HERE / 'setup_tf2_bazzite_before_visual_clarity.py')
interim = load('tf2_interim', HERE / 'setup_tf2_bazzite_v1_1.py')


def args(*argv):
    return new.parser().parse_args(list(argv))


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tf2-unit-')
        self.root = Path(self.temp.name)
        self.game = self.root / 'Team Fortress 2'
        self.tf = self.game / 'tf'
        (self.tf / 'cfg').mkdir(parents=True)
        (self.tf / 'custom').mkdir()
        (self.tf / 'gameinfo.txt').write_text('GameInfo {}\n')
        (self.tf / 'cfg/config.cfg').write_text('sensitivity "1.75"\nbind mouse5 +attack2\n')
        (self.tf / 'cfg/soldier.cfg').write_text('echo "my soldier settings"\n')
        (self.tf / 'cfg/autoexec.cfg').write_text('// My old custom config\nbind f +inspect\n')
        self.cfg = self.root / 'initial-staged-cfg'
        old.stage_cfg(self.tf, self.cfg, 'low', '240')
        shutil.rmtree(self.tf / 'cfg')
        shutil.copytree(self.cfg, self.tf / 'cfg')
        (self.tf / 'custom/mastercomfig-base.vpk').write_bytes(struct.pack('<III', 0x55AA1234, 1, 1) + b'\0')
        self.state = self.root / 'state'
        self.state.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def snapshot(self):
        return {p.relative_to(self.tf).as_posix(): p.read_bytes()
                for p in self.tf.rglob('*') if p.is_file()}

    def apply_delta(self, changes):
        for rel, data in changes.items():
            (self.tf / rel).write_bytes(data)

    def zip_hud(self, name='rayshud'):
        path = self.root / (name + '.zip')
        with zipfile.ZipFile(path, 'w') as z:
            for rel, body in {'info.vdf':'hud {}', 'resource/clientscheme.res':'scheme {}',
                              'scripts/hudlayout.res':'layout {}',
                              'cfg/valve.rc':'mat_antialias 8\nexec autoexec.cfg\n'}.items():
                z.writestr(name + '/' + rel, body)
        return path

    def dummy_hud(self, name):
        root = self.tf / 'custom' / name
        (root / 'resource').mkdir(parents=True)
        (root / 'scripts').mkdir()
        (root / 'info.vdf').write_text('hud {}')
        (root / 'scripts/hudlayout.res').write_text('layout {}')
        (root / 'personal.txt').write_text('keep my old HUD customization')
        return root

    def run_main(self, *argv, download=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        deny = lambda *a, **kw: self.fail('Unexpected network download')
        with patch.object(sys, 'argv', ['setup_tf2_bazzite.py', '--tf2-dir', str(self.game), *argv]), \
             patch.object(new.os, 'geteuid', return_value=1000), \
             patch.dict(os.environ, {'XDG_STATE_HOME': str(self.state)}), \
             patch.object(new, 'require_closed'), \
             patch.object(new, 'download', side_effect=download or deny), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = new.main()
        return result, stdout.getvalue(), stderr.getvalue()

    def test_recognizes_original_version(self):
        self.assertTrue(new.recognized_install(self.tf))

    def test_no_options_are_a_noop(self):
        self.assertEqual(new.plan_update(self.tf, args()), {})

    def test_hud_only_does_not_edit_config(self):
        self.assertEqual(new.plan_update(self.tf, args('--hud', 'rayshud')), {})

    def test_visual_delta_preserves_preset_fps_and_all_other_files(self):
        before = self.snapshot()
        changes = new.plan_update(self.tf, args('--visual-clarity'))
        self.assertEqual(set(changes), {'cfg/overrides/modules.cfg'})
        self.apply_delta(changes)
        after = self.snapshot()
        self.assertEqual([k for k in before if before[k] != after[k]], ['cfg/overrides/modules.cfg'])
        self.assertIn(b'fpscap=240\n', after['cfg/overrides/modules.cfg'])
        self.assertIn(b'preset=low\n', after['cfg/overrides/setup_hook.cfg'])
        for line in before['cfg/overrides/modules.cfg'].splitlines():
            self.assertIn(line, after['cfg/overrides/modules.cfg'].splitlines())

    def test_preserves_stricter_effects(self):
        rel = self.tf / 'cfg/overrides/modules.cfg'
        rel.write_text(rel.read_text().replace(new.END, 'effects=very_low\n' + new.END))
        self.apply_delta(new.plan_update(self.tf, args('--visual-clarity')))
        self.assertIn('effects=very_low\n', rel.read_text())
        self.assertNotIn('effects=medium', rel.read_text())

    def test_viewmodel_only_leaves_everything_else(self):
        before = (self.tf / new.MANAGED_FILES[1]).read_bytes()
        changes = new.plan_update(self.tf, args('--viewmodels', 'hidden'))
        self.assertEqual(set(changes), {new.MANAGED_FILES[1]})
        self.assertEqual(changes[new.MANAGED_FILES[1]], before.replace(b'r_drawviewmodel 1', b'r_drawviewmodel 0'))

    def test_viewmodels_remain_hidden_when_option_omitted(self):
        self.apply_delta(new.plan_update(self.tf, args('--viewmodels', 'hidden')))
        self.apply_delta(new.plan_update(self.tf, args('--visual-clarity')))
        self.assertIn('r_drawviewmodel 0', (self.tf / new.MANAGED_FILES[1]).read_text())

    def test_can_restore_visible_viewmodels_without_other_resets(self):
        self.apply_delta(new.plan_update(self.tf, args('--viewmodels', 'hidden')))
        self.apply_delta(new.plan_update(self.tf, args('--viewmodels', 'minimal')))
        self.assertIn('r_drawviewmodel 1', (self.tf / new.MANAGED_FILES[1]).read_text())
        self.assertIn('fpscap=240', (self.tf / new.MANAGED_FILES[2]).read_text())

    def test_incremental_updates_are_idempotent(self):
        request = args('--visual-clarity', '--viewmodels', 'hidden')
        self.apply_delta(new.plan_update(self.tf, request))
        self.assertEqual(new.plan_update(self.tf, request), {})
        text = (self.tf / new.MANAGED_FILES[2]).read_text()
        for key, value, _ in new.CLARITY_MODULES:
            self.assertEqual(text.count(key + '=' + value), 1)

    def test_explicit_fps_change_does_not_change_preset(self):
        changes = new.plan_update(self.tf, args('--fps-cap', '360'))
        self.assertEqual(set(changes), {new.MANAGED_FILES[2]})
        self.assertIn(b'fpscap=360', changes[new.MANAGED_FILES[2]])
        self.assertNotIn(b'fpscap=300', changes[new.MANAGED_FILES[2]])

    def test_explicit_preset_change_does_not_change_fps(self):
        changes = new.plan_update(self.tf, args('--preset', 'high'))
        self.assertEqual(set(changes), {new.MANAGED_FILES[0]})
        self.assertIn(b'preset=high', changes[new.MANAGED_FILES[0]])

    def test_interim_version_supported_without_resetting_effects(self):
        staged = self.root / 'v11'
        interim.stage_cfg(self.tf, staged, 'high', '360', True, 'hidden')
        shutil.rmtree(self.tf / 'cfg')
        shutil.copytree(staged, self.tf / 'cfg')
        self.assertTrue(new.recognized_install(self.tf))
        self.assertEqual(new.plan_update(self.tf, args('--visual-clarity')), {})
        self.assertIn('effects=medium', (self.tf / new.MANAGED_FILES[2]).read_text())

    def test_duplicate_target_is_rejected(self):
        path = self.tf / new.MANAGED_FILES[1]
        path.write_text(path.read_text() + '\nr_drawviewmodel 0\n')
        before = self.snapshot()
        with self.assertRaisesRegex(new.SetupError, 'multiple active definitions'):
            new.plan_update(self.tf, args('--viewmodels', 'hidden'))
        self.assertEqual(self.snapshot(), before)

    def test_target_in_alias_is_rejected(self):
        path = self.tf / new.MANAGED_FILES[1]
        path.write_text(path.read_text() + '\nalias hide "r_drawviewmodel 0"\n')
        with self.assertRaisesRegex(new.SetupError, 'scripted or ambiguous'):
            new.plan_update(self.tf, args('--viewmodels', 'hidden'))

    def test_comments_and_urls_are_not_executed(self):
        self.assertEqual(new.active_line('echo "https://example.com/a" // comment'), 'echo "https://example.com/a" ')
        text = new.BEGIN + '\n// r_drawviewmodel 1\nr_drawviewmodel 1 // keep this comment\n' + new.END + '\n'
        updated = new.patch_scalar(text, 'r_drawviewmodel', '0', ' ', 'test')
        self.assertIn('// r_drawviewmodel 1\n', updated)
        self.assertIn('r_drawviewmodel 0 // keep this comment', updated)

    def test_crlf_preserved(self):
        path = self.tf / new.MANAGED_FILES[2]
        path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
        data = new.plan_update(self.tf, args('--visual-clarity'))[new.MANAGED_FILES[2]]
        self.assertNotIn(b'\n', data.replace(b'\r\n', b''))

    def test_malformed_markers_refused(self):
        path = self.tf / new.MANAGED_FILES[2]
        path.write_text(path.read_text().replace(new.END, ''))
        with self.assertRaises(new.SetupError):
            new.recognized_install(self.tf)

    def test_partial_installation_refused(self):
        (self.tf / new.MANAGED_FILES[0]).unlink()
        with self.assertRaises(new.SetupError):
            new.recognized_install(self.tf)

    def test_symlink_is_not_followed(self):
        path = self.tf / new.MANAGED_FILES[2]
        external = self.root / 'external'
        path.rename(external)
        path.symlink_to(external)
        with self.assertRaises(new.SetupError):
            new.recognized_install(self.tf)

    def test_new_hud_plan(self):
        self.assertEqual(new.plan_hud(self.tf, 'rayshud', False), (True, []))

    def test_replacement_requires_authorization(self):
        self.dummy_hud('budhud')
        with self.assertRaisesRegex(new.SetupError, '--replace-hud'):
            new.plan_hud(self.tf, 'rayshud', False)
        self.assertEqual(new.plan_hud(self.tf, 'rayshud', True), (True, ['custom/budhud']))

    def test_replacement_flag_requires_hud(self):
        with self.assertRaises(new.SetupError):
            new.plan_hud(self.tf, 'keep', True)

    def test_prepare_excludes_startup_and_skips_identical_hud(self):
        staged = new.prepare_hud(self.zip_hud(), self.root / 'unpacked', 'rayshud')
        self.assertFalse((staged / 'cfg/valve.rc').exists())
        shutil.copytree(staged, self.tf / 'custom/rayshud')
        self.assertEqual(new.plan_hud(self.tf, 'rayshud', False), (False, []))

    def test_modified_hud_requires_replacement(self):
        staged = new.prepare_hud(self.zip_hud(), self.root / 'unpacked', 'rayshud')
        selected = self.tf / 'custom/rayshud'
        shutil.copytree(staged, selected)
        (selected / 'resource/clientscheme.res').write_text('my custom color')
        with self.assertRaises(new.SetupError):
            new.plan_hud(self.tf, 'rayshud', False)
        self.assertEqual(new.plan_hud(self.tf, 'rayshud', True), (True, []))

    def test_zip_path_traversal_rejected(self):
        z = self.root / 'bad.zip'
        with zipfile.ZipFile(z, 'w') as out:
            out.writestr('../outside', 'bad')
        with self.assertRaises(new.SetupError):
            new.extract_hud(z, self.root / 'unpacked')
        self.assertFalse((self.root / 'outside').exists())

    def test_hud_surprise_autoexec_rejected(self):
        z = self.zip_hud()
        with zipfile.ZipFile(z, 'a') as out:
            out.writestr('rayshud/cfg/autoexec.cfg', 'fps_max 10')
        with self.assertRaises(new.SetupError):
            new.prepare_hud(z, self.root / 'unpacked', 'rayshud')

    def test_dry_run_no_writes_or_downloads(self):
        before = self.snapshot()
        root_before = sorted(str(p) for p in self.root.rglob('*'))
        # temp file creation during the preview is also prohibited.
        with patch.object(new.tempfile, 'TemporaryDirectory', side_effect=AssertionError('Temporary write during dry run')):
            result, output, _ = self.run_main('--update-only', '--dry-run', '--visual-clarity', '--hud', 'rayshud')
        self.assertEqual(result, 0)
        self.assertIn('(current)', output)
        self.assertIn('FPS cap: keep', output)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(sorted(str(p) for p in self.root.rglob('*')), root_before)

    def test_automatic_update_with_no_options_is_noop(self):
        before = sorted(str(p) for p in self.root.rglob('*'))
        result, output, _ = self.run_main('--yes')
        self.assertEqual(result, 0)
        self.assertIn('Already configured', output)
        self.assertEqual(sorted(str(p) for p in self.root.rglob('*')), before)

    def test_full_update_and_undo_do_not_reinstall_base(self):
        self.dummy_hud('budhud')
        before = self.snapshot()
        zip_path = self.zip_hud()
        downloads = []
        def mock_download(asset, path, maximum):
            downloads.append(asset)
            self.assertIs(asset, new.RAYSHUD)
            shutil.copy2(zip_path, path)
        result, output, _ = self.run_main('--update-only', '--visual-clarity', '--viewmodels', 'hidden',
                                          '--hud', 'rayshud', '--replace-hud', '--yes', download=mock_download)
        self.assertEqual(result, 0)
        self.assertEqual(len(downloads), 1)
        self.assertFalse((self.tf / 'custom/budhud').exists())
        self.assertTrue((self.tf / 'custom/rayshud').is_dir())
        self.assertEqual((self.tf / 'custom/mastercomfig-base.vpk').read_bytes(), before['custom/mastercomfig-base.vpk'])
        manifests = list(self.state.rglob('manifest.json'))
        self.assertEqual(len(manifests), 1)
        m = json.loads(manifests[0].read_text())
        self.assertNotIn('cfg', [entry['path'] for entry in m['entries']])
        self.assertNotIn('custom/mastercomfig-base.vpk', [entry['path'] for entry in m['entries']])
        tf, ops = new.load_restore(manifests[0].parent)
        with contextlib.redirect_stdout(io.StringIO()):
            new.transact(tf, ops, self.state, 'test-restore')
        self.assertEqual(self.snapshot(), before)

    def test_second_hud_install_is_noop_and_download_free(self):
        zip_path = self.zip_hud()
        def mock_download(asset, path, maximum):
            shutil.copy2(zip_path, path)
        self.run_main('--hud', 'rayshud', '--yes', download=mock_download)
        before = self.snapshot()
        count = len(list(self.state.rglob('manifest.json')))
        _, output, _ = self.run_main('--hud', 'rayshud', '--yes')
        self.assertIn('Already configured', output)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(list(self.state.rglob('manifest.json'))), count)

    def test_old_backup_still_restores(self):
        before = self.snapshot()
        staged = self.root / 'old-reinstall'
        old.stage_cfg(self.tf, staged, 'high', '400')
        with contextlib.redirect_stdout(io.StringIO()):
            saved = old.transact(self.tf, {'cfg': staged}, self.state, 'old-install')
            tf, operations = new.load_restore(saved)
            new.transact(tf, operations, self.state, 'new-restores-old')
        self.assertEqual(self.snapshot(), before)

    def test_rollback_after_copy_failure(self):
        before = self.snapshot()
        changes = new.plan_update(self.tf, args('--visual-clarity', '--viewmodels', 'hidden'))
        ops = {}
        for rel, data in changes.items():
            path = self.root / 'staged' / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            ops[rel] = path
        real_copy = new.copy_item
        failed = False
        def copy_fails_once(src, dst):
            nonlocal failed
            if 'staged' in src.parts and not failed:
                failed = True
                raise OSError('synthetic install failure')
            return real_copy(src, dst)
        with patch.object(new, 'copy_item', side_effect=copy_fails_once), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(OSError):
                new.transact(self.tf, ops, self.state, 'rollback-test')
        self.assertEqual(self.snapshot(), before)

    def test_unknown_installation_rejected_in_update_only(self):
        shutil.rmtree(self.tf / 'cfg/overrides')
        before = self.snapshot()
        with self.assertRaisesRegex(new.SetupError, '--update-only did not find'):
            self.run_main('--update-only', '--dry-run', '--hud', 'rayshud')
        self.assertEqual(self.snapshot(), before)

    def test_warning_about_other_class_script(self):
        path = self.tf / 'cfg/overrides/soldier.cfg'
        path.write_text('r_drawviewmodel 1\n')
        before = path.read_bytes()
        result, output, error = self.run_main('--dry-run', '--viewmodels', 'hidden')
        self.assertEqual(result, 0)
        self.assertIn('soldier.cfg:1', error)
        self.assertEqual(path.read_bytes(), before)

    def test_checksum_verification_rejects_bad_content(self):
        class Response(io.BytesIO):
            def geturl(self): return 'https://example.org/hud.zip'
        with patch.object(new.urllib.request, 'urlopen', return_value=Response(b'bad')), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(new.SetupError, 'SHA-256 mismatch'):
                new.download(new.RAYSHUD, self.root / 'download', 1000)

    def test_checksum_verification_accepts_expected_content(self):
        class Response(io.BytesIO):
            def geturl(self): return 'https://example.org/hud.zip'
        asset = {'url': 'https://example.org/hud.zip', 'version': 'test', 'sha256': hashlib.sha256(b'good').hexdigest()}
        with patch.object(new.urllib.request, 'urlopen', return_value=Response(b'good')), \
             contextlib.redirect_stdout(io.StringIO()):
            new.download(asset, self.root / 'download', 1000)
        self.assertEqual((self.root / 'download').read_bytes(), b'good')


if __name__ == '__main__':
    unittest.main(verbosity=2)
