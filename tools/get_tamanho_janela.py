import os

import ttkbootstrap as ttk
from __init__ import append_paths

append_paths()

from tools.my_logger import Logger  # noqa: E402

script_name = os.path.basename(__file__)

root = ttk.Window(themename="darkly")
root.title("Capturar Tamanho da Janela")
root.geometry("300x175")
logger = Logger(nome_script_original=script_name)


def capturar_tamanho_janela():
    largura = root.winfo_width()
    altura = root.winfo_height()
    print(f"Largura: {largura}, Altura: {altura}")
    logger.critical(f"Largura: {largura}, Altura: {altura}")


button = ttk.Button(root, text="Capturar Tamanho", command=capturar_tamanho_janela)
button.pack(pady=20)

prog_bar = ttk.Progressbar(
    root, mode="indeterminate", style="info.Horizontal.TProgressbar"
)
prog_bar.pack(pady=20)

prog_bar.start(10)

root.mainloop()
