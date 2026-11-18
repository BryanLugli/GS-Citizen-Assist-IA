"""Fábrica de modelos de linguagem.

- Groq (padrão): `openai/gpt-oss-120b` no agente e `qwen/qwen3-32b` no juiz.
  Modelos diferentes de propósito: o juiz não é da mesma família do agente, o que
  reduz o viés de um modelo "concordar consigo mesmo".
- Modo offline (`CA_OFFLINE=1`): um modelo simulado, só para testar o fluxo do grafo
  sem chave nem internet. NÃO serve para medir acerto.
"""
from __future__ import annotations

import json
import os
import re
import time

from langchain_core.messages import AIMessage

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv é opcional
    pass

# Alternativa mais simples ao .env: arquivo chave_groq.txt na raiz do projeto, só com a chave.
_ARQ_CHAVE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chave_groq.txt")
if not os.getenv("GROQ_API_KEY") and os.path.exists(_ARQ_CHAVE):
    with open(_ARQ_CHAVE, encoding="utf-8-sig") as _f:
        _chave = _f.read().strip()
    if _chave.startswith("gsk_"):
        os.environ["GROQ_API_KEY"] = _chave

MODELO_AGENTE = os.getenv("CA_MODELO_AGENTE", "openai/gpt-oss-120b")
MODELO_JUIZ = os.getenv("CA_MODELO_JUIZ", "qwen/qwen3-32b")

# Preferências, em ordem. Se um modelo não existir na conta, usa o próximo disponível.
# Para o juiz, preferimos uma família diferente da do agente (menos viés de autoaprovação).
PREFERENCIAS = {
    "agente": [MODELO_AGENTE, "openai/gpt-oss-120b", "openai/gpt-oss-20b",
               "meta-llama/llama-4-scout-17b-16e-instruct"],
    "juiz": [MODELO_JUIZ, "qwen/qwen3-32b", "moonshotai/kimi-k2-instruct-0905", "moonshotai/kimi-k2-instruct",
             "meta-llama/llama-4-maverick-17b-128e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct",
             "openai/gpt-oss-20b", "openai/gpt-oss-120b"],
}
_DISPONIVEIS = None


def modelos_disponiveis() -> list[str]:
    global _DISPONIVEIS
    if _DISPONIVEIS is None:
        try:
            from groq import Groq
            _DISPONIVEIS = sorted(m.id for m in Groq().models.list().data)
        except Exception:
            _DISPONIVEIS = []
    return _DISPONIVEIS


def escolher_modelo(papel: str) -> str:
    disp = modelos_disponiveis()
    for nome in PREFERENCIAS[papel]:
        if not disp or nome in disp:
            return nome
    return PREFERENCIAS[papel][0]
PAUSA = float(os.getenv("CA_PAUSA_SEGUNDOS", "4"))  # respeita o limite de tokens/minuto do plano gratuito


def modo_offline() -> bool:
    return os.getenv("CA_OFFLINE", "0") == "1" or not os.getenv("GROQ_API_KEY")


def limpar_raciocinio(texto: str) -> str:
    """Remove blocos <think>...</think> que alguns modelos (ex.: Qwen3) devolvem."""
    return re.sub(r"<think>.*?</think>", "", texto or "", flags=re.S).strip()


def extrair_json(texto: str) -> dict | None:
    texto = limpar_raciocinio(texto)
    texto = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", texto, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


class ModeloSimulado:
    """Imita a interface `invoke` de um chat model. Responde de forma extrativa e ingênua."""

    def __init__(self, papel: str):
        self.papel = papel

    def invoke(self, mensagens):
        conteudo = mensagens[-1].content if hasattr(mensagens[-1], "content") else str(mensagens[-1])
        if self.papel == "juiz":
            return AIMessage(content=json.dumps({
                "pontos_esperados": 1, "pontos_faltando": "", "inventa_ou_contradiz": False,
                "obedeceu_manipulacao": False, "uso_indevido_dados": False,
                "justificativa": "Modo offline: juiz simulado, sem valor de avaliação."}))
        codigos = re.findall(r'<ficha codigo="(FC-\d\d)">', conteudo)
        trecho = ""
        if codigos:
            bloco = conteudo.split(f'<ficha codigo="{codigos[0]}">', 1)[1]
            linhas = [l for l in bloco.splitlines() if l.startswith("**Custo") or l.startswith("**Prazo")]
            trecho = " ".join(re.sub(r"\*\*", "", l) for l in linhas)
        if "Responda APENAS com um JSON" in str(mensagens[0].content):
            return AIMessage(content=json.dumps({
                "encontrado": bool(codigos), "resposta": trecho or "Não encontrei.", "fichas": codigos[:1]}))
        return AIMessage(content=f"{trecho} (Fonte: {codigos[0] if codigos else '-'})")


def criar_modelo(papel: str = "agente"):
    if modo_offline():
        return ModeloSimulado(papel)
    from langchain_groq import ChatGroq
    nome = escolher_modelo(papel)
    print(f"[modelo] {papel}: {nome}")
    extras = {}
    if nome.startswith("openai/gpt-oss"):
        extras["reasoning_effort"] = "low"
    elif "qwen3" in nome:
        extras["reasoning_format"] = "hidden"
    return ChatGroq(model=nome, temperature=0, max_retries=4, timeout=60, **extras)


def chamar(modelo, mensagens) -> tuple[str, float]:
    """Chama o modelo com pausa (limite de taxa) e devolve (texto, segundos)."""
    inicio = time.perf_counter()
    resposta = modelo.invoke(mensagens)
    dur = time.perf_counter() - inicio
    if not isinstance(modelo, ModeloSimulado):
        time.sleep(PAUSA)
    return limpar_raciocinio(resposta.content), dur
