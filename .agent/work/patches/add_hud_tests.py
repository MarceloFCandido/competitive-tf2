from pathlib import Path
p=Path('/mnt/data/test_setup_tf2_bazzite.py'); s=p.read_text().replace('v1.4.0', 'v1.5.0')
s=s.replace("{'keep', 'stock', 'middlemann', 'idhud', 'rayshud', 'budhud'}", "{'keep', 'stock', 'middlemann', 'idhud', 'rayshud', 'budhud',\n                                              'centerhud', 'communityhudfixes', 'maxihud', 'toonhud'}")
extra='''
    def test_centerhud_switch_keeps_baseline_and_exact_restore(self):
        self.install_hud_fixture(customized=True)
        before = self.snapshot(self.tf)
        cfg_before = self.snapshot(self.tf / 'cfg')
        def center(asset, dest, maximum):
            write(dest, archive_bytes('centerhud', {'cfg/joystick.cfg': 'exec center_hud_init',
                                                   'cfg/center_hud_init.cfg': 'fps_max 30'}))
        self.run_main('--update-only', '--hud', 'centerhud', '--replace-hud', downloader=center)
        path = self.tf / 'custom/center-hud'
        self.assertTrue(m.hud_is_current(path, 'centerhud'))
        self.assertFalse((path / 'cfg/joystick.cfg').exists())
        self.assertFalse((path / 'cfg/valve.rc').exists())
        self.assertTrue((path / 'cfg/center_hud_init.cfg').exists())
        self.assertEqual(cfg_before, self.snapshot(self.tf / 'cfg'))
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        m.transact(tf, ops, backup.parent, 'test-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_communityhudfixes_pin_and_idempotence(self):
        self.assertEqual(m.COMMUNITYHUDFIXES['version'], '11.0')
        self.run_main('--update-only', '--hud', 'communityhudfixes')
        self.assertTrue(m.hud_is_current(self.tf / 'custom/tf2hud-fixes', 'communityhudfixes'))
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'communityhudfixes')
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_centerhud_dryrun_makes_no_writes(self):
        self.install_hud_fixture()
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'centerhud', '--replace-hud', '--dry-run')
        self.assertIn('Configuration files: no changes.', result[1])
        self.assertIn('Layout-first', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_local_options_require_explicit_zip(self):
        before = self.snapshot()
        for name in m.LOCAL_HUDS:
            with self.assertRaisesRegex(m.SetupError, 'requires --hud-zip'):
                self.run_main('--update-only', '--hud', name, '--dry-run')
        self.assertEqual(before, self.snapshot())

    def test_local_zip_dryrun_reads_only(self):
        src = self.root / 'chosen theme.zip'
        write(src, archive_bytes('toonhud'))
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'toonhud', '--hud-zip', str(src), '--dry-run')
        self.assertIn('NOT a verified upstream', result[1])
        self.assertIn('Configuration files: no changes.', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_local_zip_install_restore_and_no_network(self):
        self.install_hud_fixture(customized=True)
        src = self.root / 'chosen theme.zip'
        write(src, archive_bytes('toonhud', {'cfg/autoexec.cfg': 'sensitivity 123',
                                            'cfg/user_default.scr': 'settings'}))
        before = self.snapshot(self.tf)
        cfg_before = self.snapshot(self.tf / 'cfg')
        result = self.run_main('--update-only', '--hud', 'toonhud', '--hud-zip', str(src), '--replace-hud')
        self.assertFalse(result[3].called)
        path = self.tf / 'custom/toonhud'
        self.assertFalse((path / 'cfg/autoexec.cfg').exists())
        self.assertFalse((path / 'cfg/user_default.scr').exists())
        self.assertEqual(cfg_before, self.snapshot(self.tf / 'cfg'))
        backup = next(self.state.rglob('manifest.json')).parent
        tf, ops = m.load_restore(backup)
        m.transact(tf, ops, backup.parent, 'test-restore')
        self.assertEqual(before, self.snapshot(self.tf))

    def test_maxihud_local_reapply_same_bytes_is_noop(self):
        src = self.root / 'maxihud-v17.5.zip'
        write(src, archive_bytes('maxihud', {'cfg/user_default.scr': 'defaults'}))
        self.run_main('--update-only', '--hud', 'maxihud', '--hud-zip', str(src))
        before = self.snapshot()
        result = self.run_main('--update-only', '--hud', 'maxihud', '--hud-zip', str(src))
        self.assertIn('Already configured', result[1])
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

    def test_local_different_theme_needs_replace(self):
        src = self.root / 'theme.zip'
        write(src, archive_bytes('toonhud'))
        self.run_main('--update-only', '--hud', 'toonhud', '--hud-zip', str(src))
        write(src, archive_bytes('toonhud', {'resource/theme.res': 'changed'}))
        before = self.snapshot(self.tf)
        with self.assertRaisesRegex(m.SetupError, 'would be replaced'):
            self.run_main('--update-only', '--hud', 'toonhud', '--hud-zip', str(src))
        self.assertEqual(before, self.snapshot(self.tf))

    def test_local_checksum_mismatch_no_writes(self):
        src = self.root / 'theme.zip'
        write(src, archive_bytes('toonhud'))
        before = self.snapshot()
        with self.assertRaisesRegex(m.SetupError, 'SHA-256 mismatch'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(src), '--hud-sha256', '0'*64)
        self.assertEqual(before, self.snapshot())

    def test_local_matching_checksum_accepted(self):
        src = self.root / 'theme.zip'
        write(src, archive_bytes('toonhud'))
        asset = m.resolve_hud_asset(self.args('--hud', 'toonhud', '--hud-zip', str(src),
                                            '--hud-sha256', m.tree_hash(src)))
        self.assertEqual(asset['sha256'], m.tree_hash(src))

    def test_local_checksum_flag_misuse_rejected(self):
        for args in (('--hud-sha256', '0'*64), ('--hud', 'rayshud', '--hud-zip', '/not/a/file')):
            with self.assertRaises(m.SetupError):
                m.resolve_hud_asset(self.args(*args))

    def test_local_invalid_archive_rejected(self):
        src = self.root / 'theme.zip'
        write(src, b'<html>not an archive</html>')
        with self.assertRaisesRegex(m.SetupError, 'not a ZIP'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(src))

    def test_local_symlink_rejected(self):
        src = self.root / 'theme.zip'
        write(src, archive_bytes('toonhud'))
        symlink = self.root / 'linked.zip'
        symlink.symlink_to(src)
        with self.assertRaisesRegex(m.SetupError, 'Symlink'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(symlink))

    def test_local_changed_after_preview_rejected(self):
        src = self.root / 'theme.zip'
        write(src, archive_bytes('toonhud'))
        before = self.snapshot(self.tf)
        old_copy = m.shutil.copyfile
        def changed(source, target, *args, **kwargs):
            if Path(source) == src:
                write(src, archive_bytes('toonhud', {'resource/race.res': 'changed'}))
            return old_copy(source, target, *args, **kwargs)
        with patch.object(m.shutil, 'copyfile', side_effect=changed), \\
             self.assertRaisesRegex(m.SetupError, 'changed after the preview'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(src))
        self.assertEqual(before, self.snapshot(self.tf))

    def test_local_unsafe_zip_no_game_writes(self):
        src = self.root / 'unsafe.zip'
        with zipfile.ZipFile(src, 'w') as z:
            z.writestr('../escape.txt', 'bad')
        before = self.snapshot(self.tf)
        with self.assertRaisesRegex(m.SetupError, 'Unsafe'):
            self.run_main('--hud', 'toonhud', '--hud-zip', str(src))
        self.assertEqual(before, self.snapshot(self.tf))

    def test_new_options_cannot_layer_multiple_huds(self):
        self.install_hud_fixture()
        self.run_main('--hud', 'centerhud', '--replace-hud')
        self.run_main('--hud', 'communityhudfixes', '--replace-hud')
        self.assertEqual([p.name for p in m.hud_candidates(self.tf)], ['tf2hud-fixes'])

    def test_no_args_keeps_existing_new_hud(self):
        self.run_main('--hud', 'centerhud')
        before = self.snapshot()
        result = self.run_main('--update-only')
        self.assertFalse(result[3].called)
        self.assertEqual(before, self.snapshot())

'''
s=s.replace("\nif __name__ == '__main__':", '\n'+extra+"\nif __name__ == '__main__':")
p.write_text(s)
