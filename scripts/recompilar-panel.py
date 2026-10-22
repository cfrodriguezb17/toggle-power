#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rebuild the user-owned battery applet against installed KDE/Qt, without root."""
import argparse
import fcntl
import gettext
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

PACKAGES = ('powerdevil', 'libplasma', 'plasma-workspace', 'qt6-base', 'qt6-declarative')
PLUGIN = Path('plugins/plasma/applets/org.kde.plasma.battery.so')
_ = gettext.translation('lenovo-modes', localedir='/usr/local/share/locale', fallback=True).gettext


def normalized(text):
    lines = [line.split() for line in text.splitlines()]
    if len(lines) != len(PACKAGES) or any(len(line) != 2 for line in lines):
        raise ValueError('Incomplete KDE/Qt package versions')
    if tuple(line[0] for line in lines) != PACKAGES:
        raise ValueError('Unexpected KDE/Qt package list')
    result = []
    for package, version in lines:
        if not re.search(r'-[0-9]+(?:\.[0-9]+)*$', version):
            raise ValueError('Invalid package version: ' + version)
        result.append((package, version.rsplit('-', 1)[0]))
    return result


def atomic_write(path, contents, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.panel-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as file:
            file.write(contents)
        temporary.chmod(mode)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class Updater:
    def __init__(self, base, cache, run=subprocess.run):
        self.base = Path(base)
        self.cache = Path(cache)
        self.source = self.base / 'source'
        self.run = run

    def versions(self):
        result = self.run(['pacman', '-Q', *PACKAGES], check=True, capture_output=True, text=True, timeout=15)
        normalized(result.stdout)
        return result.stdout

    def signature(self, versions):
        digest = hashlib.sha256(json.dumps(normalized(versions)).encode())
        for path in sorted(self.source.rglob('*')):
            if path.is_file():
                digest.update(str(path.relative_to(self.source)).encode())
                digest.update(path.read_bytes())
        return digest.hexdigest()

    def reload(self):
        active = self.run(['systemctl', '--user', 'is-active', '--quiet', 'plasma-plasmashell.service'],
                          check=False, timeout=15)
        if active.returncode == 0:
            self.run(['systemctl', '--user', '--no-block', 'restart', 'plasma-plasmashell.service'],
                     check=True, timeout=15)
            (self.cache / 'needs-reload').unlink(missing_ok=True)

    def rebuild(self, restart=False, force=False):
        self.cache.mkdir(parents=True, exist_ok=True)
        with (self.cache / 'lock').open('a') as lock:
            # Serializes login and the update timer; never build as root.
            fcntl.flock(lock, fcntl.LOCK_EX)
            if Path('/var/lib/pacman/db.lck').exists():
                raise RuntimeError('Package transaction in progress; retry after it finishes')
            versions = self.versions()
            signature = self.signature(versions)
            state_file = self.cache / 'state.json'
            try:
                state = json.loads(state_file.read_text())
            except (OSError, ValueError):
                state = {}
            try:
                matching = normalized((self.base / 'kde-version.txt').read_text()) == normalized(versions)
            except (OSError, ValueError):
                matching = False
            if not force and matching and (self.base / PLUGIN).is_file() and state.get('success') == signature:
                if restart and (self.cache / 'needs-reload').exists():
                    self.reload()
                return False
            if not force and state.get('failed') == signature:
                raise RuntimeError('This source/package combination already failed; see journal or retry with --force')
            try:
                build = self.cache / 'build'
                print('Toggle Power: rebuilding battery panel for installed KDE/Qt', flush=True)
                self.run(['cmake', '-S', str(self.source), '-B', str(build),
                          '-DCMAKE_BUILD_TYPE=Release', '-DTOGGLE_POWER_PANEL_ONLY=ON'], check=True, timeout=180)
                self.run(['cmake', '--build', str(build), '--parallel', '2'], check=True, timeout=300)
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   XDG_DATA_DIRS=str(build / 'share') + ':/usr/local/share:/usr/share',
                                   QT_PLUGIN_PATH=str(build / 'plugins'), LC_ALL='en_US.UTF-8', LANGUAGE='en')
                self.run(['ctest', '--test-dir', str(build), '--output-on-failure'],
                         check=True, env=environment, timeout=60)
                self.run([str(build / 'panel-bateria/check_applet')], check=True, env=environment, timeout=30)
                self.run([str(build / 'panel-bateria/preview_panel'), str(self.source / 'panel-bateria/preview.qml'),
                          str(self.cache / 'preview.png'), 'Limit charge to 80%'],
                         check=True, env=environment, timeout=30)
                # Package changes during a build invalidate its result.
                if Path('/var/lib/pacman/db.lck').exists() or normalized(self.versions()) != normalized(versions):
                    raise RuntimeError('Packages changed during compilation; result was not installed')
                atomic_write(self.base / PLUGIN, (build / PLUGIN).read_bytes(), 0o755)
                atomic_write(self.base / 'kde-version.txt', versions.encode())
                atomic_write(state_file, json.dumps({'success': signature}).encode())
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                # Avoid recompiling a broken combination every two minutes.
                atomic_write(state_file, json.dumps({'failed': signature}).encode())
                if shutil.which('notify-send'):
                    self.run(['notify-send', '--app-name=Toggle Power', _('Battery panel update failed'),
                              _('KDE will use its standard battery panel. See the Toggle Power update log.')],
                             check=False, timeout=10)
                raise
            if restart:
                self.reload()
            print('Toggle Power: battery panel rebuilt and verified', flush=True)
            return True


def main():
    parser = argparse.ArgumentParser(description='Rebuild the integrated battery control for installed KDE/Qt')
    parser.add_argument('--restart', action='store_true', help='Reload Plasma after a successful rebuild')
    parser.add_argument('--force', action='store_true', help='Retry even if the same package combination failed')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise RuntimeError('The panel must be compiled as the desktop user, never root')
    cache = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'toggle-power/panel'
    try:
        Updater(Path(__file__).resolve().parent, cache).rebuild(args.restart, args.force)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        if not args.restart:
            cache.mkdir(parents=True, exist_ok=True)
            (cache / 'needs-reload').touch()
        raise


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Toggle Power: {error}', flush=True)
        raise SystemExit(1)
