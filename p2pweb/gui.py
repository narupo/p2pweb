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

    def bind(self, *args, **kwargs):
        self.entry.bind(*args, **kwargs)


class AddressBar(EntryButton):
    def __init__(self, master, goto_command):
        super().__init__(
            master,
            button_text='Goto',
            button_command=goto_command,            
        )


class ScrolledListbox(Listbox):
    def __init__(self, master=None, **kw):
        name = kw.get("name")
        if name is None:
            name = ""
        self.frame = Frame(master, name=name)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.vbar = tk.Scrollbar(self.frame)
        self.vbar.grid(row=0, column=1, sticky="NWS")
        self.hbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.hbar.grid(row=1, column=0, sticky="SWE")

        kw.update({'yscrollcommand': self.vbar.set})
        kw.update({'xscrollcommand': self.hbar.set})
        Listbox.__init__(self, self.frame, **kw)
        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.vbar['command'] = self.yview
        self.hbar['command'] = self.xview

        text_meths = vars(Listbox).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(text_meths)
        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))
    
    def forget_hbar(self):
        self.hbar.grid_forget()

    def __str__(self):
        return str(self.frame)