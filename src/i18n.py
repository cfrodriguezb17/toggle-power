# SPDX-License-Identifier: GPL-3.0-or-later
"""One gettext domain shared by the Python, C++ and QML interfaces."""
import gettext
import os
from pathlib import Path

DOMAIN = "lenovo-modes"


def translations():
    # Match GNU/KI18n: the C/POSIX message locale deliberately selects source text.
    message_locale = next((os.environ[key] for key in ('LC_ALL', 'LC_MESSAGES', 'LANG') if os.environ.get(key)), '')
    if message_locale in ('C', 'POSIX', 'C.UTF-8', 'C.utf8'):
        return gettext.NullTranslations()
    development = Path(__file__).resolve().parent.parent / "build/share/locale"
    directory = os.environ.get("LENOVO_MODES_LOCALE_DIR")
    if not directory:
        directory = str(development if development.is_dir() else Path("/usr/local/share/locale"))
    return gettext.translation(DOMAIN, localedir=directory, fallback=True)
