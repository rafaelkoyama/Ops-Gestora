import os
import sys

str_user = os.getlogin()
script_name = os.path.basename(sys.argv[0])

sys.path.append(
    f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Processos Python\\Modules"
)

import ttkbootstrap as ttk

from tools.my_logger import Logger

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
