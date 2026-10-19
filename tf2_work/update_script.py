from pathlib import Path
p = Path('/mnt/data/setup_tf2_bazzite.py')
s = p.read_text()
s = s.replace("SCRIPT_VERSION = '1.3.0'", "SCRIPT_VERSION = '1.3.1'")
s = s.replace('    python3 setup_tf2_bazzite.py --update-only --dry-run --hud idhud --replace-hud\n    python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud', '    python3 setup_tf2_bazzite.py --update-only --dry-run --hud middlemann --replace-hud\n    python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud')
s = s.replace('HUDs:\n    --hud idhud', 'HUDs:\n    --hud middlemann installs Middle Mann: TF2-style panels with centered\n    health, ammo and class meters. It does not restore disabled 3D portraits.\n    --hud idhud')
s = s.replace("    IDHUD's optional recommended ConVars are NOT applied by the installer.\n", "    IDHUD's optional recommended ConVars are NOT applied by the installer.\n    Middle Mann expects cl_hud_minmode 0. Its bundled startup override is\n    excluded too: minmode, caching and automatic reload tweaks are NOT applied.\n    If needed, set cl_hud_minmode 0 explicitly in TF2; this is HUD layout mode,\n    not minimal weapon viewmodels. Test rendering on your own display.\n")
s = s.replace('Baseline sources checked 2026-10-18; IDHUD addition checked 2026-10-19:', 'Baseline sources checked 2026-10-18; HUD additions checked 2026-10-19:')
s = s.replace('    https://github.com/idhud-tf2/idhud/blob/4.0.8/README.md\n', '    https://github.com/idhud-tf2/idhud/blob/4.0.8/README.md\n    https://github.com/Vexcenot/-middle-mann/releases/tag/v26.1\n    https://github.com/Vexcenot/-middle-mann/blob/v26.1/cfg/valve.rc\n    https://github.com/Vexcenot/-middle-mann/issues/166\n')
s = s.replace("# Do not silently upgrade the HUDs or mastercomfig from the earlier installer.\nHUDS = {'idhud': IDHUD, 'rayshud': RAYSHUD, 'budhud': BUDHUD}", "MIDDLEMANN = {\n    'version': 'v26.1',\n    'url': 'https://github.com/Vexcenot/-middle-mann/releases/download/v26.1/-middle-mann-v26.1.zip',\n    'sha256': '4cc9721be700e6530f2cb731fae14ddc1d27b2b4c4aa7b42e69a3621513cf899',\n}\n# Do not silently upgrade the HUDs or mastercomfig from the earlier installer.\nHUDS = {'middlemann': MIDDLEMANN, 'idhud': IDHUD, 'rayshud': RAYSHUD, 'budhud': BUDHUD}")
s = s.replace('HUD_DESCRIPTIONS = {\n', "HUD_DESCRIPTIONS = {\n    'middlemann': 'Middle Mann: TF2-style panels with centered health, ammo and class meters.',\n")
s = s.replace('HUD_PAGES = {\n', "HUD_PAGES = {\n    'middlemann': 'https://github.com/Vexcenot/-middle-mann',\n")
s = s.replace("    startup = root / 'cfg/valve.rc'\n", "    if name == 'middlemann' and exists(root / 'cfg'):\n        # The inspected v26.1 source has only valve.rc here. Fail closed on surprises.\n        cfg = root / 'cfg'\n        if not cfg.is_dir() or any(entry.name != 'valve.rc' for entry in cfg.iterdir()):\n            raise SetupError('Unexpected Middle Mann cfg content; refusing startup changes.')\n    startup = root / 'cfg/valve.rc'\n")
s = s.replace("        print(f'{name:<8}{HUD_DESCRIPTIONS[name]}')\n        print(f'        Pinned release: {asset[\"version\"]}; {HUD_PAGES[name]}')", "        print(f'{name:<12}{HUD_DESCRIPTIONS[name]}')\n        print(f'            Pinned release: {asset[\"version\"]}; {HUD_PAGES[name]}')\n        if name == 'middlemann':\n            print('            Expects cl_hud_minmode 0; this installer preserves your current value.')")
s = s.replace('Preview: python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud --dry-run', 'Preview: python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud --dry-run')
s = s.replace("            warn('HUD detection cannot prove compatibility with every renamed/packed custom mod.')", "            if args.hud == 'middlemann':\n                print('Middle Mann expects cl_hud_minmode 0; check it in the TF2 console.')\n                print('Its startup minmode/caching/reload tweaks are NOT applied; no gameplay cvars are reset.')\n                print('Tournament spectator overlap has been reported upstream (#166); test your modes/display.')\n            warn('HUD detection cannot prove compatibility with every renamed/packed custom mod.')")
p.write_text(s)

p=Path('/mnt/data/test_setup_tf2_bazzite.py')
s=p.read_text().replace('v1.3.0.', 'v1.3.1.')
s=s.replace("{'keep', 'stock', 'idhud', 'rayshud', 'budhud'}", "{'keep', 'stock', 'idhud', 'rayshud', 'budhud', 'middlemann'}")
# New tests retain all 48 previous test cases, and use no live network or game.
insert='''    def test_middlemann_dry_run_preserves_everything(self):
        self.install_hud_fixture('rayshud', customized=True)
        write(self.tf / 'cfg/config.cfg', 'cl_hud_minmode 1\\nvolume 0.65\\n')
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
                                    extra={'customizations/vignette.res': '// off\\n',
                                           'cfg/valve.rc': 'cl_hud_minmode 0\\nvgui_cache_res_files 0\\nwait 200; hud_reloadscheme\\n'}))
        root = m.prepare_hud(archive, self.root / 'middlemann-stage', 'middlemann')
        self.assertEqual(root.name, '-middle-mann-v26.1')
        self.assertFalse((root / 'cfg').exists())
        self.assertEqual((root / 'customizations/vignette.res').read_text(), '// off\\n')
        self.assertTrue(m.hud_is_current(root, 'middlemann'))

    def test_middlemann_unexpected_startup_refused(self):
        archive = self.root / 'middlemann-test.zip'
        write(archive, archive_bytes('middlemann', extra={'cfg/joystick.cfg': 'exec bad.cfg'}))
        with self.assertRaisesRegex(m.SetupError, 'Unexpected Middle Mann cfg'):
            m.prepare_hud(archive, self.root / 'middlemann-stage', 'middlemann')

'''
s=s.replace("    def test_catalog_choices_include_previous_and_new(self):", insert+"    def test_catalog_choices_include_previous_and_new(self):")
p.write_text(s)
