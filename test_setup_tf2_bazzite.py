#!/usr/bin/env python3
"""Offline regression tests for setup_tf2_bazzite.py.

Run: python3 -m unittest -v test_setup_tf2_bazzite.py
Requires only Python's standard library. Uses temporary game trees and synthetic
ZIP/network fixtures; does NOT launch TF2 or validate live upstream downloads.
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
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tf2setup', HERE / 'setup_tf2_bazzite.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def archive_bytes(name='fixture', startup=True, extra=None):
    stream = io.BytesIO()
    files = {
        name + '/info.vdf': '"hud" { "ui_version" "3" }',
        name + '/resource/clientscheme.res': '"Scheme" {}',
        name + '/scripts/hudlayout.res': '"HudLayout" {}',
    }
    if startup:
        files[name + '/cfg/valve.rc'] = 'vgui_cache_res_files 0\ncl_hud_minmode 0\n'
    if extra:
        files.update({name + '/' + rel: data for rel, data in extra.items()})
    with zipfile.ZipFile(stream, 'w') as archive:
        for rel, data in files.items():
            archive.writestr(rel, data)
    return stream.getvalue()


class GameCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'Team Fortress 2'
        self.tf = self.game / 'tf'
        self.tf.mkdir(parents=True)
        (self.tf / 'gameinfo.txt').write_text('"GameInfo" {}\n')
        (self.tf / 'custom').mkdir()
        staged = self.root / 'initial-cfg'
        m.stage_cfg(self.tf, staged, 'low', '240', visual_clarity=True, viewmodels='hidden')
        shutil.copytree(staged, self.tf / 'cfg')
        (self.tf / 'custom/mastercomfig-base.vpk').write_bytes(struct.pack('<III', 0x55AA1234, 1, 1) + b'\0')
        auto = self.tf / 'cfg/overrides/autoexec.cfg'
        auto.write_text('sensitivity 1.7\nbind "q" "lastinv"\n' + auto.read_text())
        modules = self.tf / 'cfg/overrides/modules.cfg'
        modules.write_text('effects=very_low\n' + modules.read_text())
        (self.tf / 'cfg/overrides/soldier.cfg').write_text('// Custom class settings\nviewmodel_fov 80\n')
        self.state = self.root / 'state'

    def fixture_hud(self, name, managed=True, extra=None):
        archive = self.root / (name + '-fixture.zip')
        archive.write_bytes(archive_bytes(name, startup=(name != 'idhud'), extra=extra))
        stage = self.root / (name + '-unpack-' + str(len(list(self.root.iterdir()))))
        result = m.prepare_hud(archive, stage, name)
        dest = self.tf / 'custom' / name
        shutil.copytree(result, dest)
        if not managed:
            (dest / m.HUD_MARKER).unlink()
        return dest

    def protected_bytes(self):
        paths = list((self.tf / 'cfg').rglob('*')) + [self.tf / 'custom/mastercomfig-base.vpk']
        return {str(p.relative_to(self.tf)): p.read_bytes() for p in paths if p.is_file()}

    def args(self, *options):
        return m.parser().parse_args(['--tf2-dir', str(self.game), '--update-only', *options])

    def run_main(self, *options, download=None):
        output = io.StringIO()
        if download is None:
            def download(asset, dest, maximum):
                name = next(n for n, a in m.HUDS.items() if asset is a)
                dest.write_bytes(archive_bytes(name, startup=(name != 'idhud')))
        with mock.patch.object(sys, 'argv', ['setup', '--tf2-dir', str(self.game), *options]), \
             mock.patch.object(os, 'geteuid', return_value=1000), \
             mock.patch.dict(os.environ, {'XDG_STATE_HOME': str(self.state)}), \
             mock.patch.object(m, 'require_closed'), \
             mock.patch.object(m, 'download', side_effect=download) as dl, \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = m.main()
        return result, output.getvalue(), dl.call_count

    def test_existing_setup_is_recognized(self):
        self.assertTrue(m.recognized_install(self.tf))

    def test_each_hud_only_delta_is_empty(self):
        before = self.protected_bytes()
        for name in m.HUD_CHOICES:
            with self.subTest(hud=name):
                self.assertEqual(m.plan_update(self.tf, self.args('--hud', name)), {})
        self.assertEqual(before, self.protected_bytes())

    def test_visual_clarity_reapply_is_noop(self):
        self.assertEqual(m.plan_update(self.tf, self.args('--visual-clarity')), {})

    def test_effects_and_hidden_weapons_survive_hud_update(self):
        self.fixture_hud('rayshud')
        before = self.protected_bytes()
        self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', '--yes')
        self.assertEqual(before, self.protected_bytes())
        self.assertIn('effects=very_low', (self.tf / m.MANAGED_FILES[2]).read_text())
        self.assertIn('r_drawviewmodel 0', (self.tf / m.MANAGED_FILES[1]).read_text())

    def test_keep_has_no_hud_operations(self):
        self.fixture_hud('rayshud')
        self.assertEqual(m.plan_hud(self.tf, 'keep', False), (False, []))

    def test_keep_with_replace_fails(self):
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'keep', True)

    def test_new_idhud_requests_download(self):
        self.assertEqual(m.plan_hud(self.tf, 'idhud', False), (True, []))

    def test_new_middlemann_requests_download(self):
        self.assertEqual(m.plan_hud(self.tf, 'middlemann', False), (True, []))

    def test_switch_requires_authorization(self):
        self.fixture_hud('rayshud')
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'idhud', False)

    def test_authorized_switch_removes_other_hud(self):
        self.fixture_hud('rayshud')
        self.assertEqual(m.plan_hud(self.tf, 'idhud', True), (True, ['custom/rayshud']))

    def test_same_release_is_noop_for_all_choices(self):
        for name in m.HUDS:
            with self.subTest(hud=name):
                p = self.fixture_hud(name)
                self.assertTrue(m.hud_is_current(p, name))
                self.assertEqual(m.plan_hud(self.tf, name, False), (False, []))
                shutil.rmtree(p)

    def test_customized_hud_is_not_overwritten_silently(self):
        p = self.fixture_hud('rayshud')
        (p / 'resource/custom-color.res').write_text('My custom settings\n')
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'rayshud', False)
        self.assertEqual(m.plan_hud(self.tf, 'rayshud', True), (True, []))

    def test_old_hud_policy_still_accepted(self):
        p = self.fixture_hud('budhud')
        self.assertEqual(json.loads((p / m.HUD_MARKER).read_text())['policy'], 'preserve-startup-v1')
        self.assertTrue(m.hud_is_current(p, 'budhud'))

    def test_dry_run_has_no_writes_downloads_or_backups(self):
        self.fixture_hud('rayshud')
        before = m.tree_hash(self.root)
        result, text, count = self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', '--dry-run')
        self.assertEqual(result, 0)
        self.assertEqual(count, 0)
        self.assertIn('Configuration files: no changes.', text)
        self.assertIn('custom/rayshud', text)
        self.assertIn('HUD install: idhud 4.0.8', text)
        self.assertEqual(before, m.tree_hash(self.root))
        self.assertFalse(self.state.exists())

    def test_other_new_hud_dry_run_is_readonly(self):
        before = m.tree_hash(self.root)
        _, text, count = self.run_main('--update-only', '--hud', 'middlemann', '--dry-run')
        self.assertEqual(count, 0)
        self.assertIn('cl_hud_minmode 0', text)
        self.assertEqual(before, m.tree_hash(self.root))

    def test_noop_does_not_download_or_create_state(self):
        self.fixture_hud('idhud')
        before = m.tree_hash(self.root)
        _, text, count = self.run_main('--update-only', '--hud', 'idhud', '--yes')
        self.assertEqual(count, 0)
        self.assertIn('Already configured', text)
        self.assertEqual(before, m.tree_hash(self.root))

    def test_switch_and_exact_restore(self):
        p = self.fixture_hud('rayshud')
        (p / 'personal-notes.txt').write_text('Keep my exact customized HUD\n')
        protected = self.protected_bytes()
        old = m.tree_hash(p)
        _, text, count = self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', '--yes')
        self.assertEqual(count, 1)
        self.assertEqual([p.name for p in m.hud_candidates(self.tf)], ['idhud'])
        self.assertEqual(protected, self.protected_bytes())
        self.assertIn('--restore', text)
        backups = list((self.state / 'tf2-competitive-backups').glob('*/manifest.json'))
        self.assertEqual(len(backups), 1)
        tf, ops = m.load_restore(backups[0].parent)
        self.assertEqual(tf, self.tf)
        self.assertEqual(set(ops), {'custom/idhud', 'custom/rayshud'})
        m.transact(tf, ops, self.state / 'tf2-competitive-backups', 'before-restore')
        self.assertFalse((tf / 'custom/idhud').exists())
        self.assertEqual(old, m.tree_hash(tf / 'custom/rayshud'))
        self.assertEqual(protected, self.protected_bytes())

    def test_three_sequential_switches_do_not_stack(self):
        before = self.protected_bytes()
        self.fixture_hud('rayshud')
        for name in ('idhud', 'middlemann', 'budhud'):
            self.run_main('--update-only', '--hud', name, '--replace-hud', '--yes')
            self.assertEqual([p.name for p in m.hud_candidates(self.tf)], [name])
            self.assertEqual(before, self.protected_bytes())

    def test_stock_requires_authorization(self):
        self.fixture_hud('rayshud')
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'stock', False)

    def test_stock_without_custom_hud_is_noop(self):
        self.assertEqual(m.plan_hud(self.tf, 'stock', False), (False, []))
        _, _, count = self.run_main('--update-only', '--hud', 'stock', '--yes')
        self.assertEqual(count, 0)
        self.assertFalse(self.state.exists())

    def test_stock_only_removes_detected_huds(self):
        self.fixture_hud('rayshud')
        extra = self.tf / 'custom/my-sound-pack/sound/hitsound.wav'
        extra.parent.mkdir(parents=True)
        extra.write_bytes(b'fake-sound-file')
        before = self.protected_bytes()
        _, text, count = self.run_main('--update-only', '--hud', 'stock', '--replace-hud', '--yes')
        self.assertEqual(count, 0)
        self.assertEqual(m.hud_candidates(self.tf), [])
        self.assertTrue(extra.is_file())
        self.assertEqual(before, self.protected_bytes())
        self.assertIn('no HUD download or config reset', text)

    def test_stock_dry_run_is_readonly(self):
        self.fixture_hud('budhud')
        before = m.tree_hash(self.root)
        _, _, count = self.run_main('--update-only', '--hud', 'stock', '--replace-hud', '--dry-run')
        self.assertEqual(count, 0)
        self.assertEqual(before, m.tree_hash(self.root))

    def test_case_insensitive_hud_detection(self):
        p = self.tf / 'custom/not_named_as_a_hud/Resource/UI/HudPlayerHealth.res'
        p.parent.mkdir(parents=True)
        p.write_text('HUD fixture\n')
        self.assertIn(p.parents[2], m.hud_candidates(self.tf))

    def test_marker_detects_renamed_managed_hud(self):
        p = self.tf / 'custom/random_name'
        p.mkdir()
        (p / m.HUD_MARKER).write_text('{}')
        self.assertIn(p, m.hud_candidates(self.tf))

    def test_packed_hud_is_included_in_replacement(self):
        p = self.tf / 'custom/idhud.vpk'
        p.write_bytes(b'fixture')
        self.assertEqual(m.plan_hud(self.tf, 'idhud', True), (True, ['custom/idhud.vpk']))

    def test_mastercomfig_addons_are_not_huds(self):
        p = self.tf / 'custom/mastercomfig-addon-hud.vpk'
        p.write_bytes(b'fixture')
        self.assertEqual(m.hud_candidates(self.tf), [])

    def test_symlinked_hud_refused(self):
        external = self.root / 'external'
        external.mkdir()
        (external / 'info.vdf').write_text('fixture')
        (self.tf / 'custom/rayshud').symlink_to(external, target_is_directory=True)
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'idhud', True)

    def test_failed_download_does_not_change_game(self):
        self.fixture_hud('rayshud')
        before = m.tree_hash(self.tf)
        def fail(*args):
            raise m.SetupError('Simulated failed download')
        with self.assertRaises(m.SetupError):
            self.run_main('--update-only', '--hud', 'idhud', '--replace-hud', '--yes', download=fail)
        self.assertEqual(before, m.tree_hash(self.tf))
        self.assertEqual(list(self.state.rglob('manifest.json')), [])

    def test_preserve_unrelated_bytes_on_visual_change(self):
        a = self.args('--viewmodels', 'minimal')
        result = m.plan_update(self.tf, a)
        self.assertEqual(set(result), {m.MANAGED_FILES[1]})
        self.assertEqual(result[m.MANAGED_FILES[1]], (self.tf / m.MANAGED_FILES[1]).read_bytes().replace(b'r_drawviewmodel 0', b'r_drawviewmodel 1'))

    def test_conflicting_scalar_fails(self):
        file = self.tf / m.MANAGED_FILES[1]
        file.write_text(file.read_text() + '\nr_drawviewmodel 1\n')
        with self.assertRaises(m.SetupError):
            m.plan_update(self.tf, self.args('--viewmodels', 'minimal'))

    def test_invalid_hud_rejected(self):
        with self.assertRaises(m.SetupError):
            m.plan_hud(self.tf, 'unknown', True)

    def test_old_format_backup_can_be_read(self):
        b = self.root / 'old-v1-backup'
        src = b / 'originals/cfg'
        shutil.copytree(self.tf / 'cfg', src)
        m.save_json(b / 'manifest.json', {'format': 'tf2-competitive-setup-v1', 'tf': str(self.tf), 'status': 'complete',
                                       'entries': [{'path': 'cfg', 'existed': True, 'sha256': m.tree_hash(src)}]})
        tf, ops = m.load_restore(b)
        self.assertEqual(tf, self.tf)
        self.assertEqual(ops['cfg'], src)

    def test_transaction_failure_rolls_back(self):
        self.fixture_hud('rayshud')
        staged = self.root / 'staged'
        staged.mkdir()
        (staged / 'info.vdf').write_text('fixture')
        state = self.root / 'backup-state'
        state.mkdir()
        before = m.tree_hash(self.tf)
        original_copy = m.copy_item
        def interrupted_copy(src, dst):
            if src == staged:
                raise OSError('Simulated failure applying new HUD')
            return original_copy(src, dst)
        with mock.patch.object(m, 'copy_item', side_effect=interrupted_copy), self.assertRaises(OSError):
            m.transact(self.tf, {'custom/rayshud': None, 'custom/idhud': staged}, state, 'failure-test')
        self.assertEqual(before, m.tree_hash(self.tf))

    def test_update_only_rejects_unmanaged_game(self):
        for rel in m.MANAGED_FILES:
            (self.tf / rel).unlink()
        with self.assertRaises(m.SetupError):
            self.run_main('--update-only', '--hud', 'idhud', '--dry-run')


class ArchiveAndCatalogCase(unittest.TestCase):
    def test_catalog_lists_new_and_existing_huds_without_game_or_network(self):
        with mock.patch.object(sys, 'argv', ['setup', '--list-huds']), \
             mock.patch.object(m, 'discover_games', side_effect=AssertionError('must not inspect game')), \
             mock.patch.object(m, 'download', side_effect=AssertionError('must not download')), \
             contextlib.redirect_stdout(io.StringIO()) as text:
            self.assertEqual(m.main(), 0)
        for name in m.HUD_CHOICES:
            self.assertIn(name, text.getvalue())

    def test_catalog_rejects_mutation_options(self):
        with mock.patch.object(sys, 'argv', ['setup', '--list-huds', '--hud', 'idhud']), self.assertRaises(m.SetupError):
            m.main()

    def test_parser_retains_old_options(self):
        for name in ('keep', 'budhud', 'rayshud'):
            args = m.parser().parse_args(['--hud', name, '--visual-clarity', '--viewmodels', 'hidden', '--dry-run'])
            self.assertEqual(args.hud, name)
            self.assertTrue(args.visual_clarity)
            self.assertTrue(args.dry_run)

    def test_baseline_dependency_pin_unchanged(self):
        self.assertEqual(m.COMFIG['version'], '9.100.1')
        self.assertEqual(m.COMFIG['sha256'], 'cdabc8251864a1ab2ef7f7ffed1b44f52810956e476d62183b8d7e3e960d8650')

    def test_all_downloads_pinned_to_https_releases_with_digests(self):
        for asset in [m.COMFIG, *m.HUDS.values()]:
            self.assertTrue(asset['url'].startswith('https://github.com/'))
            self.assertIn('/releases/download/' + asset['version'] + '/', asset['url'])
            self.assertRegex(asset['sha256'], r'^[0-9a-f]{64}$')

    def test_old_hud_pins_unchanged(self):
        self.assertEqual(m.RAYSHUD['version'], '2026.0111')
        self.assertEqual(m.RAYSHUD['sha256'], '09c695faa1243d649dff5636d1ccb0c831a6f4f6d118380b2e40d451f6dbd014')
        self.assertEqual(m.BUDHUD['version'], '2511_01')
        self.assertEqual(m.BUDHUD['sha256'], 'f42f2af1d6469c80a01f093930a0db32f901e0a03bad5aaa1dbe7e17749335c2')

    def test_archive_valve_rc_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arc = root / 'hud.zip'
            arc.write_bytes(archive_bytes())
            hud = m.prepare_hud(arc, root / 'unpacked', 'middlemann')
            self.assertFalse((hud / 'cfg/valve.rc').exists())
            self.assertTrue((hud / 'scripts/hudlayout.res').exists())
            self.assertTrue(m.hud_is_current(hud, 'middlemann'))

    def test_idhud_without_cfg_preserves_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arc = root / 'hud.zip'
            arc.write_bytes(archive_bytes(startup=False))
            hud = m.prepare_hud(arc, root / 'unpacked', 'idhud')
            self.assertFalse((hud / 'cfg').exists())
            self.assertTrue(m.hud_is_current(hud, 'idhud'))

    def test_unexpected_autoexec_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arc = root / 'hud.zip'
            arc.write_bytes(archive_bytes(extra={'cfg/autoexec.cfg': 'fps_max 60'}))
            with self.assertRaises(m.SetupError):
                m.prepare_hud(arc, root / 'unpacked', 'idhud')

    def test_zip_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arc = root / 'hud.zip'
            with zipfile.ZipFile(arc, 'w') as z:
                z.writestr('../escape', 'bad')
            with self.assertRaises(m.SetupError):
                m.extract_hud(arc, root / 'unpacked')
            self.assertFalse((root / 'escape').exists())

    def test_zip_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arc = root / 'hud.zip'
            with zipfile.ZipFile(arc, 'w') as z:
                i = zipfile.ZipInfo('symlink')
                i.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(i, '/tmp')
            with self.assertRaises(m.SetupError):
                m.extract_hud(arc, root / 'unpacked')

    def test_ambiguous_archive_roots_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arc = root / 'hud.zip'
            arc.write_bytes(archive_bytes(extra={'extra/info.vdf': 'fixture', 'extra/resource/a': 'fixture', 'extra/scripts/a': 'fixture'}))
            with self.assertRaises(m.SetupError):
                m.extract_hud(arc, root / 'unpacked')

    def test_checksum_verification_accepts_matching_data(self):
        data = b'Synthetic network fixture, not an actual HUD.'
        response = io.BytesIO(data)
        response.geturl = lambda: 'https://github.com/example/fixture'
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(m.urllib.request, 'urlopen', return_value=response):
            p = Path(tmp) / 'file'
            m.download({'version': 'fixture', 'url': 'https://github.com/example/fixture', 'sha256': hashlib.sha256(data).hexdigest()}, p, 1000)
            self.assertEqual(p.read_bytes(), data)

    def test_checksum_verification_rejects_changed_data(self):
        response = io.BytesIO(b'Bad fixture')
        response.geturl = lambda: 'https://github.com/example/fixture'
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(m.urllib.request, 'urlopen', return_value=response):
            with self.assertRaises(m.SetupError):
                m.download({'version': 'fixture', 'url': 'https://github.com/example/fixture', 'sha256': '0' * 64}, Path(tmp) / 'file', 1000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
