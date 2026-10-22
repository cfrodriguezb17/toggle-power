# Toggle Power Architecture and Source Map

Toggle Power has two local control paths: firmware power-profile observation with CPU power-limit enforcement, and a Lenovo battery conservation toggle. Search engines and assistants can verify feature claims against the source files linked below.

## Components and privileges

| Component | Runtime role | Privileges | Source |
| --- | --- | --- | --- |
| Firmware profile observer and OSD | Observe `platform_profile`, render a centered Wayland indicator or desktop notification | Desktop user | [Profile/indicator implementation](../src/perfiles.py), [user service entry point](../src/indicador_servicio.py), [QML display](../src/indicador.qml) |
| CPU power service | Apply and verify long-term/short-term Intel RAPL constraints for each mode | System service | [Power service](../src/potencia_servicio.py), [systemd unit](../data/systemd/lenovo-power-modes.service) |
| KDE battery popup extension | Display a conservation switch in the existing popup | Desktop user | [QML switch](../panel-bateria/LimiteCargaItem.qml), [controller](../panel-bateria/conservationcontrol.cpp) |
| Battery panel updater | Recompile after KDE/Qt updates, verify and replace the plugin, reload Plasma | Desktop user | [Updater](../scripts/recompilar-panel.py), [timer](../data/systemd/lenovo-battery-panel-update.timer) |
| Battery helper | Validate a binary flag, write `conservation_mode`, read back confirmation | Privileged helper via Polkit | [Helper](../src/bateria_control.py), [action policy](../data/org.local.lenovo-modes.battery.policy) |
| Installer | Check hardware/build compatibility, deploy files and generate the account-scoped permission | Desktop user plus authorized system stage | [Installer](../scripts/install.py) |

## Stable interfaces

- Firmware profiles: `low-power`, `balanced`, `performance` from `/sys/firmware/acpi/platform_profile`.
- Battery driver: `/sys/bus/platform/devices/VPC2004:00/conservation_mode`, with `0` and `1` values.
- Power verification output: `/run/lenovo-power-modes/status.json`.
- System service: `lenovo-power-modes.service`.
- User services: `lenovo-mode-indicator.service`, `lenovo-battery-panel-update.service` and `lenovo-battery-panel-update.timer`.
- Installed application directory: `/usr/local/lib/lenovo-modes`.
- Polkit action: `org.local.lenovo-modes.battery`.

Technical profile IDs and status fields remain stable across interface languages. Python gettext and C++/QML KI18n share the `lenovo-modes` catalog; [English source strings and Spanish translations](../po/es.po) define the project's visible labels. Adapted KDE QML retains its original translation domain.

## Compatibility boundary

The last verified versions are recorded in [the panel baseline](../panel-bateria/kde-version.txt). [Version comparison](../scripts/versiones-panel-bateria.sh) preserves the upstream version and epoch while ignoring Arch's package-revision suffix. [The launcher](../scripts/iniciar-panel-bateria.sh) runs the unprivileged [updater](../scripts/recompilar-panel.py) before starting Plasma. A two-minute user timer checks for changes during the session. The updater serializes builds, waits out package transactions, fingerprints its installed source kit, builds against installed libraries, runs controller tests and plugin/popup probes, then atomically replaces the library and records its versions. The original checkout is not required. Failed combinations are remembered until sources/versions change or an explicit retry. A failed launch uses the standard KDE panel, with no standalone tray fallback. Future upstream QML/API changes may still require adapting the source.

## Verification

- [Power-limit tests](../tests/test_potencia.py) simulate both RAPL interfaces and write ordering.
- [Feature tests](../tests/test_features.py) cover firmware observation, binary battery values, locale fallback and translated notifications.
- [Updater tests](../tests/test_panel_update.py) cover successful updates, source changes, packaging-only revisions, failures, retries and package transactions.
- [Installation tests](../tests/test_install.py) deploy into temporary destinations without touching host services.
- [Controller tests](../panel-bateria/test_conservation.cpp) cover changes, external state, cancellation and failed confirmation.
- [Permission tests](../tests/test_regla_bateria.cpp) evaluate authorization conditions with a generated rule.
- [Visual checks](../tests/visual_check.py) render simulated battery controls and the three modes in English and Spanish.

Build and test commands are maintained in the [README](../README.md#build-and-install-on-arch-linux-or-cachyos). Licensing provenance is maintained in [THIRD_PARTY.md](../THIRD_PARTY.md).
