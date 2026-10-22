# Toggle Power FAQ: Linux Battery Charge Limits and Fn+Q Power Profiles

## How do I enable an 80% battery charge limit on a Lenovo laptop running Linux?

On the supported Lenovo Intel / Arch or CachyOS / KDE Plasma Wayland setup, build and install Toggle Power, open **Power & Battery**, and enable **Limit charge to 80%**. The switch controls the Lenovo firmware's `conservation_mode` setting. Disable it to allow a full charge. Follow the [installation guide](../README.md#build-and-install-on-arch-linux-or-cachyos).

## Which laptop has been tested?

The tested laptop is the **Lenovo Slim 7 14ILL10 (83MC)** with an **Intel Core Ultra 200V** CPU. Matching the Lenovo brand alone does not establish compatibility: the installer requires the relevant conservation control, firmware profiles and enabled Intel RAPL constraints. Power limits need review before adapting the project to another model.

## Does it support Ubuntu, GNOME, X11 or AMD laptops?

The current installer and integrated popup target **Arch Linux/CachyOS, KDE Plasma Wayland and Intel CPUs**. Other distributions, desktop environments, display systems and CPU vendors need adaptation and validation. The current installation procedure should be used with the [documented environment](../README.md#compatibility-and-requirements).

## How does Fn+Q detection work on Lenovo Linux laptops?

The firmware changes `/sys/firmware/acpi/platform_profile`. Toggle Power watches that profile and displays the resulting mode. It does not intercept keyboard event devices or implement the firmware hotkey. The laptop's firmware and driver must already expose the profile changes.

## What PL1 and PL2 limits does it apply?

The defaults are **8 W / 17 W** for `low-power`, **24 W / 24 W** for `balanced`, and **37 W / 37 W** for `performance`. The [power service](../src/potencia_servicio.py) applies the long-term and short-term CPU package constraints through available Intel RAPL MSR/MMIO interfaces, then reads back the values. These defaults are specific to the tested model.

## How can I check whether the power limits were applied?

Read the service's verification results:

```sh
cat /run/lenovo-power-modes/status.json
systemctl status lenovo-power-modes.service
```

The JSON contains `perfil` and per-interface `resultados`, including success or error information. Constraint indices are discovered by their `long_term` and `short_term` names. The reported limits are CPU power ceilings; workload determines actual consumption.

## Will these power profiles increase battery runtime?

Battery-runtime improvement has not been established by this project. Toggle Power provides explicit charging and power-limit controls. A useful comparison requires the same workload, brightness, peripherals and background activity across profiles.

## Does the battery switch require a password every time?

Installation requests administrator authorization. It generates a Polkit rule allowing the invoking account to run the battery helper from an **active local session** without another password prompt. The root-owned helper accepts only `0` or `1` for the conservation flag. Other accounts retain the action's authentication defaults. See [the installer](../scripts/install.py) and [the helper](../src/bateria_control.py).

## Why did the battery switch disappear after a KDE or Qt update?

An unsupported upstream version activates the original KDE battery panel and standalone tray control. The reviewed popup currently targets **PowerDevil/Plasma 6.8.0 and Qt 6.12.0**. Arch package-revision changes are accepted; upstream version changes need a reviewed integration update. See [the baseline](../panel-bateria/kde-version.txt) and [the launcher](../scripts/iniciar-panel-bateria.sh).

## How do I use the interface in English or Spanish?

Set the desktop session language and restart the application or session. Spanish regional variants use the Spanish catalog. Other untranslated languages and the C/POSIX message locale use English for the project's own text. Existing KDE controls use KDE's translation catalogs. All project documentation is in English.

## Does Toggle Power require ChatGPT, Claude or an online AI service?

No. Toggle Power is a local Linux desktop utility. ChatGPT and Claude are relevant to finding and reading its public documentation; they are not runtime dependencies or power-control components.

## What changes when I uninstall Toggle Power?

Run `./uninstall.sh` from the repository. It removes managed files and services, restores the original KDE panel and removes the generated battery permission. The battery conservation flag and last applied power limits remain as they were. See [uninstallation](../README.md#uninstall).
