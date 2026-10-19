#!/usr/bin/env python3
"""Offline regression tests for setup_tf2_bazzite.py v1.3.1.

Uses artificial TF2 folders and small artificial HUD archives. No real TF2,
Steam, network, fonts, or downloaded HUD assets are needed or exercised.
Run: python3 -m unittest -v test_setup_tf2_bazzite.py
Place this test file beside setup_tf2_bazzite.py, or set TF2_SETUP_SCRIPT.
"""
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

SCRIPT = Path(os.environ.get('TF2_SETUP_SCRIPT', str(Path(__file__).with_name('setup_tf2_bazzite.py'))))
spec = importlib.util.spec_from_file_location('tf2_setup_tested', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text if isinstance(text, bytes) else text.encode())


def vpk_bytes():
    return struct.pack('<III', 0x55AA1234, 1, 1) + b'\0'


def archive_bytes(name='idhud', extra=None, folder=None):
    folder = folder or name
    files = {'info.vdf': '"HUD" { "ui_version" "3" }',
             'resource/clientscheme.res': '"Scheme" {}',
             'scripts/hudlayout.res': '"Resource/HudLayout.res" {}'}
    if name != 'idhud':
        files['cfg/valve.rc'] = 'exec autoexec.cfg\nmat_antialias 4\n'
    if extra:
        files.update(extra)
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel, contents in files.items():
            z.writestr(folder + '/' + rel, contents)
    return out.getvalue()


class Response(io.BytesIO):
    def geturl(self):
        return 'https://github.com/example/release.zip'


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tf2-regression-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'Steam library/steamapps/common/Team Fortress 2'
        self.tf = self.game / 'tf'
        write(self.tf / 'gameinfo.txt', '"GameInfo" {}')
        write(self.tf / 'custom/mastercomfig-base.vpk', vpk_bytes())
        for rel, body in zip(m.MANAGED_FILES, ('preset=low', m.personal_config('hidden'),
                                               m.module_config('240', True))):
            path = self.tf / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            m.managed_file(path, body)
        # Extra user changes: these must survive a HUD-only update byte-for-byte.
        with (self.tf / m.MANAGED_FILES[1]).open('a') as f:
            f.write('\nsensitivity 1.13\nbind "mouse4" "+attack2"\ncl_crosshair_scale 27\n')
        with (self.tf / m.MANAGED_FILES[2]).open('a') as f:
            f.write('\neffects=very_low\n// local comment\n')
        write(self.tf / 'cfg/overrides/scout.cfg', 'viewmodel_fov 85\n')
        write(self.tf / 'cfg/config.cfg', 'volume 0.65\n')
        write(self.tf / 'custom/othermod/sound/myhit.wav', b'not a real sound')
        self.state = self.root / 'state'
        self.downloads = []

    def args(self, *args):
        return m.parser().parse_args(list(args))

    def snapshot(self, root=None):
        root = root or self.root
        return {str(p.relative_to(root)): ('dir' if p.is_dir() else p.read_bytes())
                for p in sorted(root.rglob('*')) if not p.is_symlink()}

    def install_hud_fixture(self, name='rayshud', customized=False):
        src = self.root / (name + '-fixture.zip')
        write(src, archive_bytes(name))
        prepared = m.prepare_hud(src, self.root / (name + '-staging'), name)
        dest = self.tf / 'custom' / name
        shutil.copytree(prepared, dest)
        if customized:
            write(dest / 'resource/local_changes.res', '"PlayerChoice" "keep me"')
        return dest

    def fake_download(self, asset, dest, maximum):
        self.downloads.append(asset['url'])
        if asset is m.COMFIG:
            write(dest, vpk_bytes())
        else:
            name = next(name for name, a in m.HUDS.items() if a is asset)
            write(dest, archive_bytes(name))

    def run_main(self, *args, downloader=None, confirmer=True):
        location = [] if '--restore' in args else ['--tf2-dir', str(self.game)]
        argv = [str(SCRIPT), *location, *args]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', argv), patch.object(m.os, 'geteuid', return_value=1000), \
             patch.dict(os.environ, {'XDG_STATE_HOME': str(self.state)}), \
             patch.object(m, 'require_closed') as closed, \
             patch.object(m, 'confirm', return_value=confirmer) as confirm, \
             patch.object(m, 'download', side_effect=downloader or self.fake_download) as download, \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = m.main()
        return result, stdout.getvalue(), stderr.getvalue(), download, confirm, closed

    def test_middlemann_dry_run_preserves_everything(self):
        self.install_hud_fixture('rayshud', customized=True)
        write(self.tf / 'cfg/config.cfg', 'cl_hud_minmode 1\nvolume 0.65\n')
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'middlemann', '--replace-hud', '--dry-run')
        self.assertEqual(result[0], 0)
        self.assertIn('Configuration files: no changes.', result[1])
        self.assertIn('Middle Mann expects cl_hud_minmode 0', result[1])
        self.assertIn('v26.1', result[1])
        self.assertFalse(result[3].called)
        self.assertFalse(result[4].called)
        self.assertEqual(before, self.snapshot())

    def test_middlemann_switch_and_exact_restore(self):
        self.install_hud_fixture('rayshud', customized=True)
        before = self.snapshot(self.tf)
        cfg_before = self.snapshot(self.tf / 'cfg')
        result = self.run_main('--update-only', '--hud', 'middlemann', '--replace-hud')
        self.assertEqual(result[0], 0)
        self.assertEqual(cfg_before, self.snapshot(self.tf / 'cfg'))
        self.assertFalse((self.tf / 'custom/rayshud').exists())
        self.assertTrue(m.hud_is_current(self.tf / 'custom/middlemann', 'middlemann'))
        self.assertFalse((self.tf / 'custom/middlemann/cfg/valve.rc').exists())
        self.assertEqual(self.downloads, [m.MIDDLEMANN['url']])
        backup = next(self.state.rglob('manifest.json')).parent
        self.run_main('--restore', str(backup))
        self.assertEqual(before, self.snapshot(self.tf))

    def test_middlemann_reapply_is_noop(self):
        self.install_hud_fixture('middlemann')
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'middlemann', '--replace-hud')
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_middlemann_realistic_root_and_startup_exclusion(self):
        archive = self.root / 'middlemann-test.zip'
        write(archive, archive_bytes('middlemann',
                                    folder='-middle-mann-v26.1',
                                    extra={'customizations/vignette.res': '// off\n',
                                           'cfg/valve.rc': 'cl_hud_minmode 0\nvgui_cache_res_files 0\nwait 200; hud_reloadscheme\n'}))
        root = m.prepare_hud(archive, self.root / 'middlemann-stage', 'middlemann')
        self.assertEqual(root.name, '-middle-mann-v26.1')
        self.assertFalse((root / 'cfg').exists())
        self.assertEqual((root / 'customizations/vignette.res').read_text(), '// off\n')
        self.assertTrue(m.hud_is_current(root, 'middlemann'))

    def test_middlemann_unexpected_startup_refused(self):
        archive = self.root / 'middlemann-test.zip'
        write(archive, archive_bytes('middlemann', extra={'cfg/joystick.cfg': 'exec bad.cfg'}))
        with self.assertRaisesRegex(m.SetupError, 'Unexpected Middle Mann cfg'):
            m.prepare_hud(archive, self.root / 'middlemann-stage', 'middlemann')

    def test_catalog_choices_include_previous_and_new(self):
        self.assertEqual(set(m.HUD_CHOICES), {'keep', 'stock', 'idhud', 'rayshud', 'budhud', 'middlemann'})
        self.assertEqual(self.args().hud, 'keep')
        self.assertEqual(self.args('--hud', 'idhud').hud, 'idhud')

    def test_catalog_no_game_no_network_no_writes(self):
        before = self.snapshot()
        with patch.object(sys, 'argv', [str(SCRIPT), '--list-huds']), \
             patch.object(m, 'discover_games', side_effect=AssertionError('must not discover')), \
             patch.object(m, 'download', side_effect=AssertionError('must not download')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(m.main(), 0)
        for name in m.HUD_CHOICES:
            self.assertIn(name, out.getvalue())
        self.assertEqual(before, self.snapshot())

    def test_release_pins_unchanged_for_existing_installs(self):
        self.assertEqual(m.COMFIG['version'], '9.100.1')
        self.assertEqual(m.COMFIG['sha256'], 'cdabc8251864a1ab2ef7f7ffed1b44f52810956e476d62183b8d7e3e960d8650')
        self.assertEqual(m.RAYSHUD['version'], '2026.0111')
        self.assertEqual(m.RAYSHUD['sha256'], '09c695faa1243d649dff5636d1ccb0c831a6f4f6d118380b2e40d451f6dbd014')
        self.assertEqual(m.BUDHUD['version'], '2511_01')
        self.assertEqual(m.HUD_POLICY, 'preserve-startup-v1')
        self.assertEqual(m.IDHUD['version'], '4.0.8')
        for a in m.HUDS.values():
            self.assertEqual(len(a['sha256']), 64)
            self.assertIn('/releases/download/' + a['version'] + '/', a['url'])
            self.assertTrue(a['url'].startswith('https://github.com/'))

    def test_legacy_managed_install_recognized(self):
        self.assertTrue(m.recognized_install(self.tf))

    def test_hud_only_plan_changes_no_configs(self):
        before = self.snapshot(self.tf)
        self.assertEqual(m.plan_update(self.tf, self.args('--hud', 'idhud', '--replace-hud')), {})
        self.assertEqual(before, self.snapshot(self.tf))

    def test_clarity_keeps_stricter_effects_and_is_idempotent(self):
        self.assertEqual(m.plan_update(self.tf, self.args('--visual-clarity')), {})
        self.assertIn('effects=very_low', (self.tf / m.MANAGED_FILES[2]).read_text())

    def test_viewmodels_changes_only_requested_commands(self):
        result = m.plan_update(self.tf, self.args('--viewmodels', 'minimal'))
        self.assertEqual(set(result), {m.MANAGED_FILES[1]})
        old = (self.tf / m.MANAGED_FILES[1]).read_bytes()
        self.assertEqual(result[m.MANAGED_FILES[1]], old.replace(b'r_drawviewmodel 0', b'r_drawviewmodel 1'))

    def test_explicit_fps_and_preset_still_work(self):
        result = m.plan_update(self.tf, self.args('--preset', 'high', '--fps-cap', '360'))
        self.assertEqual(set(result), {m.MANAGED_FILES[0], m.MANAGED_FILES[2]})
        self.assertIn(b'preset=high', result[m.MANAGED_FILES[0]])
        self.assertIn(b'fpscap=360', result[m.MANAGED_FILES[2]])
        self.assertIn(b'effects=very_low', result[m.MANAGED_FILES[2]])

    def test_duplicate_targeted_setting_rejected(self):
        with (self.tf / m.MANAGED_FILES[1]).open('a') as f:
            f.write('r_drawviewmodel 1\n')
        with self.assertRaises(m.SetupError):
            m.plan_update(self.tf, self.args('--viewmodels', 'minimal'))

    def test_ambiguous_targeted_script_rejected(self):
        with (self.tf / m.MANAGED_FILES[1]).open('a') as f:
            f.write('alias vm "r_drawviewmodel 1"\n')
        with self.assertRaises(m.SetupError):
            m.plan_update(self.tf, self.args('--viewmodels', 'minimal'))

    def test_keep_does_not_touch_current_hud(self):
        self.install_hud_fixture(customized=True)
        self.assertEqual(m.plan_hud(self.tf, 'keep', False), (False, []))
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'keep', True)

    def test_switch_needs_replacement_permission(self):
        self.install_hud_fixture()
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'idhud', False)
        self.assertEqual(m.plan_hud(self.tf, 'idhud', True), (True, ['custom/rayshud']))

    def test_stock_removal_permission(self):
        self.install_hud_fixture()
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'stock', False)
        self.assertEqual(m.plan_hud(self.tf, 'stock', True), (False, ['custom/rayshud']))

    def test_stock_without_custom_hud_is_noop(self):
        self.assertEqual(m.plan_hud(self.tf, 'stock', False), (False, []))
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'stock')
        self.assertEqual(result[0], 0)
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertFalse(result[4].called)
        self.assertEqual(before, self.snapshot())

    def test_existing_rayshud_marker_still_noop(self):
        self.install_hud_fixture('rayshud')
        self.assertEqual(m.plan_hud(self.tf, 'rayshud', False), (False, []))

    def test_customized_current_hud_not_overwritten_silently(self):
        self.install_hud_fixture('idhud', customized=True)
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'idhud', False)
        self.assertEqual(m.plan_hud(self.tf, 'idhud', True), (True, []))

    def test_named_unrecognized_destination_conflicts(self):
        write(self.tf / 'custom/idhud/private.txt', 'unrelated local directory')
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'idhud', False)

    def test_all_detected_huds_replaced_not_layered(self):
        self.install_hud_fixture('rayshud')
        self.install_hud_fixture('budhud')
        self.assertEqual(m.plan_hud(self.tf, 'idhud', True),
                         (True, ['custom/budhud', 'custom/rayshud']))

    def test_vpk_hud_detected_and_nonhud_mod_kept(self):
        write(self.tf / 'custom/oldhud.vpk', vpk_bytes())
        write(self.tf / 'custom/soundpack.vpk', vpk_bytes())
        self.assertEqual(m.plan_hud(self.tf, 'stock', True), (False, ['custom/oldhud.vpk']))

    def test_symlink_hud_rejected(self):
        outside = self.root / 'outside-hud'
        write(outside / 'scripts/hudlayout.res', '{}')
        (self.tf / 'custom/linkedhud').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'idhud', True)

    def test_invalid_selection_rejected(self):
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, '../escape', True)

    def test_hud_switch_dry_run_does_nothing(self):
        self.install_hud_fixture(customized=True)
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', '--dry-run')
        self.assertEqual(result[0], 0)
        self.assertIn('Configuration files: no changes.', result[1])
        self.assertIn('custom/rayshud', result[1])
        self.assertIn('IDHUD', result[1])
        self.assertIn('4.0.8', result[1])
        self.assertFalse(result[3].called)
        self.assertFalse(result[4].called)
        self.assertFalse(result[5].called)
        self.assertEqual(before, self.snapshot())

    def test_stock_dry_run_does_nothing(self):
        self.install_hud_fixture()
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'stock', '--replace-hud', '--dry-run')
        self.assertIn('built-in stock HUD', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_apply_switch_preserves_everything_but_hud(self):
        oldhud = self.install_hud_fixture(customized=True)
        cfg_before = self.snapshot(self.tf / 'cfg')
        base_before = (self.tf / 'custom/mastercomfig-base.vpk').read_bytes()
        oldhash = m.tree_hash(oldhud)
        result = self.run_main('--update-only', '--hud', 'idhud', '--replace-hud')
        self.assertEqual(result[0], 0)
        self.assertFalse(oldhud.exists())
        self.assertTrue(m.hud_is_current(self.tf / 'custom/idhud', 'idhud'))
        self.assertEqual(cfg_before, self.snapshot(self.tf / 'cfg'))
        self.assertEqual(base_before, (self.tf / 'custom/mastercomfig-base.vpk').read_bytes())
        self.assertTrue((self.tf / 'custom/othermod/sound/myhit.wav').exists())
        self.assertEqual(self.downloads, [m.IDHUD['url']])
        manifest_path = next(self.state.rglob('manifest.json'))
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual({e['path'] for e in manifest['entries']}, {'custom/rayshud', 'custom/idhud'})
        self.assertEqual(m.tree_hash(manifest_path.parent / 'originals/custom/rayshud'), oldhash)
        self.assertIn('--restore', result[1])
        self.assertNotIn(self.tf, manifest_path.parents)

    def test_reapplying_idhud_is_noop(self):
        self.install_hud_fixture('idhud')
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'idhud', '--replace-hud')
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_declining_switch_changes_nothing(self):
        self.install_hud_fixture()
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', confirmer=False)
        self.assertIn('Cancelled', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_stock_apply_preserves_config_and_makes_restorable_backup(self):
        self.install_hud_fixture('rayshud', customized=True)
        before_cfg = self.snapshot(self.tf / 'cfg')
        self.run_main('--update-only', '--hud', 'stock', '--replace-hud')
        self.assertEqual(m.hud_candidates(self.tf), [])
        self.assertEqual(self.downloads, [])
        self.assertEqual(before_cfg, self.snapshot(self.tf / 'cfg'))
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        self.assertEqual(set(ops), {'custom/rayshud'})
        m.transact(tf, ops, backup.parent, 'test-restore')
        self.assertTrue((self.tf / 'custom/rayshud/resource/local_changes.res').is_file())

    def test_restore_undoes_only_latest_switch(self):
        self.install_hud_fixture(customized=True)
        before = self.snapshot(self.tf)
        self.run_main('--update-only', '--hud', 'idhud', '--replace-hud')
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        self.assertEqual(set(ops), {'custom/rayshud', 'custom/idhud'})
        m.transact(tf, ops, backup.parent, 'test-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_updates_require_earlier_baseline(self):
        for rel in m.MANAGED_FILES:
            (self.tf / rel).unlink()
        before = self.snapshot()
        with self.assertRaises(m.SetupError):
            self.run_main('--update-only', '--hud', 'idhud', '--replace-hud')
        self.assertEqual(before, self.snapshot())

    def test_missing_base_refuses_update(self):
        (self.tf / 'custom/mastercomfig-base.vpk').unlink()
        with self.assertRaises(m.SetupError):
            m.recognized_install(self.tf)

    def test_bad_download_does_not_change_game(self):
        self.install_hud_fixture()
        before = self.snapshot(self.tf)
        def fail(*args):
            raise m.SetupError('SHA-256 mismatch')
        with self.assertRaisesRegex(m.SetupError, 'SHA-256'):
            self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', downloader=fail)
        self.assertEqual(before, self.snapshot(self.tf))
        self.assertFalse(list(self.state.rglob('manifest.json')))

    def test_stale_config_during_download_refused(self):
        self.install_hud_fixture()
        def race(asset, dest, maximum):
            self.fake_download(asset, dest, maximum)
            with (self.tf / m.MANAGED_FILES[2]).open('a') as f:
                f.write('// another editor\n')
        with self.assertRaisesRegex(m.SetupError, 'changed after the preview'):
            self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', downloader=race)
        self.assertTrue((self.tf / 'custom/rayshud').exists())
        self.assertFalse((self.tf / 'custom/idhud').exists())

    def test_new_hud_during_download_refused(self):
        self.install_hud_fixture()
        def race(asset, dest, maximum):
            self.fake_download(asset, dest, maximum)
            write(self.tf / 'custom/surprisehud/scripts/hudlayout.res', '{}')
        with self.assertRaisesRegex(m.SetupError, 'HUDs changed after the preview'):
            self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', downloader=race)
        self.assertTrue((self.tf / 'custom/rayshud').exists())
        self.assertFalse((self.tf / 'custom/idhud').exists())

    def test_idhud_no_startup_scripts(self):
        path = self.install_hud_fixture('idhud')
        self.assertFalse((path / 'cfg').exists())
        self.assertTrue(m.hud_is_current(path, 'idhud'))

    def test_idhud_unexpected_startup_folder_rejected(self):
        src = self.root / 'bad.zip'
        write(src, archive_bytes('idhud', {'cfg/valve.rc': 'exec anything.cfg'}))
        with self.assertRaisesRegex(m.SetupError, 'Unexpected cfg'):
            m.prepare_hud(src, self.root / 'bad-extract', 'idhud')

    def test_old_hud_startup_is_excluded(self):
        for name in ('budhud', 'rayshud'):
            path = self.install_hud_fixture(name)
            self.assertFalse((path / 'cfg/valve.rc').exists())
            self.assertTrue(m.hud_is_current(path, name))

    def test_zip_traversal_rejected(self):
        archive = self.root / 'unsafe.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('../../outside.txt', 'bad')
        with self.assertRaises(m.SetupError):
            m.extract_hud(archive, self.root / 'unsafe')
        self.assertFalse((self.root.parent / 'outside.txt').exists())

    def test_zip_symlink_rejected(self):
        archive = self.root / 'link.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            item = zipfile.ZipInfo('idhud/link')
            item.create_system = 3
            item.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(item, '/etc/passwd')
        with self.assertRaises(m.SetupError):
            m.extract_hud(archive, self.root / 'unsafe')

    def test_ambiguous_hud_roots_rejected(self):
        archive = self.root / 'multiple.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            for name in ('hud1', 'hud2'):
                for rel in ('info.vdf', 'resource/clientscheme.res', 'scripts/hudlayout.res'):
                    z.writestr(name + '/' + rel, '{}')
        with self.assertRaises(m.SetupError):
            m.extract_hud(archive, self.root / 'multi')

    def test_download_checksum_verification(self):
        data = archive_bytes()
        asset = {'version': 'test', 'url': 'https://github.com/example/release.zip',
                 'sha256': hashlib.sha256(data).hexdigest()}
        with patch.object(m.urllib.request, 'urlopen', return_value=Response(data)):
            m.download(asset, self.root / 'download.zip', len(data) + 1)
        self.assertEqual((self.root / 'download.zip').read_bytes(), data)

    def test_download_checksum_mismatch_rejected(self):
        asset = {'version': 'test', 'url': 'https://github.com/example/release.zip', 'sha256': '0' * 64}
        with patch.object(m.urllib.request, 'urlopen', return_value=Response(b'wrong')):
            with self.assertRaisesRegex(m.SetupError, 'SHA-256 mismatch'):
                m.download(asset, self.root / 'download.zip', 1024)

    def test_download_size_limit(self):
        asset = {'version': 'test', 'url': 'https://github.com/example/release.zip', 'sha256': '0' * 64}
        with patch.object(m.urllib.request, 'urlopen', return_value=Response(b'a' * 100)):
            with self.assertRaisesRegex(m.SetupError, 'size limit'):
                m.download(asset, self.root / 'download.zip', 10)

    def test_transaction_rollback(self):
        oldhud = self.install_hud_fixture(customized=True)
        before = self.snapshot(self.tf)
        source = self.root / 'replacement'
        write(source / 'info.vdf', '{}')
        self.state.mkdir()
        original = m.copy_item
        def fails_once(src, dest):
            if src == source:
                raise OSError('injected failure')
            return original(src, dest)
        with patch.object(m, 'copy_item', side_effect=fails_once):
            with self.assertRaises(OSError):
                m.transact(self.tf, {'custom/rayshud': None, 'custom/idhud': source}, self.state, 'test')
        self.assertEqual(before, self.snapshot(self.tf))
        self.assertTrue(oldhud.exists())

    def test_edited_backup_not_restored(self):
        self.install_hud_fixture()
        self.run_main('--update-only', '--hud', 'stock', '--replace-hud')
        backup = next(self.state.rglob('manifest.json')).parent
        write(backup / 'originals/custom/rayshud/resource/clientscheme.res', 'modified')
        with self.assertRaisesRegex(m.SetupError, 'Backup missing or changed'):
            m.load_restore(backup)

    def test_bom_crlf_untouched_on_hud_only_update(self):
        path = self.tf / m.MANAGED_FILES[1]
        content = b'\xef\xbb\xbf' + path.read_bytes().replace(b'\n', b'\r\n')
        path.write_bytes(content)
        self.assertEqual(m.plan_update(self.tf, self.args('--hud', 'idhud')), {})
        self.assertEqual(path.read_bytes(), content)

    def test_multiple_old_preset_vpks_refused(self):
        write(self.tf / 'custom/mastercomfig-low-preset.vpk', vpk_bytes())
        with self.assertRaises(m.SetupError):
            m.recognized_install(self.tf)

    def test_native_and_flatpak_library_detection(self):
        for label, steam_rel in (('native', '.local/share/Steam'),
                                 ('flatpak', '.var/app/com.valvesoftware.Steam/data/Steam')):
            home = self.root / label
            write(home / steam_rel / 'steamapps/libraryfolders.vdf',
                  '"libraryfolders" { "1" { "path" "' + str(self.game.parents[2]) + '" } }')
            self.assertEqual(m.discover_games(home), [self.game.resolve()])

    def test_restore_with_install_options_rejected(self):
        with self.assertRaises(m.SetupError):
            self.run_main('--restore', str(self.root / 'backup'), '--hud', 'stock')


if __name__ == '__main__':
    unittest.main(verbosity=2)
