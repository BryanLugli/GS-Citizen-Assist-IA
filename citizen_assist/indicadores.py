"""Indicadores dos testes com usuários (tempo, acerto e facilidade de uso). Só usa a biblioteca padrão."""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "testes_usuarios"

TAREFAS = {
    "T1": ("Descobrir o que levar para a segunda via do RG",
           "certidão de nascimento ou casamento + comprovante de residência (90 dias) + BO (roubo/furto) ou declaração de extravio (perda)"),
    "T2": ("Descobrir se a Central atende aos sábados e o horário",
           "não atende aos sábados; segunda a sexta, 8h às 17h"),
    "T3": ("Descobrir quanto custa a certidão de nascimento pelo portal e em quanto tempo fica pronta",
           "R$ 49,00, em 3 dias úteis"),
}

QUESTOES = {
    "q1": "Foi fácil encontrar a informação que eu procurava.",
    "q2": "As respostas foram claras e fáceis de entender.",
    "q3": "Confiei mais na resposta porque ela mostrava a fonte e a data.",
    "q4": "Consegui usar sozinho(a), sem ajuda.",
    "q5": "Eu usaria este assistente de novo.",
}


def _ler(nome: str) -> list[dict]:
    with (PASTA / nome).open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def calcular() -> str:
    tarefas = [l for l in _ler("tarefas.csv") if l["tempo_segundos"].strip()]
    quest = [l for l in _ler("questionario.csv") if l["q1"].strip()]
    if not tarefas and not quest:
        return ("Planilhas ainda vazias. Preencha testes_usuarios/tarefas.csv e questionario.csv "
                "(participantes como P1..P5, sem nomes) e rode esta célula de novo.")
    out = ["### Tempo e acerto por tarefa\n", "| Tarefa | n | Tempo médio (s) | Mediana (s) | Acerto |",
           "|---|---|---|---|---|"]
    for t, (desc, _) in TAREFAS.items():
        ls = [l for l in tarefas if l["tarefa"] == t]
        if not ls:
            continue
        tempos = [float(l["tempo_segundos"].replace(",", ".")) for l in ls]
        acertos = sum(l["acertou_S_N"].strip().upper() == "S" for l in ls)
        out.append(f"| {t}: {desc} | {len(ls)} | {statistics.mean(tempos):.0f} | "
                   f"{statistics.median(tempos):.0f} | {acertos}/{len(ls)} ({100*acertos/len(ls):.0f}%) |")
    teclado = [l for l in tarefas if l["usou_so_teclado_S_N"].strip()]
    if teclado:
        ok = sum(l["usou_so_teclado_S_N"].strip().upper() == "S" for l in teclado)
        out.append(f"\nTarefas concluídas usando só o teclado: {ok}/{len(teclado)}.")
    if quest:
        out += ["\n### Facilidade de uso (1 a 5)\n", "| Pergunta | Média | Mín | Máx |", "|---|---|---|---|"]
        medias = []
        for q, texto in QUESTOES.items():
            notas = [int(l[q]) for l in quest if l[q].strip()]
            medias.append(statistics.mean(notas))
            out.append(f"| {q}. {texto} | {medias[-1]:.1f} | {min(notas)} | {max(notas)} |")
        out.append(f"\n**Nota geral de facilidade de uso: {statistics.mean(medias):.2f} / 5** "
                   f"({len(quest)} participantes).")
    return "\n".join(out)
