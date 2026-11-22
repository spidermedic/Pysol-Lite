"""Stand-in for upstream PySolFC's pysollib.mygettext.

This project dropped translations, so the Kivy UI (copied from upstream,
which calls _() everywhere) just gets the original string back.
"""


def _(message):
    return message


def n_(message):
    return message
