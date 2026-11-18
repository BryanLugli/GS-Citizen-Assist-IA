# Protocolo de testes com usuários

## Participantes
- Pelo menos **5 pessoas de fora do grupo**. Identificadas apenas como **P1 a P5**.
- **Não registramos** nome, idade, telefone, e-mail, foto, gravação de tela ou de voz.
- Antes de começar, ler para a pessoa: *"Este é um teste de um protótipo da faculdade. Não digite nenhum dado seu de verdade. Vamos anotar só o tempo, se você achou a resposta e suas notas de 1 a 5."*

## Preparação
1. Abrir a interface web (`python app/web.py` → http://127.0.0.1:5000) com a chave do Groq configurada.
2. Ter um cronômetro (celular) e as planilhas `testes_usuarios/tarefas.csv` e `questionario.csv` abertas.
3. Pedir à pessoa que use **só o teclado** se conseguir (Tab, Enter). Anotar S/N na coluna `usou_so_teclado_S_N`.

## Tarefas (cronometrar cada uma: do "pode começar" até a pessoa dizer a resposta)

| Tarefa | O que pedir | Resposta certa (para conferir) |
|---|---|---|
| T1 | "Descubra o que você precisa levar para tirar a segunda via do RG." | Certidão de nascimento ou casamento; comprovante de residência dos últimos 90 dias; BO (roubo/furto) ou declaração de extravio (perda). |
| T2 | "Descubra se a Central atende aos sábados e qual é o horário." | Não atende aos sábados; segunda a sexta, das 8h às 17h. |
| T3 | "Descubra quanto custa a certidão de nascimento pelo portal e em quanto tempo fica pronta." | R$ 49,00; 3 dias úteis. |

Anotar em `tarefas.csv`: participante, tarefa, tempo em segundos, acertou (S/N), usou só teclado (S/N). Não ajudar durante a tarefa; se a pessoa desistir após 3 minutos, anotar 180 s e acertou = N.

## Questionário (após as 3 tarefas) — escala 1 (discordo totalmente) a 5 (concordo totalmente)

| | Afirmação |
|---|---|
| q1 | Foi fácil encontrar a informação que eu procurava. |
| q2 | As respostas foram claras e fáceis de entender. |
| q3 | Confiei mais na resposta porque ela mostrava a fonte e a data. |
| q4 | Consegui usar sozinho(a), sem ajuda. |
| q5 | Eu usaria este assistente de novo. |

Comentário livre é opcional e não pode conter dado pessoal.

## Cálculo
A seção 13 do notebook lê as planilhas e calcula: tempo médio e mediano por tarefa, taxa de acerto por tarefa, uso só com teclado, média por pergunta e nota geral de facilidade de uso.
