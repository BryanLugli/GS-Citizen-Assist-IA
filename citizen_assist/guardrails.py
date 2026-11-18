"""Validações determinísticas (sem IA): entradas inválidas, dados pessoais e prompt injection.

Tudo aqui é regra explícita e testável. A IA só entra depois que a mensagem passou por
estes filtros, e recebe o texto já sem dados pessoais.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .knowledge import normalizar, termos_conhecidos

LIMITE_CARACTERES = 500

# ---------------------------------------------------------------- dados pessoais
# Ordem importa: padrões mais específicos primeiro.
PADROES_PII: list[tuple[str, str, re.Pattern]] = [
    ("e-mail", "[E-MAIL REMOVIDO]", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("CPF", "[CPF REMOVIDO]", re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}[-\s]?\d{2}(?!\d)")),
    ("telefone", "[TELEFONE REMOVIDO]",
     re.compile(r"(?<!\d)(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}(?!\d)")),
    ("CEP", "[CEP REMOVIDO]", re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)")),
    ("RG", "[RG REMOVIDO]", re.compile(r"(?<!\d)\d{1,2}\.\d{3}\.\d{3}-?[\dxX](?!\d)")),
    ("endereço", "[ENDEREÇO REMOVIDO]",
     re.compile(r"(?i)\b(?:rua|r\.|avenida|av\.|travessa|alameda|estrada|rodovia|praça)\s+[^,\n]{2,40}?,?\s*(?:n[ºo°]?\.?\s*)?\d+")),
    ("nome", "[NOME REMOVIDO]",
     re.compile(r"(?i)\b(meu nome (?:é|e)|me chamo)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wáéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wáéíóúâêôãõç]+)*)")),
    ("número de documento", "[NÚMERO REMOVIDO]", re.compile(r"(?<!\d)\d{7,}(?!\d)")),
]

# Intenção de enviar dados pessoais sem enviar (ex.: "vou te passar meu endereço").
INTENCAO_PII = re.compile(
    r"(?i)\b(vou (te )?(passar|mandar|enviar|informar)|segue|anota|aqui est[aá])\b.{0,40}"
    r"\b(meu|minha|meus|minhas)\b.{0,20}\b(endere[cç]o|telefone|celular|e-?mail|cpf|rg|nome|dados|cnh|t[ií]tulo)"
)


def mascarar_pii(texto: str) -> tuple[str, list[str]]:
    """Substitui dados pessoais por marcadores. Retorna (texto_mascarado, tipos_encontrados)."""
    encontrados: list[str] = []
    for tipo, marcador, padrao in PADROES_PII:
        if tipo == "nome":
            novo = padrao.sub(lambda m: f"{m.group(1)} {marcador}", texto)
        else:
            novo = padrao.sub(marcador, texto)
        if novo != texto:
            encontrados.append(tipo)
            texto = novo
    return texto, encontrados


def contem_pii(texto: str) -> bool:
    return bool(mascarar_pii(texto)[1])


# ---------------------------------------------------------------- prompt injection
PADROES_INJECTION = [
    r"ignor\w*\s+(as\s+|todas\s+as\s+)?(instru|regras|orienta)",
    r"desconsider\w*\s+(as\s+|todas\s+as\s+)?(instru|regras)",
    r"esque[cç]\w*\s+(as\s+|tudo|suas)",
    r"prompt\s+(de\s+)?sistema|system\s+prompt|instru[cç][oõ]es\s+(internas|do\s+sistema|iniciais)",
    r"\[\s*(sistema|system|admin|developer|desenvolvedor)\s*\]",
    r"nova\s+regra|regra\s+nova|a\s+partir\s+de\s+agora",
    r"voc[eê]\s+agora\s+[eé]|finja\s+(que|ser)|aja\s+como|modo\s+(desenvolvedor|dev|admin)",
    r"jailbreak|DAN\b",
    r"(mostre|revele|imprima|repita)\s+(o\s+|seu\s+|suas\s+)?(prompt|instru|configura)",
]
_RE_INJECTION = re.compile("|".join(PADROES_INJECTION), re.IGNORECASE)


def detectar_injection(texto: str) -> bool:
    return bool(_RE_INJECTION.search(texto))


# ---------------------------------------------------------------- texto sem sentido
_VOGAIS = set("aeiou")
_PALAVRAS_COMUNS = set("""
a o e as os um uma de do da dos das em no na nos nas para pra por com sem que qual quais
quanto quanta quantos quando como onde porque por que eu meu minha voce voces vc preciso
posso pode tem ter tirar fazer pedir custa custo prazo demora tempo documento documentos
oi ola bom dia boa tarde noite obrigado obrigada ajuda menu sim nao
""".split())
_TERMOS = None


def _palavra_valida(p: str) -> bool:
    global _TERMOS
    if _TERMOS is None:
        _TERMOS = termos_conhecidos()
    if p in _PALAVRAS_COMUNS or p in _TERMOS:
        return True
    if len(p) < 3 or not any(c in _VOGAIS for c in p):
        return False
    if re.search(r"[^aeiou]{4,}", p):          # "asdfgh": consoantes demais seguidas
        return False
    if re.search(r"(.)\1{2,}", p):             # "aaaa", "kkkk"
        return False
    return True


def parece_sem_sentido(texto: str) -> bool:
    palavras = re.findall(r"[a-z]+", normalizar(texto))
    if not palavras:
        return True
    validas = [p for p in palavras if _palavra_valida(p)]
    return len(validas) / len(palavras) < 0.5


# ---------------------------------------------------------------- intenções fixas
_RE_SAUDACAO = re.compile(r"^(oi|ola|bom dia|boa tarde|boa noite|menu|ajuda|help|inicio)[\s!.?]*$")
_RE_LIMITACAO = re.compile(
    r"canal oficial|voce e (o |a |um |uma )?(canal|site|orgao|prefeitura|governo|oficial)|"
    r"quem (e|eh) voce|o que voce (e|faz)|voce e (humano|robo|ia|real)|e oficial"
)
_RE_FORA_ESCOPO = re.compile(
    r"passaporte|visto|reservista|cnpj|\bmei\b|imposto de renda|irpf|inss|aposentadoria|fgts|"
    r"bolsa familia|seguro desemprego|iptu|ipva|multa de transito|licenciamento"
)


@dataclass
class Triagem:
    texto_original_tamanho: int
    texto_seguro: str                 # já mascarado; é o único que segue no fluxo
    pii_tipos: list[str] = field(default_factory=list)
    pii_intencao: bool = False
    injection: bool = False
    categoria: str = "pergunta"       # vazia | longa | sem_sentido | saudacao | limitacao | fora_escopo | pergunta


def triar(mensagem: str | None) -> Triagem:
    """Classificação determinística da mensagem. Não guarda nada."""
    bruto = (mensagem or "").strip()
    seguro, tipos = mascarar_pii(bruto)
    t = Triagem(len(bruto), seguro, tipos, bool(INTENCAO_PII.search(bruto)), detectar_injection(bruto))
    norm = normalizar(seguro)
    if not bruto:
        t.categoria = "vazia"
    elif len(bruto) > LIMITE_CARACTERES:
        t.categoria = "longa"
    elif _RE_SAUDACAO.match(norm):
        t.categoria = "saudacao"
    elif _RE_LIMITACAO.search(norm):
        t.categoria = "limitacao"
    elif not t.injection and parece_sem_sentido(re.sub(r"\[[^\]]+\]", " ", seguro)):
        t.categoria = "sem_sentido"
    elif _RE_FORA_ESCOPO.search(norm):
        t.categoria = "fora_escopo"
    return t
