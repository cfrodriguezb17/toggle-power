# Toggle Power — 80% Battery Charge Limit and Fn+Q Power Profiles for Linux

**Toggle Power** is an open-source desktop utility for **Lenovo Intel laptops running Arch Linux or CachyOS with KDE Plasma on Wayland**. It adds an **80% battery conservation switch** to KDE's battery popup, shows a centered **Fn+Q power-profile indicator**, and applies verified **Intel RAPL PL1/PL2 power limits** for each firmware profile.

## Project at a glance

| Capability | Details |
| --- | --- |
| Battery charge limit | Toggle Lenovo conservation mode between an 80% limit and full charging |
| Power profiles | Observe firmware changes, including Fn+Q, and show an on-screen display (OSD) |
| CPU power control | Apply and verify PL1/PL2 through available Intel RAPL MSR/MMIO interfaces |
| Supported environment | Arch Linux / CachyOS, KDE Plasma, Wayland, supported Lenovo Intel hardware |
| Tested laptop | Lenovo Slim 7 14ILL10 (83MC), Intel Core Ultra 200V |
| Reviewed panel versions | PowerDevil/Plasma 6.8.1 and Qt 6.12.0; automatic rebuilds after updates |
| Interface languages | English and Spanish, selected from the session language |
| Documentation | English |
| License | GPL-3.0-or-later for original code; retained KDE notices for adapted files |

The tested model defines the current hardware scope. Other Lenovo models need matching firmware controls and a review of their power limits before adaptation.

## Documentation

- [Frequently asked questions](docs/FAQ.md): battery charging, Fn+Q, power limits, compatibility and updates.
- [Architecture and source map](docs/ARCHITECTURE.md): components, privileges and implementation references.
- [GitHub publishing and AI-search discoverability](docs/DISCOVERY.md): repository description, topics and crawler guidance.
- [Documentation index for language models](llms.txt): concise project facts and links.
- [Third-party code and licenses](THIRD_PARTY.md).

## Limit Lenovo battery charging to 80% on Linux

After installation, open KDE's **Power & Battery** popup and use **Limit charge to 80%**:

- **Enabled:** activate Lenovo firmware battery conservation mode.
- **Disabled:** allow charging to 100%.

The switch reads back the driver's state after an operation and reports cancellation or failure. The integrated popup is the only battery control; the older standalone tray application has been removed. Installation preserves the current conservation setting.

## Fn+Q power profiles and CPU power limits

The indicator observes `/sys/firmware/acpi/platform_profile`, so it follows the firmware's profile changes without opening keyboard event devices. The firmware handles Fn+Q; Toggle Power displays the resulting profile.

| Firmware profile | Display name | PL1 | PL2 |
| --- | --- | ---: | ---: |
| `low-power` | Power Save | 8 W | 17 W |
| `balanced` | Balanced | 24 W | 24 W |
| `performance` | Performance | 37 W | 37 W |

PL1 and PL2 configure CPU package power ceilings. Actual consumption and battery runtime depend on workload and hardware. These values are the tested defaults for the Lenovo Slim 7 14ILL10; review them before adapting the project to another laptop.

The system service rechecks the limits and records confirmed values in `/run/lenovo-power-modes/status.json`. If the centered renderer is unavailable, the indicator can use a desktop notification.

## Compatibility and requirements

The current installer targets **Arch/CachyOS with KDE Plasma Wayland and Intel CPUs**. It checks Lenovo firmware profiles, `conservation_mode`, and enabled CPU-package Intel RAPL constraints before starting services. AMD processors, other desktops and other distributions need implementation work and validation.

The bundled battery popup originates from PowerDevil 6.8.0 and is verified with **PowerDevil/Plasma 6.8.1 and Qt 6.12.0**. The installer saves a self-contained source kit in `~/.local/share/lenovo-battery-panel/source`. Keep the build dependencies installed: the integration recompiles as your desktop user at login when needed and checks for KDE/Qt updates every two minutes during the session. It waits until the package transaction has finished, builds locally, runs controller tests and checks the plugin and a simulated popup before replacing the integration and reloading Plasma. Arch packaging-only revisions do not trigger a rebuild.

Compilation is a compatibility check, not a guarantee of compatibility with every future KDE interface. A failed build leaves the previous plugin file intact, reports a notification and uses the standard KDE panel at the next launch. The standalone tray control is never started. Failed source/package combinations are not rebuilt repeatedly; a new version or source change retries automatically. No administrator password or network download is needed for these rebuilds.

## Build and install on Arch Linux or CachyOS

Clone [Toggle Power](https://github.com/cfrodriguezb17/toggle-power), then install dependencies, build and run the tests:

```sh
git clone https://github.com/cfrodriguezb17/toggle-power.git
cd toggle-power
sudo pacman -S --needed base-devel cmake extra-cmake-modules gettext python pkgconf qt6-base qt6-declarative libplasma powerdevil ki18n kcoreaddons layer-shell-qt libnotify
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 4
ctest --test-dir build --output-on-failure
./install.sh
```

Run `./install.sh` as your desktop user. It requests administrator authorization for the system files, configures user services and reloads the KDE panel; application windows stay open. Files are installed under `/usr/local/lib/lenovo-modes`. Starting the power service applies the limits for the current profile.

The installer generates a passwordless Polkit rule only for the invoking account's **active local session** and the battery-helper action. The administrator-owned helper accepts only `0` and `1` for Lenovo's `conservation_mode`. Other accounts retain the action's authentication defaults.

## Interface language

Application text follows the session language: **English** or **Spanish**, including Spanish regional variants. English is the fallback for untranslated languages and the C/POSIX message locale. Power-mode labels, headings, notifications and battery controls share the `lenovo-modes` gettext/KI18n catalog. Existing KDE controls retain their KDE translations.

Restart the application or session after changing language. Edit translations in `po/es.po` and rebuild to compile and validate the catalog. `scripts/update-translations.sh` refreshes the template and merges the Spanish catalog. Project documentation is maintained in English.

## Uninstall

```sh
./uninstall.sh
```

This removes the project's installed files and services, restores the original KDE panel and removes the generated permission. It preserves the battery conservation setting and the last applied power limits. Empty installation directories may remain.

## Troubleshooting

```sh
systemctl status lenovo-power-modes.service
systemctl --user status lenovo-mode-indicator.service plasma-plasmashell.service
systemctl --user status lenovo-battery-panel-update.timer
journalctl --user -u lenovo-battery-panel-update.service -b
cat /run/lenovo-power-modes/status.json
cat /sys/bus/platform/devices/VPC2004:00/conservation_mode
```

To retry a failed compilation after correcting the cause:

```sh
python3 -B ~/.local/share/lenovo-battery-panel/recompilar-panel.py --force --restart
```

The conservation control reports `1` when enabled and `0` when disabled. The status JSON reports the firmware profile and verification results for each available power interface. See the [FAQ](docs/FAQ.md) for update fallback behavior and hardware limitations.

## Tests and development

CTest covers simulated power limits, firmware changes, battery operations, authorization rules, locale selection, notification translations, compatibility and staged installation/removal. Offscreen visual checks use mock controls:

```sh
python3 -B tests/visual_check.py
```

Images are written under `build/previews/`. To test the installed file layout without changing host services or hardware:

```sh
./install.sh --destdir /tmp/lenovo-modes-stage --user demo --home /home/demo
./uninstall.sh --destdir /tmp/lenovo-modes-stage --user demo --home /home/demo
```

`--destdir` is a file-staging mode: it skips host hardware checks and never invokes the service manager. [The source map](docs/ARCHITECTURE.md) links the implementation and tests.

## License and source history

Original code is **GPL-3.0-or-later**; see [LICENSE](LICENSE). Adapted KDE files retain their original notices; see [THIRD_PARTY.md](THIRD_PARTY.md) and `LICENSES/`.

Local experiments and the earlier project snapshot are kept in `local-backup/`, excluded from Git together with build outputs, caches and personal diagnostics. Preparing this source tree does not change an already installed copy.
