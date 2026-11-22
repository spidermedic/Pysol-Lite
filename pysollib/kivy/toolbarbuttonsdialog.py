"""Placeholder for the toolbar button chooser of the Tk UI.

The Kivy toolbar is not customised this way; the dialog reports "cancelled"
so Options > Toolbar buttons does nothing."""


class ToolbarButtonsDialog:
    def __init__(self, parent, title, app, **kw):
        self.status = 1
        self.button = 1
        self.visible = {}
