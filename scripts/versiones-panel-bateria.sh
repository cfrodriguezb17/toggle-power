#!/usr/bin/env bash
# Shared compatibility check: retain the upstream version and epoch, ignore pkgrel.
versiones_panel_sistema() {
    pacman -Q powerdevil libplasma plasma-workspace qt6-base qt6-declarative
}

versiones_panel_normalizar() {
    awk '
        NF != 2 || $2 !~ /-[0-9]+([.][0-9]+)*$/ { invalid = 1; exit 1 }
        { sub(/-[0-9]+([.][0-9]+)*$/, "", $2); print $1, $2; count++ }
        END { if (invalid || count != 5) exit 1 }
    ' "$@"
}

versiones_panel_comprobar() {
    local actual esperado normalizado
    actual=$(versiones_panel_sistema) || return 1
    esperado=$(versiones_panel_normalizar "$1") || return 1
    normalizado=$(printf '%s\n' "$actual" | versiones_panel_normalizar) || return 1
    [[ "$esperado" == "$normalizado" ]]
}
