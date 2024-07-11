VERSION = "1.0.1"

from ttkbootstrap import BooleanVar, Menu, StringVar, Toplevel
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs.dialogs import Messagebox, Querybox
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.widgets import (
    Button,
    Checkbutton,
    Combobox,
    DateEntry,
    Entry,
    Frame,
    Label,
    Labelframe,
    Menubutton,
    Progressbar,
    Radiobutton,
    Spinbox,
)


class newLabelFrame(Labelframe):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newCheckButton(Checkbutton):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)

    def set_enabled(self):
        self.configure(state="normal")

    def set_disabled(self):
        self.configure(state="disabled")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_secondary(self):
        self.configure(bootstyle="secondary")

    def set_warning(self):
        self.configure(bootstyle="warning")


class newButton(Button):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bootstyle="secondary")

    def set_enabled(self):
        self.configure(state="normal", bootstyle="secondary")

    def set_disabled(self):
        self.configure(state="disabled", bootstyle="disabled")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newWindowStatus(Toplevel):
    def __init__(self, status_running, **kwargs):
        super().__init__(**kwargs)
        self.geometry("300x500")
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.status_running = status_running
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.text_box = newScrolledText(self)
        self.text_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def ajusta_tamanho(self):
        total_lines = int(self.text_box.index("end-1c").split(".")[0])
        altura = 18 * (total_lines + 1)
        self.geometry(f"400x{altura}")

    def close_window(self):
        if not self.status_running:
            self.destroy()
        else:
            Messagebox.show_info(
                title="Aviso",
                message="Aguarde o término do processo para fechar a janela.",
            )


class newDateEntry(DateEntry):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bootstyle="default")

    def set_enabled(self):
        self.configure(state="normal")

    def set_disabled(self):
        self.configure(state="disabled")

    def clear_date(self):
        self.entry.delete(0, "end")

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_secondary(self):
        self.configure(bootstyle="secondary")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)

    def set_date(self, date_str):
        self.entry.delete(0, "end")
        self.entry.insert(0, date_str)


class newLabelStatus(Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(font=("Consolas", 9))

    def set_bootstyle(self, bootstyle):
        self.configure(bootstyle=bootstyle)

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newLabelTitle(Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(font=("Consolas", 26), anchor="center", bootstyle="default")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)

    def set_tamanho_fonte(self, tamanho):
        self.configure(font=("Consolas", tamanho))


class newEntry(Entry):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.set_default()

    def set_enabled(self):
        self.configure(state="normal")

    def set_disabled(self):
        self.configure(state="disabled")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_readonly(self):
        self.configure(state="readonly")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newCombobox(Combobox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bootstyle="default")

    def set_enabled(self):
        self.configure(state="normal")

    def set_disabled(self):
        self.configure(state="disabled")

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_readonly(self):
        self.configure(state="readonly")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newScrolledText(ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def clear_text(self):
        self.delete("1.0", "end")

    def insert_text(self, text):
        self.insert("end", text)

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)

    def set_max_chars(self, max_chars):
        current_text = self.get("1.0", "end-1c")
        current_text = current_text.replace("\n", " ")
        if len(current_text) > max_chars:
            current_text = current_text[:max_chars]
        self.clear_text()
        self.insert("1.0", current_text)

    def check_if_text(self):
        if self.get("1.0", "end-1c") == "":
            return False
        else:
            return True

    def capt_text(self):
        return self.get("1.0", "end-1c")


class newFrame(Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_secondary(self):
        self.configure(bootstyle="secondary")

    def set_column_weight(self, column, weight):
        self.columnconfigure(column, weight=weight)

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newMenuButton(Menubutton):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_secondary(self):
        self.configure(bootstyle="secondary")

    def set_light(self):
        self.configure(bootstyle="light")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newMenu(Menu):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)


class newProgressBar(Progressbar):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_secondary(self):
        self.configure(bootstyle="secondary")

    def set_light(self):
        self.configure(bootstyle="light")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)


class newSpinBox(Spinbox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_secondary(self):
        self.configure(bootstyle="secondary")

    def set_light(self):
        self.configure(bootstyle="light")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)

    def set_values(self, values: list):
        self.configure(values=values)


class newLabelSubtitle(Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(font=("Consolas", 12), anchor="center")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)

    def set_tamanho_fonte(self, tamanho):
        self.configure(font=("Consolas", tamanho))


class newStringVar(StringVar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class newBooleanVar(BooleanVar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class newRadioButton(Radiobutton):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def set_danger(self):
        self.configure(bootstyle="danger")

    def set_success(self):
        self.configure(bootstyle="success")

    def set_default(self):
        self.configure(bootstyle="default")

    def set_warning(self):
        self.configure(bootstyle="warning")

    def set_secondary(self):
        self.configure(bootstyle="secondary")

    def set_light(self):
        self.configure(bootstyle="light")

    def set_tooltip(self, msg, bootstyle_p=None):
        if bootstyle_p is None:
            ToolTip(self, msg)
        else:
            ToolTip(self, msg, bootstyle=bootstyle_p)

    def set_disabled(self):
        self.configure(state="disabled")

    def set_enabled(self):
        self.configure(state="normal")
