import tkinter as tk
from tkinter import ttk
from tkinter import *


class RootWindow(tk.Tk):
    pass


class Frame(tk.Frame):
    pass


class Label(tk.Label):
    pass


class Entry(tk.Entry):
    pass


class Text(tk.Text):
    pass


class Listbox(tk.Listbox):
    pass


class Combobox(ttk.Combobox):
    pass


class PanedWindow(tk.PanedWindow):
    pass


class Button(tk.Button):
    pass


class EntryButton(tk.Frame):
    def __init__(self, master, button_text, button_command):
        super().__init__(master)
        self.address_entry = Entry(self)
        self.address_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        Frame(self).pack(side=tk.LEFT, padx=4)

        self.goto_btn = Button(
            self,
            text=button_text,
            command=button_command,
        )
        self.goto_btn.pack(side=tk.LEFT)

    def get(self):
        return self.address_entry.get()


class AddressBar(tk.Frame):
    def __init__(self, master, goto_command):
        super().__init__(master)
        self.address_entry = Entry(self)
        self.address_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        Frame(self).pack(side=tk.LEFT, padx=4)

        self.goto_btn = Button(
            self,
            text='Goto',
            command=goto_command,
        )
        self.goto_btn.pack(side=tk.LEFT)

    def get(self):
        return self.address_entry.get()

