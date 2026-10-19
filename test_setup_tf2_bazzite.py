#!/usr/bin/env python3
"""Offline regression tests for setup_tf2_bazzite.py v1.6.1.

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


def maxihud_fixture():
    """Artificial aliases/resources only; no upstream cfg is executed by tests."""
    files = {}
    for group in ('general', 'colors', 'fonts', 'crosshairs', 'streamer', 'reset'):
        files['cfg/maxihud_customization_' + group + '.cfg'] = (
            'alias "m0_' + group + '_log" "con_logfile cfg/maxihud/' + group + '.txt"\n'
            'alias "m0_' + group + '" "m0_' + group + '_log; echo X{}; console_unlog"\n')
    files['cfg/maxihud_customization_general.cfg'] += (
        'alias "m0_customization_menu_clear" "sixense_clear_bindings; sixense_write_bindings maxihud/maxihud_customization_menu.txt"\n'
        'alias "m0_customization_menu_log" "con_logfile cfg/maxihud/maxihud_customization_menu.txt"\n'
        'alias "m0_custom_settings" "m0_customization_menu_clear; m0_customization_menu_log; echo X{Settings{Visible 1}}; console_unlog"\n'
        'alias "m0_custom_colors" "m0_customization_menu_clear; m0_customization_menu_log; echo X{Colors{Visible 1}}; console_unlog"\n'
        '================================================================\n')
    files['resource/gamemenu.res'] = (
        '"command" "engine toggle cl_mainmenu_safemode; mat_queue_mode 0"\n'
        '"other" "engine echo KeepThis"\n')
    files[m.MAXIHUD_MENU_FRAME] = (
        '"Command" "engine cl_mainmenu_safemode 0; mat_queue_mode -1; gameui_allowescape"\n'
        '"Command" "engine gameui_allowescape; mat_queue_mode -1; gamemenucommand RestartWithNewLanguage"\n'
        '"Command" "engine cl_mainmenu_safemode 0; gameui_allowescape; mat_queue_mode -1; hud_reloadscheme"\n')
    files['scripts/hudlayout.res'] = '#base "../../../cfg/maxihud/maxihud_customization_menu.txt"\n'
    return files


class Response(io.BytesIO):
    def geturl(self):
        return 'https://github.com/example/release.zip'


class SetupTests(unittest.TestCase):
    def setUp(self):
        platform = patch.object(m.sys, 'platform', 'linux')
        platform.start()
        self.addCleanup(platform.stop)
        network = patch.object(m.urllib.request, 'urlopen', side_effect=AssertionError('Unexpected live HTTP in offline tests'))
        network.start()
        self.addCleanup(network.stop)
        fixture = maxihud_fixture()
        reviewed = patch.object(m, 'MAXIHUD_REVIEWED_SHA256',
                                {rel: hashlib.sha256(fixture[rel].encode()).hexdigest()
                                 for rel in m.MAXIHUD_REVIEWED_SHA256})
        reviewed.start()
        self.addCleanup(reviewed.stop)
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
        argv = [str(SCRIPT), '--tf2-dir', str(self.game), *args]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', argv), patch.object(m.os, 'geteuid', return_value=1000), \
             patch.dict(os.environ, {'XDG_STATE_HOME': str(self.state)}), \
             patch.object(m, 'require_closed') as closed, \
             patch.object(m, 'confirm', return_value=confirmer) as confirm, \
             patch.object(m, 'download', side_effect=downloader or self.fake_download) as download, \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = m.main()
        return result, stdout.getvalue(), stderr.getvalue(), download, confirm, closed

    def test_catalog_choices_include_previous_and_new(self):
        self.assertEqual(set(m.HUD_CHOICES), {'keep', 'stock', 'middlemann', 'centerhud', 'idhud', 'hudfixes', 'rayshud', 'budhud', 'maxihud', 'toonhud'})
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


    def test_middlemann_pin_and_choice(self):
        self.assertEqual(self.args('--hud', 'middlemann').hud, 'middlemann')
        self.assertEqual(m.MIDDLEMANN['version'], 'v26.1')
        self.assertEqual(m.MIDDLEMANN['sha256'],
                         '4cc9721be700e6530f2cb731fae14ddc1d27b2b4c4aa7b42e69a3621513cf899')

    def test_middlemann_preview_preserves_all_files(self):
        self.install_hud_fixture(customized=True)
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'middlemann', '--replace-hud', '--dry-run')
        self.assertEqual(result[0], 0)
        self.assertIn('Configuration files: no changes.', result[1])
        self.assertIn('custom/rayshud', result[1])
        self.assertIn('cl_hud_minmode 0', result[1])
        self.assertFalse(result[3].called)
        self.assertFalse(result[4].called)
        self.assertEqual(before, self.snapshot())

    def test_middlemann_switch_exact_restoration_and_cfg_preservation(self):
        self.install_hud_fixture(customized=True)
        before = self.snapshot(self.tf)
        cfg_before = self.snapshot(self.tf / 'cfg')
        self.run_main('--update-only', '--hud', 'middlemann', '--replace-hud')
        self.assertTrue(m.hud_is_current(self.tf / 'custom/middlemann', 'middlemann'))
        self.assertFalse((self.tf / 'custom/middlemann/cfg').exists())
        self.assertFalse((self.tf / 'custom/rayshud').exists())
        self.assertEqual(cfg_before, self.snapshot(self.tf / 'cfg'))
        self.assertEqual(self.downloads, [m.MIDDLEMANN['url']])
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        self.assertEqual(set(ops), {'custom/middlemann', 'custom/rayshud'})
        m.transact(tf, ops, backup.parent, 'test-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_middlemann_preserves_existing_minmode_and_portrait_settings(self):
        with (self.tf / 'cfg/config.cfg').open('a') as f:
            f.write('cl_hud_minmode 1\ncl_hud_playerclass_use_playermodel 0\n')
        before = self.snapshot(self.tf / 'cfg')
        result = self.run_main('--update-only', '--hud', 'middlemann')
        self.assertEqual(before, self.snapshot(self.tf / 'cfg'))
        self.assertIn('preserves your current cl_hud_minmode', result[1])

    def test_middlemann_second_install_is_noop(self):
        self.install_hud_fixture('middlemann')
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'middlemann', '--replace-hud')
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_middlemann_remains_optional_current_rayshud_is_untouched(self):
        self.install_hud_fixture('rayshud')
        before = self.snapshot()
        result = self.run_main('--update-only')
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_middlemann_release_root_and_startup_exclusion(self):
        src = self.root / 'middlemann.zip'
        write(src, archive_bytes('middlemann',
                                {'cfg/valve.rc': 'cl_hud_minmode 0\nvgui_cache_res_files 0\nwait 200; hud_reloadscheme'},
                                folder='-middle-mann-v26.1'))
        root = m.prepare_hud(src, self.root / 'middle-unpacked', 'middlemann')
        self.assertEqual(root.name, '-middle-mann-v26.1')
        self.assertFalse((root / 'cfg').exists())
        self.assertTrue(m.hud_is_current(root, 'middlemann'))

    def test_middlemann_unexpected_joystick_script_stops_before_game_writes(self):
        before = self.snapshot(self.tf)
        def unexpected(asset, dest, maximum):
            write(dest, archive_bytes('middlemann', {'cfg/joystick.cfg': 'fps_max 30'}))
        with self.assertRaisesRegex(m.SetupError, 'Unexpected cfg contents'):
            self.run_main('--update-only', '--hud', 'middlemann', downloader=unexpected)
        self.assertEqual(before, self.snapshot(self.tf))



    def make_local_zip(self, name='toonhud', extra=None):
        contents = maxihud_fixture() if name == 'maxihud' else {}
        contents.update(extra or {})
        if name == 'maxihud':
            contents.setdefault('cfg/maxihud_customization.cfg', 'exec maxihud_first_run')
        path = self.root / ('input-' + name + '.zip')
        write(path, archive_bytes(name, contents))
        return path

    def test_new_remote_choices_dry_run_no_side_effects(self):
        self.install_hud_fixture(customized=True)
        for name in ('centerhud', 'hudfixes'):
            before = self.snapshot()
            result = self.run_main('--update-only', '--hud', name, '--replace-hud', '--dry-run')
            self.assertIn('Configuration files: no changes.', result[1])
            self.assertIn('All bundled HUD cfg scripts are omitted', result[1])
            self.assertFalse(result[3].called)
            self.assertFalse(result[4].called)
            self.assertEqual(before, self.snapshot())

    def test_new_remote_choices_switch_and_restore_exactly(self):
        self.install_hud_fixture(customized=True)
        for name in ('centerhud', 'hudfixes'):
            before = self.snapshot(self.tf)
            cfg = self.snapshot(self.tf / 'cfg')
            self.run_main('--update-only', '--hud', name, '--replace-hud')
            dest = self.tf / m.hud_relative(name)
            self.assertTrue(m.hud_is_current(dest, name))
            self.assertFalse((dest / 'cfg').exists())
            self.assertEqual(cfg, self.snapshot(self.tf / 'cfg'))
            manifests = [p for p in self.state.rglob('manifest.json')
                         if json.loads(p.read_text()).get('label') == 'update']
            backup = max(manifests, key=lambda p: p.stat().st_mtime_ns).parent
            tf, ops = m.load_restore(backup)
            m.transact(tf, ops, backup.parent, 'test-restore')
            self.assertEqual(before, self.snapshot(self.tf))

    def test_new_hud_directories_and_existing_names(self):
        self.assertEqual(m.hud_relative('centerhud'), 'custom/center-hud')
        self.assertEqual(m.hud_relative('hudfixes'), 'custom/tf2hud-fixes')
        for name in ('middlemann', 'rayshud', 'budhud', 'idhud', 'maxihud', 'toonhud'):
            self.assertEqual(m.hud_relative(name), 'custom/' + name)

    def test_all_new_hud_cfg_scripts_excluded(self):
        for name in m.ISOLATED_HUDS:
            path = self.make_local_zip(name, {'cfg/autoexec.cfg': 'fps_max 20',
                                             'cfg/joystick.cfg': 'exec reset',
                                             'cfg/overrides/scout.cfg': 'sensitivity 9'})
            asset = {'version': 'fixture', 'sha256': m.tree_hash(path)}
            dest = m.prepare_hud(path, self.root / (name + '-isolated'), name, asset)
            if name == 'maxihud':
                self.assertEqual({p.name for p in (dest / 'cfg').iterdir()},
                                 {Path(p).name for p in m.MAXIHUD_ALIAS_FILES} | {m.MAXIHUD_LOADER})
            else:
                self.assertFalse((dest / 'cfg').exists())
            self.assertTrue(m.hud_is_current(dest, name, asset))
            self.assertEqual(json.loads((dest / m.HUD_MARKER).read_text())['policy'], m.hud_policy(name))

    def test_local_choices_require_zip(self):
        before = self.snapshot()
        for name in m.LOCAL_HUDS:
            with self.assertRaisesRegex(m.SetupError, 'requires --hud-zip'):
                self.run_main('--update-only', '--hud', name, '--dry-run')
        self.assertEqual(before, self.snapshot())

    def test_local_zip_with_remote_choice_requires_pinned_digest(self):
        path = self.make_local_zip()
        with self.assertRaisesRegex(m.SetupError, 'Pinned HUD SHA-256 mismatch'):
            self.run_main('--hud', 'rayshud', '--hud-zip', str(path), '--dry-run')

    def test_local_zip_preview_reads_only(self):
        self.install_hud_fixture(customized=True)
        for name in m.LOCAL_HUDS:
            path = self.make_local_zip(name)
            before = self.snapshot()
            result = self.run_main('--update-only', '--hud', name, '--hud-zip', str(path),
                                   '--replace-hud', '--dry-run')
            if name == 'maxihud':
                self.assertIn('TF2-COMPETITIVE-MAXIHUD-MENU', result[1])
            else:
                self.assertIn('Configuration files: no changes.', result[1])
            self.assertIn('NOT authenticated', result[1])
            self.assertFalse(result[3].called)
            self.assertFalse(result[4].called)
            self.assertEqual(before, self.snapshot())

    def test_local_zip_install_no_download_preserves_cfg(self):
        self.install_hud_fixture(customized=True)
        for name in m.LOCAL_HUDS:
            path = self.make_local_zip(name)
            before = self.snapshot(self.tf / 'cfg')
            result = self.run_main('--update-only', '--hud', name, '--hud-zip', str(path), '--replace-hud')
            self.assertFalse(result[3].called)
            self.assertEqual((self.tf / m.hud_relative(name) / 'cfg').exists(), name == 'maxihud')
            after = self.snapshot(self.tf / 'cfg')
            for rel, data in before.items():
                if rel == 'overrides/autoexec.cfg':
                    expected = data + m.MAXIHUD_HOOK if name == 'maxihud' else data.replace(m.MAXIHUD_HOOK, b'')
                    self.assertEqual(after[rel], expected)
                else:
                    self.assertEqual(after[rel], data)
            self.assertEqual([p.name for p in m.hud_candidates(self.tf)], [name])

    def test_local_zip_repeat_is_noop(self):
        path = self.make_local_zip()
        args = ('--update-only', '--hud', 'toonhud', '--hud-zip', str(path))
        self.run_main(*args)
        before = self.snapshot()
        result = self.run_main(*args)
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertFalse(result[4].called)
        self.assertEqual(before, self.snapshot())

    def test_local_zip_hash_mismatch_stops_before_writes(self):
        path = self.make_local_zip()
        before = self.snapshot()
        with self.assertRaisesRegex(m.SetupError, 'SHA-256 mismatch'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(path), '--hud-sha256', '0' * 64)
        self.assertEqual(before, self.snapshot())

    def test_local_zip_optional_expected_hash_matches(self):
        path = self.make_local_zip()
        result = self.run_main('--hud', 'toonhud', '--hud-zip', str(path),
                               '--hud-sha256', m.tree_hash(path), '--dry-run')
        self.assertEqual(result[0], 0)

    def test_local_zip_invalid_expected_hash(self):
        path = self.make_local_zip()
        with self.assertRaisesRegex(m.SetupError, '64 hexadecimal'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(path), '--hud-sha256', 'not-a-hash')

    def test_local_zip_race_preserves_game(self):
        path = self.make_local_zip()
        before = self.snapshot(self.tf)
        def mutate(_yes):
            write(path, archive_bytes('toonhud', {'resource/new.txt': 'changed'}))
            return True
        with patch.object(sys, 'argv', [str(SCRIPT), '--tf2-dir', str(self.game),
                                       '--hud', 'toonhud', '--hud-zip', str(path)]), \
             patch.object(m.os, 'geteuid', return_value=1000), \
             patch.dict(os.environ, {'XDG_STATE_HOME': str(self.state)}), \
             patch.object(m, 'require_closed'), patch.object(m, 'confirm', side_effect=mutate):
            with self.assertRaisesRegex(m.SetupError, 'changed after preview'):
                m.main()
        self.assertEqual(before, self.snapshot(self.tf))

    def test_local_zip_wrong_identity_rejected(self):
        path = self.make_local_zip('rayshud')
        for name in m.LOCAL_HUDS:
            with self.assertRaises(m.SetupError):
                self.run_main('--hud', name, '--hud-zip', str(path), '--dry-run')

    def test_local_zip_packed_vpk_rejected(self):
        path = self.make_local_zip(extra={'embedded.vpk': vpk_bytes()})
        with self.assertRaisesRegex(m.SetupError, 'Packed VPKs'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(path), '--dry-run')

    def test_local_zip_traversal_rejected_in_preview(self):
        path = self.make_local_zip(extra={'../../escape': 'bad'})
        before = self.snapshot()
        with self.assertRaisesRegex(m.SetupError, 'Unsafe HUD archive member'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(path), '--dry-run')
        self.assertEqual(before, self.snapshot())

    def test_local_zip_restore_exact_prior_files(self):
        self.install_hud_fixture(customized=True)
        path = self.make_local_zip()
        before = self.snapshot(self.tf)
        self.run_main('--hud', 'toonhud', '--hud-zip', str(path), '--replace-hud')
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        m.transact(tf, ops, backup.parent, 'test-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_restore_rejects_import_flags(self):
        with self.assertRaisesRegex(m.SetupError, 'cannot be combined'):
            self.run_main('--restore', str(self.root / 'backup'), '--hud-zip', 'theme.zip')

    def test_new_options_do_not_change_default_or_applied_hud(self):
        self.install_hud_fixture('rayshud')
        before = self.snapshot()
        result = self.run_main('--update-only')
        self.assertIn('Already configured', result[1])
        self.assertEqual(before, self.snapshot())

    def test_maxihud_only_reviewed_aliases_and_loader_are_installed(self):
        path = self.make_local_zip('maxihud', {
            'cfg/maxihud_first_run.cfg': 'record unsafe; sv_allow_point_servercommand always',
            'cfg/joystick.cfg': 'exec maxihud_first_run',
            'cfg/autoexec.cfg': 'fps_max 10',
            'cfg/overrides/scout.cfg': 'sensitivity 9'})
        asset = m.local_hud_asset(self.args('--hud', 'maxihud', '--hud-zip', str(path)))
        dest = m.prepare_hud(path, self.root / 'maxi-prepared', 'maxihud', asset)
        self.assertEqual({p.name for p in (dest / 'cfg').iterdir()},
                         {Path(p).name for p in m.MAXIHUD_ALIAS_FILES} | {m.MAXIHUD_LOADER})
        loader = (dest / 'cfg' / m.MAXIHUD_LOADER).read_text()
        expected = ['tf2_competitive_maxihud_logging.cfg'] + [Path(p).name for p in m.MAXIHUD_ALIAS_FILES]
        self.assertEqual([line[5:] for line in loader.splitlines() if line.startswith('exec ')], expected)
        self.assertTrue(all(line.startswith(('//', 'alias ', 'exec ')) for line in loader.splitlines()))
        self.assertNotIn('first_run', loader)
        self.assertNotIn('valve.rc', loader)
        self.assertEqual(json.loads((dest / m.HUD_MARKER).read_text())['policy'], 'maxihud-menu-v1')

    def test_maxihud_tab_aliases_timestamp_and_namespaced_logging(self):
        source = {p: body.encode() for p, body in maxihud_fixture().items()}
        prepared = m.maxihud_menu_files(source)
        general = prepared['cfg/maxihud_customization_general.cfg'].decode()
        self.assertIn('alias "m0_custom_settings"', general)
        self.assertIn('alias "m0_custom_colors"', general)
        self.assertIn('sixense_write_bindings maxihud/maxihud_customization_menu.txt', general)
        self.assertIn('con_timestamp 0; con_logfile cfg/maxihud/maxihud_customization_menu.txt', general)
        for rel in m.MAXIHUD_ALIAS_FILES:
            text = prepared[rel].decode()
            self.assertNotIn('console_unlog', text)
            self.assertIn(m.MAXIHUD_LOG_ALIAS, text)
            self.assertTrue(all(line.startswith(('alias ', '//')) for line in text.splitlines() if line.strip()))
        self.assertIn('alias ' + m.MAXIHUD_LOG_ALIAS, prepared['cfg/' + m.MAXIHUD_LOADER].decode())
        self.assertLessEqual(len(m.MAXIHUD_LOG_ALIAS), 31)

    def test_maxihud_only_four_queue_mode_assignments_are_removed(self):
        source = {p: body.encode() for p, body in maxihud_fixture().items()}
        prepared = m.maxihud_menu_files(source)
        self.assertEqual(prepared['resource/gamemenu.res'],
                         source['resource/gamemenu.res'].replace(b'; mat_queue_mode 0', b''))
        self.assertEqual(prepared[m.MAXIHUD_MENU_FRAME],
                         source[m.MAXIHUD_MENU_FRAME].replace(b'; mat_queue_mode -1', b''))
        self.assertIn(b'cl_mainmenu_safemode', prepared[m.MAXIHUD_MENU_FRAME])
        self.assertIn(b'hud_reloadscheme', prepared[m.MAXIHUD_MENU_FRAME])
        self.assertIn(b'RestartWithNewLanguage', prepared[m.MAXIHUD_MENU_FRAME])
        self.assertIn(b'KeepThis', prepared['resource/gamemenu.res'])

    def test_maxihud_unreviewed_or_missing_file_rejected_even_in_preview(self):
        for rel in m.MAXIHUD_REVIEWED_SHA256:
            with self.subTest(file=rel):
                path = self.make_local_zip('maxihud', {rel: 'unreviewed data'})
                before = self.snapshot()
                with self.assertRaisesRegex(m.SetupError, 'reviewed v17.5'):
                    self.run_main('--update-only', '--hud', 'maxihud', '--hud-zip', str(path), '--dry-run')
                self.assertEqual(before, self.snapshot())
        source = {p: body.encode() for p, body in maxihud_fixture().items()}
        del source['cfg/maxihud_customization_general.cfg']
        with self.assertRaisesRegex(m.SetupError, 'reviewed v17.5'):
            m.maxihud_menu_files(source)

    def test_maxihud_unknown_queue_command_is_not_broadly_sanitized(self):
        source = {p: body.encode() for p, body in maxihud_fixture().items()}
        rel = 'resource/gamemenu.res'
        source[rel] += b'"Command" "engine mat_queue_mode 2"\n'
        expected = dict(m.MAXIHUD_REVIEWED_SHA256, **{rel: hashlib.sha256(source[rel]).hexdigest()})
        with patch.object(m, 'MAXIHUD_REVIEWED_SHA256', expected):
            with self.assertRaisesRegex(m.SetupError, 'queue-mode command remains'):
                m.maxihud_menu_files(source)

    def test_maxihud_hud_only_keeps_competitive_config_bytes_and_is_idempotent(self):
        auto = self.tf / 'cfg/overrides/autoexec.cfg'
        old = b'\xef\xbb\xbf' + auto.read_bytes().replace(b'\n', b'\r\n').rstrip(b'\r\n')
        auto.write_bytes(old)
        before = {rel: (self.tf / rel).read_bytes() for rel in m.MANAGED_FILES}
        path = self.make_local_zip('maxihud')
        args = ('--update-only', '--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        result = self.run_main(*args)
        self.assertFalse(result[3].called)
        self.assertEqual(auto.read_bytes(), old + m.MAXIHUD_HOOK)
        for rel in (m.MANAGED_FILES[0], m.MANAGED_FILES[2]):
            self.assertEqual((self.tf / rel).read_bytes(), before[rel])
        self.assertEqual((self.tf / 'cfg/maxihud/maxihud_customization_menu.txt').read_bytes(), b'"X" {}\n')
        snapshot = self.snapshot()
        result = self.run_main(*args)
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertFalse(result[4].called)
        self.assertEqual(snapshot, self.snapshot())

    def test_maxihud_dry_run_does_not_create_loader_hook_data_or_backup(self):
        path = self.make_local_zip('maxihud')
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'maxihud', '--hud-zip', str(path), '--dry-run')
        self.assertIn('TF2-COMPETITIVE-MAXIHUD-MENU', result[1])
        self.assertFalse(result[3].called)
        self.assertFalse(result[4].called)
        self.assertFalse(result[5].called)
        self.assertEqual(before, self.snapshot())

    def test_maxihud_first_install_and_restore_preserve_original_configs(self):
        shutil.rmtree(self.tf / 'cfg')
        (self.tf / 'custom/mastercomfig-base.vpk').unlink()
        write(self.tf / 'cfg/autoexec.cfg', 'sensitivity 1.37\nbind mouse4 +attack2\n')
        path = self.make_local_zip('maxihud')
        before = self.snapshot(self.tf)
        result = self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        auto = (self.tf / 'cfg/overrides/autoexec.cfg').read_bytes()
        self.assertIn(b'sensitivity 1.37\nbind mouse4 +attack2', auto)
        self.assertEqual(auto.count(m.MAXIHUD_HOOK), 1)
        self.assertEqual(self.downloads, [m.COMFIG['url']])
        self.assertTrue((self.tf / 'custom/maxihud/cfg' / m.MAXIHUD_LOADER).is_file())
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        m.transact(tf, ops, backup.parent, 'test-maxi-first-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_maxihud_migration_from_old_policy_has_exact_restore(self):
        path = self.make_local_zip('maxihud')
        asset = m.local_hud_asset(self.args('--hud', 'maxihud', '--hud-zip', str(path)))
        dest = self.tf / 'custom/maxihud'
        write(dest / 'info.vdf', '"HUD" { "ui_version" "3" }')
        write(dest / 'resource/personal.res', 'personal HUD edit')
        m.save_json(dest / m.HUD_MARKER, {'hud': 'maxihud', 'archive_sha256': asset['sha256'],
                    'policy': 'isolate-cfg-v1', 'tree_sha256': m.tree_hash(dest)})
        before = self.snapshot(self.tf)
        self.assertFalse(m.hud_is_current(dest, 'maxihud', asset))
        self.run_main('--update-only', '--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        self.assertTrue(m.hud_is_current(dest, 'maxihud', asset))
        backup = next(self.state.rglob('manifest.json')).parent
        entries = {x['path'] for x in json.loads((backup / 'manifest.json').read_text())['entries']}
        self.assertIn('cfg/overrides/autoexec.cfg', entries)
        self.assertIn('cfg/maxihud', entries)
        self.assertIn('cfg/tf2_competitive_maxihud_logging.cfg', entries)
        tf, ops = m.load_restore(backup)
        m.transact(tf, ops, backup.parent, 'test-maxi-migrate-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_maxihud_data_and_custom_logging_profile_survive_reapply(self):
        profile = self.tf / 'cfg/tf2_competitive_maxihud_logging.cfg'
        original = ('alias ' + m.MAXIHUD_LOG_ALIAS + ' "con_logfile tournament.log; con_timestamp 1"\n').encode()
        write(profile, original)
        write(self.tf / 'cfg/maxihud/maxihud_customization_menu.txt', '"X" {"personal" "yes"}')
        write(self.tf / 'cfg/maxihud/personal.txt', 'keep colors')
        before = self.snapshot(self.tf / 'cfg/maxihud')
        path = self.make_local_zip('maxihud')
        args = ('--update-only', '--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        self.run_main(*args)
        self.run_main(*args)
        self.assertEqual(before, self.snapshot(self.tf / 'cfg/maxihud'))
        self.assertEqual(profile.read_bytes(), original)

    def test_maxihud_existing_data_directory_missing_menu_is_restorable(self):
        write(self.tf / 'cfg/maxihud/personal.txt', 'keep me')
        path = self.make_local_zip('maxihud')
        before = self.snapshot(self.tf)
        self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        m.transact(tf, ops, backup.parent, 'test-maxi-data-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_maxihud_switch_to_stock_removes_only_owned_hook(self):
        auto = self.tf / 'cfg/overrides/autoexec.cfg'
        before = auto.read_bytes()
        path = self.make_local_zip('maxihud')
        self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        snapshot = self.snapshot(self.tf)
        self.run_main('--update-only', '--hud', 'stock', '--replace-hud')
        self.assertEqual(auto.read_bytes(), before)
        self.assertTrue((self.tf / 'cfg/maxihud').is_dir())
        self.assertTrue((self.tf / 'cfg/tf2_competitive_maxihud_logging.cfg').is_file())
        backups = list(self.state.rglob('manifest.json'))
        backup = max(backups, key=lambda p: p.stat().st_mtime_ns).parent
        tf, ops = m.load_restore(backup)
        m.transact(tf, ops, backup.parent, 'test-maxi-stock-restore')
        self.assertEqual(snapshot, self.snapshot(self.tf))

    def test_maxihud_apply_failure_rolls_back_hook_profile_and_data_directory(self):
        self.install_hud_fixture(customized=True)
        path = self.make_local_zip('maxihud')
        before = self.snapshot(self.tf)
        copy = m.copy_item
        failed = False
        def fail_once(src, dst):
            nonlocal failed
            if dst.resolve() == (self.tf / 'custom/maxihud').resolve() and not failed:
                failed = True
                raise OSError('injected MaxiHUD copy failure')
            return copy(src, dst)
        with patch.object(m, 'copy_item', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'injected MaxiHUD'):
                self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        self.assertTrue(failed)
        self.assertEqual(before, self.snapshot(self.tf))
        self.assertEqual(json.loads(next(self.state.rglob('manifest.json')).read_text())['status'], 'rolled-back')

    def test_maxihud_support_data_race_stops_before_game_apply(self):
        path = self.make_local_zip('maxihud')
        auto = (self.tf / 'cfg/overrides/autoexec.cfg').read_bytes()
        prepare = m.prepare_hud
        def concurrent_change(*args):
            result = prepare(*args)
            write(self.tf / 'cfg/maxihud/concurrent.txt', 'new user data')
            return result
        with patch.object(m, 'prepare_hud', side_effect=concurrent_change):
            with self.assertRaisesRegex(m.SetupError, 'changed after the preview'):
                self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        self.assertEqual((self.tf / 'cfg/overrides/autoexec.cfg').read_bytes(), auto)
        self.assertFalse((self.tf / 'custom/maxihud').exists())
        self.assertFalse(list(self.state.rglob('manifest.json')))

    def test_maxihud_modified_startup_block_is_not_overwritten(self):
        path = self.make_local_zip('maxihud')
        auto = self.tf / 'cfg/overrides/autoexec.cfg'
        with auto.open('ab') as stream:
            stream.write(m.MAXIHUD_HOOK.replace(b'exec tf2_', b'exec user_tf2_'))
        before = self.snapshot()
        with self.assertRaisesRegex(m.SetupError, 'startup block was edited'):
            self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--replace-hud')
        self.assertEqual(before, self.snapshot())

    def test_maxihud_wrong_data_type_and_symlink_profile_are_rejected(self):
        path = self.make_local_zip('maxihud')
        data = self.tf / 'cfg/maxihud'
        write(data, 'ordinary file, not a directory')
        before = self.snapshot()
        with self.assertRaisesRegex(m.SetupError, 'ordinary directory'):
            self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--dry-run')
        self.assertEqual(before, self.snapshot())
        data.unlink()
        target = self.root / 'logging.cfg'
        write(target, 'private file')
        (self.tf / 'cfg/tf2_competitive_maxihud_logging.cfg').symlink_to(target)
        with self.assertRaisesRegex(m.SetupError, 'Symlink'):
            self.run_main('--hud', 'maxihud', '--hud-zip', str(path), '--dry-run')
        self.assertEqual(target.read_text(), 'private file')

    def resource_main(self, *args):
        """Resource helpers must not discover TF2 or run any setup operation."""
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', [str(SCRIPT), *args]), \
             patch.object(m.os, 'geteuid', return_value=1000), \
             patch.object(m, 'discover_games', side_effect=AssertionError('game discovery')), \
             patch.object(m, 'require_closed', side_effect=AssertionError('process scan')), \
             patch.object(m, 'transact', side_effect=AssertionError('game writes')), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = m.main()
        return result, out.getvalue(), err.getvalue()

    def png_fixture(self):
        # A tiny test-only PNG, NOT a screenshot and never distributed as a preview.
        import base64
        return base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jEOsAAAAASUVORK5CYII=')

    def test_resource_catalog_covers_all_eight(self):
        expected = set(m.HUDS) | set(m.LOCAL_HUDS)
        self.assertEqual(set(m.HUD_HELP), expected)
        self.assertEqual({item['name'] for item in m.GALLERY_ITEMS}, expected)
        self.assertEqual(len(m.GALLERY_ITEMS), 8)
        for item in m.GALLERY_ITEMS:
            self.assertTrue(item['image'].startswith('https://'))
            self.assertTrue(item['gallery'].startswith('https://'))
        for value in m.HUD_HELP.values():
            self.assertTrue(value['notes'])
            self.assertTrue(all(url.startswith('https://') for label, url in value['links']))

    def test_hud_info_all_is_read_only(self):
        before = self.snapshot()
        with patch.object(m, 'download', side_effect=AssertionError('network')), \
             patch.object(m, 'gallery_read_url', side_effect=AssertionError('network')):
            result = self.resource_main('--hud-info', 'all')
        self.assertEqual(result[0], 0)
        for name in m.HUD_HELP:
            self.assertIn(name.upper(), result[1])
        self.assertEqual(before, self.snapshot())

    def test_info_explains_fonts_theme_export_and_omitted_support(self):
        _, text, _ = self.resource_main('--hud-info', 'toonhud')
        self.assertIn('Custom font', text)
        self.assertIn('https://toonhud.com/faq', text)
        self.assertIn('theme', text)
        _, text, _ = self.resource_main('--hud-info', 'centerhud')
        self.assertIn('already in the download', text)
        self.assertIn('excludes', text)

    def test_modes_reject_accidental_installation_flags(self):
        variants = [('--hud-info', 'all', '--hud', 'rayshud'),
                    ('--fetch-hud', 'rayshud', '--update-only'),
                    ('--build-gallery', 'out.html', '--preset', 'low'),
                    ('--hud-info', 'rayshud', '--fetch-hud', 'rayshud'),
                    ('--list-huds', '--build-gallery', 'out.html'),
                    ('--output', 'a-directory'),
                    ('--gallery-partial',),
                    ('--gallery-images', 'some-directory')]
        before = self.snapshot()
        for flags in variants:
            with self.subTest(flags=flags), self.assertRaises(m.SetupError):
                self.resource_main(*flags)
        self.assertEqual(before, self.snapshot())

    def test_fetch_hud_dry_run_zero_network_or_writes(self):
        before = self.snapshot()
        output = self.root / 'new-download-dir'
        with patch.object(m, 'download', side_effect=AssertionError('network')):
            code, text, _ = self.resource_main('--fetch-hud', 'middlemann', '--output', str(output), '--dry-run')
        self.assertEqual(code, 0)
        self.assertIn(m.MIDDLEMANN['url'], text)
        self.assertIn(m.MIDDLEMANN['sha256'], text)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(output.exists())

    def test_fetch_saves_complete_archive_not_stripped_cfg(self):
        blob = archive_bytes('centerhud', {'cfg/support.cfg': 'echo support'})
        digest = hashlib.sha256(blob).hexdigest()
        before = self.snapshot(self.tf)
        output = self.root / 'downloads'
        def fake(asset, dest, maximum):
            write(dest, blob)
        with patch.dict(m.CENTERHUD, {'sha256': digest}), patch.object(m, 'download', side_effect=fake):
            code, text, _ = self.resource_main('--fetch-hud', 'centerhud', '--output', str(output))
        self.assertEqual(code, 0)
        package = output / ('centerhud-' + m.CENTERHUD['version'] + '.zip')
        self.assertEqual(package.read_bytes(), blob)
        with zipfile.ZipFile(package) as archive:
            self.assertIn('centerhud/cfg/support.cfg', archive.namelist())
        self.assertEqual(before, self.snapshot(self.tf))

    def test_fetch_cached_verified_zip_no_download(self):
        blob = archive_bytes('rayshud')
        output = self.root / 'downloads'
        path = output / ('rayshud-' + m.RAYSHUD['version'] + '.zip')
        write(path, blob)
        before = self.snapshot()
        with patch.dict(m.RAYSHUD, {'sha256': hashlib.sha256(blob).hexdigest()}), \
             patch.object(m, 'download', side_effect=AssertionError('no download')):
            code, text, _ = self.resource_main('--fetch-hud', 'rayshud', '--output', str(output))
        self.assertEqual(code, 0)
        self.assertIn('already present', text)
        self.assertEqual(before, self.snapshot())

    def test_fetch_wont_overwrite_wrong_existing_zip(self):
        output = self.root / 'downloads'
        write(output / ('rayshud-' + m.RAYSHUD['version'] + '.zip'), 'keep me')
        before = self.snapshot()
        with self.assertRaisesRegex(m.SetupError, 'different file already exists'):
            self.resource_main('--fetch-hud', 'rayshud', '--output', str(output))
        self.assertEqual(before, self.snapshot())

    def test_fetch_wrong_digest_does_not_publish_partial_file(self):
        output = self.root / 'downloads'
        with patch.object(m, 'download', side_effect=lambda a, d, maximum: write(d, b'wrong')), \
             self.assertRaisesRegex(m.SetupError, 'final SHA-256'):
            self.resource_main('--fetch-hud', 'rayshud', '--output', str(output))
        self.assertFalse(output.exists())

    def test_fetch_failure_leaves_destination_untouched(self):
        output = self.root / 'downloads'
        with patch.object(m, 'download', side_effect=m.SetupError('offline')), \
             self.assertRaisesRegex(m.SetupError, 'offline'):
            self.resource_main('--fetch-hud', 'rayshud', '--output', str(output))
        self.assertFalse(output.exists())

    def test_fetch_manual_huds_reports_sources_without_writes(self):
        before = self.snapshot()
        for name in m.LOCAL_HUDS:
            code, text, _ = self.resource_main('--fetch-hud', name, '--dry-run')
            self.assertEqual(code, 0)
            self.assertIn('Manual acquisition', text)
            with self.assertRaisesRegex(m.SetupError, 'user-selected ZIP'):
                self.resource_main('--fetch-hud', name)
        self.assertEqual(before, self.snapshot())

    def test_pinned_local_zip_install_preserves_game_cfg_without_network(self):
        path = self.root / 'idhud-exact.zip'
        write(path, archive_bytes('idhud'))
        self.install_hud_fixture(customized=True)
        before = self.snapshot(self.tf / 'cfg')
        with patch.dict(m.IDHUD, {'sha256': m.tree_hash(path)}):
            result = self.run_main('--update-only', '--hud', 'idhud', '--hud-zip', str(path), '--replace-hud')
        self.assertEqual(result[0], 0)
        self.assertFalse(result[3].called)
        self.assertIn('built-in pinned upstream', result[1])
        self.assertEqual(before, self.snapshot(self.tf / 'cfg'))
        self.assertTrue((self.tf / 'custom/idhud').is_dir())

    def test_pinned_local_zip_preview_and_repeat(self):
        path = self.root / 'idhud-exact.zip'
        write(path, archive_bytes('idhud'))
        flags = ('--update-only', '--hud', 'idhud', '--hud-zip', str(path))
        with patch.dict(m.IDHUD, {'sha256': m.tree_hash(path)}):
            before = self.snapshot()
            self.run_main(*flags, '--dry-run')
            self.assertEqual(before, self.snapshot())
            self.run_main(*flags)
            before = self.snapshot()
            result = self.run_main(*flags)
            self.assertIn('Already configured', result[1])
            self.assertEqual(before, self.snapshot())

    def test_pinned_local_zip_cannot_bypass_pin_with_user_digest(self):
        path = self.root / 'wrong-version.zip'
        write(path, archive_bytes('rayshud'))
        with self.assertRaisesRegex(m.SetupError, 'Pinned HUD SHA-256 mismatch'):
            self.run_main('--hud', 'rayshud', '--hud-zip', str(path),
                          '--hud-sha256', m.tree_hash(path), '--dry-run')

    def test_pinned_hash_without_file_rejected(self):
        with self.assertRaisesRegex(m.SetupError, 'requires --hud-zip'):
            self.run_main('--hud', 'rayshud', '--hud-sha256', '0' * 64, '--dry-run')

    def test_gallery_dry_run_no_network_or_writes(self):
        before = self.snapshot()
        with patch.object(m, 'fetch_gallery_image', side_effect=AssertionError('network')):
            code, text, _ = self.resource_main('--build-gallery', str(self.root / 'new/offline.html'), '--dry-run')
        self.assertEqual(code, 0)
        self.assertIn('No network', text)
        self.assertEqual(before, self.snapshot())

    def test_gallery_contains_eight_embedded_images_no_remote_sources(self):
        from html.parser import HTMLParser
        class Images(HTMLParser):
            def __init__(self):
                super().__init__()
                self.sources = []
            def handle_starttag(self, tag, attrs):
                if tag == 'img':
                    self.sources.append(dict(attrs)['src'])
        out = self.root / 'offline.html'
        before = self.snapshot(self.tf)
        with patch.object(m, 'fetch_gallery_image', return_value=(self.png_fixture(), 'image/png', 'https://example.test/source')):
            code, text, _ = self.resource_main('--build-gallery', str(out))
        self.assertEqual(code, 0)
        parser = Images()
        parser.feed(out.read_text())
        self.assertEqual(len(parser.sources), 8)
        self.assertTrue(all(url.startswith('data:image/png;base64,') for url in parser.sources))
        self.assertIn("img-src data:", out.read_text())
        self.assertNotIn('<script', out.read_text())
        self.assertEqual(before, self.snapshot(self.tf))

    def test_gallery_failure_is_not_a_fake_completed_page(self):
        out = self.root / 'new/offline.html'
        with patch.object(m, 'fetch_gallery_image', side_effect=m.SetupError('host unavailable')), \
             self.assertRaisesRegex(m.SetupError, 'No gallery was written'):
            self.resource_main('--build-gallery', str(out))
        self.assertFalse(out.parent.exists())

    def test_gallery_partial_mode_explicit_and_exit_two(self):
        out = self.root / 'partial.html'
        def one_missing(item, directory):
            if item['name'] == 'toonhud':
                raise m.SetupError('could not download')
            return self.png_fixture(), 'image/png', item['image']
        with patch.object(m, 'fetch_gallery_image', side_effect=one_missing):
            code, text, _ = self.resource_main('--build-gallery', str(out), '--gallery-partial')
        self.assertEqual(code, 2)
        self.assertIn('PARTIAL: 1 preview(s) missing', out.read_text())
        self.assertEqual(out.read_text().count('<img src="data:'), 7)
        self.assertIn('Screenshot unavailable', out.read_text())

    def test_gallery_refuses_existing_file(self):
        out = self.root / 'comparison.html'
        write(out, 'preserve old gallery')
        with self.assertRaisesRegex(m.SetupError, 'exists'), \
             patch.object(m, 'fetch_gallery_image', side_effect=AssertionError('network')):
            self.resource_main('--build-gallery', str(out))
        self.assertEqual(out.read_text(), 'preserve old gallery')

    def test_gallery_rejects_non_html_output(self):
        with self.assertRaisesRegex(m.SetupError, '.html'):
            self.resource_main('--build-gallery', str(self.root / 'autoexec.cfg'))

    def test_gallery_local_images_never_need_network(self):
        directory = self.root / 'screenshots'
        for item in m.GALLERY_ITEMS:
            write(directory / (item['name'] + '.png'), self.png_fixture())
        out = self.root / 'offline-local.html'
        with patch.object(m, 'gallery_read_url', side_effect=AssertionError('network')):
            code, _, _ = self.resource_main('--build-gallery', str(out), '--gallery-images', str(directory))
        self.assertEqual(code, 0)
        self.assertEqual(out.read_text().count('User-supplied local preview:'), 8)

    def test_gallery_local_duplicates_are_explicit(self):
        item = m.GALLERY_ITEMS[0]
        write(self.root / (item['name'] + '.png'), self.png_fixture())
        write(self.root / (item['name'] + '.jpg'), self.png_fixture())
        with self.assertRaisesRegex(m.SetupError, 'Multiple local previews'):
            m.fetch_gallery_image(item, self.root)

    def test_gallery_rejects_html_svg_and_empty_images(self):
        for data in (b'', b'<html>' + b'x' * 100, b'<svg>' + b'x' * 100):
            with self.subTest(data=data), self.assertRaises(m.SetupError):
                m.image_mime(data)
        self.assertEqual(m.image_mime(self.png_fixture()), 'image/png')

    def test_gallery_raw_github_fallback(self):
        import base64
        item = next(item for item in m.GALLERY_ITEMS if item['name'] == 'centerhud')
        data = self.png_fixture()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        payload = json.dumps({'encoding': 'base64', 'sha': blob,
                              'content': base64.b64encode(data).decode()}).encode()
        with patch.object(m, 'gallery_read_url', side_effect=[OSError('raw blocked'), payload]) as read:
            contents, mime, source = m.fetch_gallery_image(item)
        self.assertEqual(contents, data)
        self.assertEqual(mime, 'image/png')
        self.assertIn('api.github.com/repos/mastercomfig/hud-db/contents/', read.call_args.args[0])

    def test_gallery_fallback_bad_blob_digest_rejected(self):
        import base64
        item = next(item for item in m.GALLERY_ITEMS if item['name'] == 'centerhud')
        payload = json.dumps({'encoding': 'base64', 'sha': '0' * 40,
                              'content': base64.b64encode(self.png_fixture()).decode()}).encode()
        with patch.object(m, 'gallery_read_url', side_effect=[OSError('raw blocked'), payload]), \
             self.assertRaisesRegex(m.SetupError, 'blob checksum mismatch'):
            m.fetch_gallery_image(item)

    def test_gallery_https_redirect_and_initial_url_checks(self):
        for url in ('file:///etc/passwd', 'http://example.com/img.png', 'https://user:password@example.com/img.png'):
            with self.subTest(url=url), self.assertRaises(m.SetupError):
                m.gallery_read_url(url, 1024)
        req = m.urllib.request.Request('https://example.com/x')
        with self.assertRaisesRegex(m.SetupError, 'unsafe screenshot redirect'):
            m.HTTPSOnlyRedirect().redirect_request(req, None, 302, '', {}, 'http://example.com/x')

    def test_write_new_file_never_replaces_existing_or_symlink(self):
        path = self.root / 'output.html'
        write(path, 'keep')
        with self.assertRaises(m.SetupError):
            m.write_new_file(path, b'replacement')
        symlink = self.root / 'alias.html'
        symlink.symlink_to(path)
        with self.assertRaises(m.SetupError):
            m.write_new_file(symlink, b'replacement')
        self.assertEqual(path.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main(verbosity=2)
