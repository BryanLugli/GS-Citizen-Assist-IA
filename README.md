# Citizen Assist AI — Assistente Digital de Orientação ao Cidadão

**Global Solution 2026.2 · Prompt and Artificial Intelligence · FIAP**

**Integrantes**
- Beckman Rodrigues Lugli — RM 573442
- Bryan Vinicius Rodrigues Lugli — RM 571350
- Guilherme Xavier — RM 573053

Assistente sobre documentos pessoais (RG, CPF, título de eleitor, carteira de trabalho, certidões e CNH) que responde **somente** com base nas 7 fichas fictícias da Central do Cidadão de Aurora, citando a ficha e a data de verificação. Feito com **LangGraph** + **Groq**.

![Arquitetura](docs/arquitetura.png)

## Estrutura
```
fichas/                     7 fichas originais (única fonte de verdade)
citizen_assist/
  knowledge.py              carga das fichas e busca por palavras-chave (IDF)
  guardrails.py             entradas inválidas, máscara de dados pessoais, detecção de injection
  prompts.py                prompts, menu e respostas fixas
  agent.py                  grafos LangGraph v1 (base) e v2 (melhorada)
  judge.py                  LLM as a Judge + checagens determinísticas + tabelas
  indicadores.py            cálculo dos indicadores dos testes com usuários
  llm.py                    modelos Groq (e modo offline simulado)
app/web.py, app/cli.py      interface web acessível e versão de terminal
data/golden_dataset.json    as 26 mensagens do enunciado
data/perguntas_extras.json  6 perguntas extras do grupo
notebooks/citizen_assist_ai.ipynb   avaliação completa (antes × depois)
docs/                       relatório, protocolo de testes com usuários, diagrama
testes_usuarios/            planilhas anônimas (P1..P5)
tests/                      testes automáticos da parte determinística
```

## Como rodar (Windows, PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # abra o .env e cole sua chave do Groq (console.groq.com -> API Keys)

python tests\test_guardrails.py   # testes sem internet
python app\web.py                 # abra http://127.0.0.1:5000
python app\cli.py                 # versão de terminal
jupyter notebook notebooks\citizen_assist_ai.ipynb   # Kernel -> Restart & Run All
```
Linux/macOS: troque `\` por `/` e use `source .venv/bin/activate`.

- O projeto **não usa pandas** (tabelas com a biblioteca padrão).
- A avaliação completa (v1 + v2 + juiz, 26 mensagens) leva alguns minutos por causa das pausas que respeitam o limite gratuito do Groq. Os resultados ficam em `resultados/`; rodar de novo reaproveita o que já foi salvo (`forcar=True` refaz).
- Sem chave, tudo roda em **modo offline simulado** (arquivos `_SIMULADO`), só para conferir o código.
- Se der erro de limite (429) ou modelo indisponível, troque `CA_MODELO_AGENTE` / `CA_MODELO_JUIZ` no `.env` por outro modelo do Groq (ex.: `openai/gpt-oss-20b`, `meta-llama/llama-4-scout-17b-16e-instruct`) ou aumente `CA_PAUSA_SEGUNDOS`.

## Privacidade
Nenhuma mensagem é gravada. Dados pessoais são mascarados **antes** de qualquer envio ao Groq e também na saída. Resultados e tabelas mostram só mensagens mascaradas. Testes com usuários registram apenas P1–P5, tempo, acerto e notas.

> Protótipo educacional. Não é canal oficial. Valores e regras das fichas são fictícios.
