#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install/remove explicit project files; --destdir never operates on services."""
import argparse
import gettext
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
_message_locale = next((os.environ[key] for key in ('LC_ALL', 'LC_MESSAGES', 'LANG') if os.environ.get(key)), '')
_catalog = gettext.NullTranslations() if _message_locale in ('C', 'POSIX', 'C.UTF-8', 'C.utf8') else gettext.translation(
    'lenovo-modes', localedir=ROOT / 'build/share/locale', fallback=True)
_ = _catalog.gettext
RUNTIME = Path('/usr/local/lib/lenovo-modes')
PROFILE = Path('/sys/firmware/acpi/platform_profile')
BATTERY = Path('/sys/bus/platform/devices/VPC2004:00/conservation_mode')
PACKAGES = ('powerdevil', 'libplasma', 'plasma-workspace', 'qt6-base', 'qt6-declarative')
ACTION = 'org.local.lenovo-modes.battery'


def battery_rule(user):
    return ('// Lenovo Modes: active local session only.\n'
            'polkit.addRule(function(action, subject) {\n'
            f'    if (action.id === "{ACTION}" &&\n'
            f'        subject.user === {json.dumps(user)} && subject.local && subject.active) {{\n'
            '        return polkit.Result.YES;\n    }\n});\n')


def check_hardware(sysroot=Path('/sys')):
    if 'lenovo' not in (sysroot / 'class/dmi/id/sys_vendor').read_text().lower():
        raise RuntimeError(_('This version supports Lenovo computers only.'))
    if 'GenuineIntel' not in Path('/proc/cpuinfo').read_text():
        raise RuntimeError(_('This version supports Intel CPUs only.'))
    profiles = set((sysroot / 'firmware/acpi/platform_profile_choices').read_text().split())
    if not {'low-power', 'balanced', 'performance'} <= profiles:
        raise RuntimeError(_('The firmware must provide low-power, balanced and performance profiles.'))
    if (sysroot / BATTERY.relative_to('/sys')).read_text().strip() not in ('0', '1'):
        raise RuntimeError(_('Lenovo conservation_mode is unavailable.'))
    if not (sysroot / PROFILE.relative_to('/sys')).is_file():
        raise RuntimeError(_('The firmware profile is unavailable.'))
    found = False
    for name in ('intel-rapl:0', 'intel-rapl-mmio:0'):
        zone = sysroot / 'class/powercap' / name
        if not zone.exists():
            continue
        names = {p.read_text().strip() for p in zone.glob('constraint_*_name')}
        if not {'long_term', 'short_term'} <= names or (zone / 'enabled').read_text().strip() != '1':
            raise RuntimeError(_('%s: both PL1/PL2 constraints must be enabled.') % name)
        found = True
    if not found:
        raise RuntimeError(_('No supported CPU package RAPL interface found.'))


def compatible(expected):
    script = ROOT / 'scripts/versiones-panel-bateria.sh'
    subprocess.run(['bash', '-c', 'source "$1"; versiones_panel_comprobar "$2"',
                    'versions', str(script), str(expected)], check=True)


def check_build():
    for file in ('lenovo-bateria', 'plugins/plasma/applets/org.kde.plasma.battery.so',
                 'share/locale/es/LC_MESSAGES/lenovo-modes.mo', 'kde-version.txt'):
        if not (ROOT / 'build' / file).is_file():
            raise RuntimeError(_('Build first: cmake -S . -B build && cmake --build build'))
    compatible(ROOT / 'panel-bateria/kde-version.txt')
    compatible(ROOT / 'build/kde-version.txt')


def system_files():
    files = [(ROOT / 'src' / name, RUNTIME / name, 0o644) for name in
             ('potencia_servicio.py', 'indicador_servicio.py', 'indicador.qml', 'perfiles.py', 'i18n.py')]
    files += [(ROOT / 'src/bateria_control.py', RUNTIME / 'bateria-control', 0o755),
              (ROOT / 'build/lenovo-bateria', RUNTIME / 'lenovo-bateria', 0o755),
              (ROOT / 'data/org.local.lenovo-modes.battery.policy',
               Path('/usr/share/polkit-1/actions/org.local.lenovo-modes.battery.policy'), 0o644),
              (ROOT / 'data/lenovo-bateria.desktop', Path('/usr/local/share/applications/lenovo-bateria.desktop'), 0o644),
              (ROOT / 'data/systemd/lenovo-power-modes.service', Path('/etc/systemd/system/lenovo-power-modes.service'), 0o644),
              (ROOT / 'build/share/locale/es/LC_MESSAGES/lenovo-modes.mo',
               Path('/usr/local/share/locale/es/LC_MESSAGES/lenovo-modes.mo'), 0o644)]
    return files


class Deployment:
    def __init__(self, destdir=None):
        self.stage = Path(destdir).resolve() if destdir else None
        if self.stage == Path('/'):
            raise RuntimeError(_('--destdir must be a temporary directory, never /.'))

    def path(self, path):
        return self.stage / Path(path).relative_to('/') if self.stage else Path(path)

    def write(self, path, data, mode=0o644, administrator=False):
        target = self.path(path)
        if administrator and not self.stage:
            for parent in (target, *target.parents):
                if parent.is_symlink() or (parent.exists() and (parent.stat().st_uid != 0 or parent.stat().st_mode & 0o022)):
                    raise RuntimeError(_('Administrator-owned, protected path required: %s') % parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.lenovo-new')
        # Do not follow an unexpected pre-existing temporary symlink.
        created = False
        try:
            with temporary.open('xb') as file:
                created = True
                file.write(data if isinstance(data, bytes) else data.encode())
            os.chmod(temporary, mode)
            if administrator and not self.stage:
                os.chown(temporary, 0, 0)
            temporary.replace(target)
        finally:
            if created:
                temporary.unlink(missing_ok=True)

    def copy(self, source, target, mode=0o644, administrator=False):
        self.write(target, source.read_bytes(), mode, administrator)

    def remove(self, path):
        target = self.path(path)
        if target.is_symlink():
            raise RuntimeError(_('Refusing to remove an unexpected symlink: %s') % target)
        target.unlink(missing_ok=True)

    def run(self, *command):
        if not self.stage:
            subprocess.run(command, check=True)

    def system(self, operation, user):
        rule = Path('/etc/polkit-1/rules.d/49-lenovo-battery.rules')
        if self.path(rule).exists() and self.path(rule).read_text() != battery_rule(user):
            raise RuntimeError(_('The battery permission was edited or belongs to another account; review it first.'))
        if operation == 'install':
            for source, target, mode in system_files():
                self.copy(source, target, mode, administrator=True)
            self.write(rule, battery_rule(user), administrator=True)
            self.run('systemctl', 'daemon-reload')
            self.run('systemctl', 'enable', '--now', 'lenovo-power-modes.service')
            self.run('systemctl', 'restart', 'lenovo-power-modes.service')
        else:
            self.run('systemctl', 'disable', '--now', 'lenovo-power-modes.service')
            # Only remove this project's rule, never an administrator's edited policy.
            if self.path(rule).exists() and self.path(rule).read_text() != battery_rule(user):
                raise RuntimeError(_('The battery permission was edited; remove it manually.'))
            self.remove(rule)
            for source_unused, target, mode_unused in system_files():
                self.remove(target)
            self.run('systemctl', 'daemon-reload')

    def session(self, operation, home):
        config = home / '.config/systemd/user'
        data = home / '.local/share/lenovo-battery-panel'
        override = config / 'plasma-plasmashell.service.d/60-lenovo-battery-panel.conf'
        files = [(ROOT / 'scripts/iniciar-panel-bateria.sh', data / 'iniciar-panel-bateria.sh', 0o755),
                 (ROOT / 'scripts/versiones-panel-bateria.sh', data / 'versiones-panel-bateria.sh', 0o644),
                 (ROOT / 'build/kde-version.txt', data / 'kde-version.txt', 0o644),
                 (ROOT / 'build/plugins/plasma/applets/org.kde.plasma.battery.so',
                  data / 'plugins/plasma/applets/org.kde.plasma.battery.so', 0o755)]
        for service in ('lenovo-mode-indicator.service', 'lenovo-battery-tray.service'):
            files.append((ROOT / 'data/systemd' / service, config / service, 0o644))
        if self.path(override).exists() and '# Lenovo battery panel' not in self.path(override).read_text():
            raise RuntimeError(_('An unrelated Plasma override already exists.'))
        if operation == 'install':
            for source, target, mode in files:
                self.copy(source, target, mode)
            # systemd specifiers and quotes must remain literal in the executable path.
            executable = str(data / 'iniciar-panel-bateria.sh').replace('%', '%%').replace('\\', '\\\\').replace('"', '\\"')
            self.write(override, '# Lenovo battery panel\n[Service]\nExecStart=\nExecStart="' + executable + '"\n')
            self.run('systemctl', '--user', 'daemon-reload')
            self.run('systemctl', '--user', 'enable', '--now', 'lenovo-mode-indicator.service')
            self.run('systemctl', '--user', 'disable', '--now', 'lenovo-battery-tray.service')
            try:
                self.run('systemctl', '--user', 'restart', 'plasma-plasmashell.service')
                if not self.stage:
                    pid = subprocess.check_output(['systemctl', '--user', 'show', 'plasma-plasmashell.service',
                                                   '-p', 'MainPID', '--value'], text=True).strip()
                    plugin = str(data / 'plugins/plasma/applets/org.kde.plasma.battery.so')
                    for attempt in range(20):
                        if plugin in Path(f'/proc/{pid}/maps').read_text():
                            break
                        time.sleep(0.5)
                    else:
                        raise RuntimeError(_('KDE did not load the battery integration.'))
            except (OSError, RuntimeError, subprocess.SubprocessError):
                self.remove(override)
                self.run('systemctl', '--user', 'daemon-reload')
                self.run('systemctl', '--user', 'restart', 'plasma-plasmashell.service')
                self.run('systemctl', '--user', 'start', 'lenovo-battery-tray.service')
                raise RuntimeError(_('The original panel and standalone battery control were restored.'))
        else:
            for service in ('lenovo-mode-indicator.service', 'lenovo-battery-tray.service'):
                self.run('systemctl', '--user', 'disable', '--now', service)
            self.remove(override)
            for source_unused, target, mode_unused in files:
                self.remove(target)
            self.run('systemctl', '--user', 'daemon-reload')
            self.run('systemctl', '--user', 'restart', 'plasma-plasmashell.service')


def main():
    parser = argparse.ArgumentParser(description=_('Install or remove Toggle Power.'))
    parser.add_argument('operation', choices=['install', 'uninstall'])
    parser.add_argument('--destdir', type=Path, help=_('Stage files only; never change the host or services'))
    parser.add_argument('--user', help=_('Target account (staging only)'))
    parser.add_argument('--home', type=Path, help=_('Target home (staging only)'))
    parser.add_argument('--system', type=int, metavar='UID', help=argparse.SUPPRESS)
    args = parser.parse_args()
    deployment = Deployment(args.destdir)
    if args.destdir:
        if args.system is not None:
            raise RuntimeError(_('--system cannot be combined with --destdir'))
        home = args.home or Path('/home/demo')
        if not home.is_absolute() or '..' in home.parts:
            raise RuntimeError(_('An absolute target home without traversal is required.'))
        check_build() if args.operation == 'install' else None
        deployment.system(args.operation, args.user or 'demo')
        deployment.session(args.operation, home)
    elif args.system is not None:
        if os.geteuid() != 0 or int(os.environ.get('PKEXEC_UID', '-1')) != args.system or args.system == 0:
            raise RuntimeError(_('The system stage must be authorized by the invoking user.'))
        user = pwd.getpwuid(args.system).pw_name
        if args.operation == 'install':
            check_build(); check_hardware()
        deployment.system(args.operation, user)
    else:
        if args.user or args.home or os.geteuid() == 0:
            raise RuntimeError(_('Run as your desktop user, without sudo. --user/--home are staging-only.'))
        account = pwd.getpwuid(os.getuid())
        home = Path(account.pw_dir)
        if args.operation == 'install':
            if os.environ.get('XDG_SESSION_TYPE') != 'wayland' or 'KDE' not in os.environ.get('XDG_CURRENT_DESKTOP', '').upper():
                raise RuntimeError(_('Install from a KDE Plasma Wayland session.'))
            check_build(); check_hardware()
        # Preflight the owned override before making any system changes.
        override = home / '.config/systemd/user/plasma-plasmashell.service.d/60-lenovo-battery-panel.conf'
        if override.exists() and '# Lenovo battery panel' not in override.read_text():
            raise RuntimeError(_('An unrelated Plasma override already exists.'))
        if args.operation == 'uninstall':
            deployment.session(args.operation, home)
        subprocess.run(['pkexec', '/usr/bin/python3', '-I', str(Path(__file__).resolve()),
                        args.operation, '--system', str(os.getuid())], check=True)
        if args.operation == 'install':
            deployment.session(args.operation, home)
    print(_('Installation complete.') if args.operation == 'install' else _('Uninstalled. Battery conservation was not changed.'))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Toggle Power: {error}', file=sys.stderr)
        sys.exit(1)
