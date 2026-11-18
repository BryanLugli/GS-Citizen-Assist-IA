"""Versão de terminal.  python app/cli.py   (digite 'sair' para encerrar)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from citizen_assist.agent import responder  # noqa: E402
from citizen_assist.prompts import MENU, TEXTO_MENU  # noqa: E402

print("Citizen Assist — protótipo educacional. Não digite dados pessoais.\n")
print(TEXTO_MENU)
while True:
    try:
        texto = input("\nVocê: ")
    except (EOFError, KeyboardInterrupt):
        break
    if texto.strip().lower() in {"sair", "exit", "q"}:
        break
    if texto.strip() in MENU:                       # número do menu vira a pergunta-exemplo
        texto = MENU[texto.strip()][1]
        print(f"(pergunta: {texto})")
    print("\nAssistente:", responder(texto)["resposta"])
