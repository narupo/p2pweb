import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.scrolledtext import ScrolledText as TkScrolledText


class RootWindow(tk.Tk):
    pass


class Frame(ttk.Frame):
    pass


class Label(ttk.Label):
    pass


class Entry(ttk.Entry):
    pass


class Text(tk.Text):
    pass


class Listbox(tk.Listbox):
    pass


class Combobox(ttk.Combobox):
    pass


class PanedWindow(ttk.PanedWindow):
    pass


class Button(ttk.Button):
    pass


class ScrolledText(TkScrolledText):
    pass


class EntryButton(tk.Frame):
    def __init__(self, master, button_text, button_command):
        super().__init__(master)
        self.entry = Entry(self)
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        Frame(self).pack(side=tk.LEFT, padx=4)

        self.btn = Button(
            self,
            text=button_text,
            command=button_command,
            cursor='hand2',
        )
        self.btn.pack(side=tk.LEFT)

    def get(self):
        return self.entry.get()

    def insert(self, *args, **kwargs):
        self.entry.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.entry.delete(*args, **kwargs)


class AddressBar(EntryButton):
    def __init__(self, master, goto_command):
        super().__init__(
            master,
            button_text='Goto',
            button_command=goto_command,            
        )
