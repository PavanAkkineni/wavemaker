"""The Tooltips class allows you to quickly add a tooltip to any widget.
    To create a tooltip:
        from modules.tooltip import Tooltip


        btn = Button(<ttk frame>, text = 'Click me')
        btn_tip = Tooltip(btn, "tip text")
"""

from tkinter import Label, Toplevel, LEFT, SOLID


class Tooltip(object):

    def __init__(self, widget, text):
        self.widget = widget
        self.x = 0
        self.y = 0
        self.text = text
        self.tipwindow = None
        self.id = None

        def enter(event):
            self.schedule()

        def leave(event):
            self.unschedule()
            self.hide()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(600, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self):
        """Display text in tooltip window."""
        if self.tipwindow or not self.text:
            return
        mouse_x, mouse_y = self.widget.winfo_pointerxy()
        x, y = mouse_x + 5, mouse_y + 10
        self.tipwindow = Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tipwindow, text=self.text, justify=LEFT,
                      background="#e3dc95", relief=SOLID, borderwidth=1)
        label.pack(ipadx=3, ipady=3)

    def hide(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

    def updateText(self, new_text: str):
        """Update tooltip text."""
        self.text = new_text
