"""Interface web acessível (Flask). Rode:  python app/web.py   e abra http://127.0.0.1:5000

Privacidade: nada é gravado. Não há banco, arquivo de histórico nem log do conteúdo
das mensagens. O histórico aparece só na tela do navegador e some ao recarregar.
"""
import logging
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from citizen_assist.agent import responder  # noqa: E402
from citizen_assist.prompts import MENU  # noqa: E402

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.WARNING)   # sem log de requisições


@app.get("/")
def inicio():
    return render_template("index.html", menu=MENU)


@app.post("/api/perguntar")
def perguntar():
    dados = request.get_json(silent=True) or {}
    mensagem = str(dados.get("mensagem", ""))[:5000]
    try:
        resposta = responder(mensagem, "v2")["resposta"]
    except Exception:  # nunca mostra erro técnico ao cidadão
        resposta = ("Tive um problema para responder agora. Tente de novo em alguns segundos "
                    "ou escolha um assunto no menu.")
    return jsonify({"resposta": resposta})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
