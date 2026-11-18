"""Base de conhecimento: carrega as 7 fichas e faz a busca por palavras-chave.

Escolha de organização (justificada no relatório):
- As fichas são pequenas (~8,7 KB no total). Não há necessidade de banco vetorial.
- Cada ficha vira um objeto `Ficha` com código, título, data de verificação e texto integral.
- A busca é determinística: palavras-chave da própria ficha + sinônimos curados pelo grupo.
  Isso é rápido, explicável (dá para mostrar POR QUE uma ficha foi escolhida) e não gasta tokens.
- Só o texto das fichas selecionadas vai para o modelo de linguagem.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

PASTA_FICHAS = Path(__file__).resolve().parent.parent / "fichas"


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos, espaços simples."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip()


# Sinônimos e termos extras curados pelo grupo. A FC-07 não tem linha de
# palavras-chave, então os termos dela vêm daqui. Os demais complementam as
# palavras-chave originais com formas que os usuários costumam escrever.
SINONIMOS: dict[str, list[str]] = {
    "FC-01": ["carteira de identidade", "cedula de identidade", "rg", "identidade", "perdi meu rg",
              "boletim de ocorrencia", "extravio", "posto de identificacao"],
    "FC-02": ["cpf", "cadastro de pessoa fisica", "inscricao no cpf", "situacao cadastral",
              "comprovante de inscricao"],
    "FC-03": ["titulo", "eleitor", "votar", "voto", "eleicao", "eleicoes", "transferencia",
              "zona eleitoral", "mudar meu titulo", "obrigatorio votar"],
    "FC-04": ["carteira de trabalho", "ctps", "primeiro emprego", "carteira digital"],
    "FC-05": ["certidao", "certidoes", "nascimento", "casamento", "obito", "cartorio"],
    "FC-06": ["cnh", "carteira de motorista", "habilitacao", "renovar", "renovacao", "vencida",
              "venceu", "dirigir", "exame medico"],
    "FC-07": ["horario", "sabado", "sabados", "domingo", "feriado", "atendem", "funciona",
              "agendamento", "agendar", "marcar horario", "outra pessoa", "terceiro", "terceiros",
              "procuracao", "pagamento", "pagar", "pix", "guia", "prioridade", "prioritario",
              "idoso", "gestante", "deficiencia", "libras", "interprete", "acessibilidade",
              "responsavel legal", "menor de idade", "sozinho"],
}


@dataclass
class Ficha:
    codigo: str
    titulo: str
    arquivo: str
    data_verificacao: str
    texto: str
    palavras_chave: list[str] = field(default_factory=list)


def _parse_ficha(caminho: Path) -> Ficha:
    texto = caminho.read_text(encoding="utf-8").strip()
    codigo = caminho.name[:5]  # "FC-01"
    titulo = texto.splitlines()[0].lstrip("# ").strip()
    m_data = re.search(r"vers[aã]o de (\d{2}/\d{2}/\d{4})", texto)
    data = m_data.group(1) if m_data else "data não informada"
    m_kw = re.search(r"\*\*Palavras-chave:\*\*\s*(.+)", texto)
    originais = [k.strip() for k in m_kw.group(1).split(",")] if m_kw else []
    chaves = {normalizar(k) for k in originais + SINONIMOS.get(codigo, []) if k.strip()}
    return Ficha(codigo, titulo, caminho.name, data, texto, sorted(chaves))


def carregar_fichas(pasta: Path = PASTA_FICHAS) -> dict[str, Ficha]:
    fichas = {}
    for caminho in sorted(pasta.glob("FC-0*.md")):
        f = _parse_ficha(caminho)
        fichas[f.codigo] = f
    if len(fichas) != 7:
        raise RuntimeError(f"Esperava 7 fichas em {pasta}, encontrei {len(fichas)}.")
    return fichas


FICHAS = carregar_fichas()


def _conta(chave: str, texto_norm: str) -> int:
    return len(re.findall(rf"(?<![a-z0-9]){re.escape(chave)}(?![a-z0-9])", texto_norm))


def _frequencia_documental() -> dict[str, int]:
    df: dict[str, int] = {}
    for f in FICHAS.values():
        for c in f.palavras_chave:
            df[c] = df.get(c, 0) + 1
    return df


_DF = _frequencia_documental()


def buscar(pergunta: str, k: int = 2, min_relativo: float = 0.5) -> list[tuple[str, float, list[str]]]:
    """Retorna até k fichas: (codigo, pontuacao, termos que bateram).

    Pontuação de cada termo = peso / nº de fichas que têm esse termo (estilo IDF):
    - termo de várias palavras vale 2, de uma palavra vale 1;
    - termos ambíguos ("segunda via" está em 3 fichas) valem menos.
    Só entram fichas com pelo menos `min_relativo` da pontuação da melhor.
    """
    q = normalizar(pergunta)
    resultado = []
    for codigo, ficha in FICHAS.items():
        batidas = [c for c in ficha.palavras_chave if _conta(c, q)]
        if not batidas:
            continue
        pontos = sum((2.0 if " " in c else 1.0) / _DF[c] for c in batidas)
        resultado.append((codigo, round(pontos, 2), batidas))
    resultado.sort(key=lambda r: (-r[1], r[0]))
    if resultado:
        topo = resultado[0][1]
        resultado = [r for r in resultado if r[1] >= min_relativo * topo]
    return resultado[:k]


def termos_conhecidos() -> set[str]:
    """Todas as palavras soltas das palavras-chave (usado para validar entradas)."""
    termos = set()
    for f in FICHAS.values():
        for c in f.palavras_chave:
            termos.update(c.split())
    return termos


def texto_das_fichas(codigos: list[str]) -> str:
    return "\n\n".join(f"<ficha codigo=\"{c}\">\n{FICHAS[c].texto}\n</ficha>" for c in codigos)
