---
name: gravacao-editada
description: >-
  Edita uma gravação do Screen Studio 4 (tela, câmera e microfone da pessoa) sem abrir o app e sem
  API, em três versões: a editada (sem muletas, repetições, frases erradas e esperas, com zoom,
  cursor, câmera na bolinha e legenda do que se ouve), a híbrida (a fala remontada numa ordem de
  raciocínio, a tela com o acabamento do Screen Studio e cenas das aulas por cima da voz) e os
  cortes em pé para Reels, TikTok e Shorts (até 90 s, a 1,3x, gancho, prova e convite). Transcreve
  no próprio computador, prova cada emenda transcrevendo antes e depois do corte e para em dois
  portões. Use sempre que a pessoa disser "edita minha gravação", "Screen Studio", "tira os né e
  os certo", "corta as pausas", "deixa dinâmico", "monta o raciocínio", "versão híbrida", "cortes
  para Reels da minha gravação", "corte viral da gravação" ou mandar uma pasta .screenstudio.
metadata:
  resumo: Gravação do Screen Studio editada, híbrida e em cortes em pé
---

# Gravação editada, híbrida e cortes em pé

A pessoa gravou no Screen Studio 4 (tela, câmera e microfone) e quer o vídeo pronto. O Claude
transcreve a fala no computador, decide o que sai, prova cada emenda, mostra o plano, e o estúdio
monta três versões a partir da mesma gravação:

| Versão | O que é | Comando |
|---|---|---|
| **editada** | a gravação na ordem em que foi feita, sem muletas, repetições, frases erradas e esperas; zoom, cursor, cliques, câmera na bolinha e legenda do que se ouve | `montar` |
| **híbrida** | a fala remontada numa ordem de raciocínio (problema, solução, usos, demonstrações, o que vem aí), a tela com o acabamento do Screen Studio e cenas das aulas por cima da voz | `hibrido` |
| **cortes em pé** | cada corte junta trechos numa narrativa curta (gancho, prova, convite), até 90 s, a 1,3x, a tela num cartão com zoom mais fechado | `reels` |

O projeto do Screen Studio só é lido. A montagem vai para `saida/edicoes/<id>/`, e o único
arquivo novo fora dela é a cópia das fatias (`fatias`), ao lado do projeto.

## O que precisa

- **Screen Studio 4.x**, com a gravação numa sessão só (gravação pausada vira várias sessões, e
  esta versão recusa). Projeto salvo no 3.x: abra e salve no 4.x antes.
- **Um transcritor de palavras, no computador.** O Screen Studio 4 traz um (a fala da Apple, que
  pede macOS 26 ou mais novo) e o estúdio o usa sozinho. Sem ele, ou em macOS mais antigo, a
  transcrição local do estúdio (`npx github:dantaspaulo/claquete --atualizar --transcricao-local`)
  com `CLAQUETE_TRANSCRITOR=whisper`. Nenhuma API, nenhuma chave.
- Uns 10 GB livres no disco do sistema: o render recusa abaixo de 5 GB.

## Antes de começar: o que perguntar

Numa rodada só, com sugestão pronta:
1. **A gravação**: a pasta `.screenstudio` (em geral, em `~/Screen Studio Projects`).
2. **Para quem e onde vai**: grupo de clientes, site, YouTube, Reels. Isso decide as versões.
3. **As versões**: editada, híbrida, cortes em pé (quantos).
4. **O que não pode aparecer**: e-mails, contas, valores, outras janelas, senhas salvas.
5. **O convite do fim**: o da marca (`kit.config.json`) ou outro para este vídeo.

## 1. Transcrever e ler a fala

```bash
python3 scripts/gravacao.py novo demo-agenda --projeto "~/Screen Studio Projects/Minha gravação.screenstudio"
python3 scripts/gravacao.py transcrever demo-agenda
python3 scripts/gravacao.py texto demo-agenda --de 0 --ate 120
```

O `texto` mostra cada palavra com o índice e o segundo (`12:né@34.10`); as que já estão nos
cortes aparecem entre colchetes. Leia a fala inteira antes de cortar, em janelas de 2 minutos.

Para achar o que não pode aparecer, faça folhas da tela (um quadro a cada 3 s, 90 s por folha) e
leia todas (um subagente, com o modelo escrito no pedido):

```bash
ffmpeg -i "<projeto>/recording/channel-1-display-0.m3u8" -vf "fps=1/3,scale=480:-2,tile=6x5" folha-%02d.jpg
```

Achou um dado, procure o quadro exato com `fps=10` em volta dele: em gravação de verdade, a lista
de contas apareceu 0,4 s depois do fim da fala.

## 2. O roteiro da edição (`edicoes/<id>.json`)

```json
{
 "titulo": "Agenda: marcar e remarcar sem conflito",
 "projeto": "/Users/voce/Screen Studio Projects/Minha gravação.screenstudio",
 "remover": [[12, 12], [40, 47]],
 "remover_tempo": [[305.4, 309.05]],
 "acelerar": [{"de": 382.2, "ate": 388.1, "vel": 4}],
 "proibidos": [{"de": 460.5, "ate": 461.4, "antes": 460.4, "depois": 461.5}],
 "mascaras": [{"de": 68.9, "ate": 99.6, "cor": "#ffffff", "retangulos": [[343, 611, 236, 26]]}],
 "zooms": [{"de": 44.7, "ate": 57.0, "escala": 1.5, "x": 640, "y": 430}, {"de": 90, "ate": 96, "seguir": true}],
 "abertura": {"kicker": "Novidade", "titulo": "Agenda *sem conflito*", "sub": "em dois minutos", "ate": 4},
 "chamadas": [{"em": 284.4, "dur": 3.6, "texto": "A senha não fica salva"}],
 "capitulos": [{"em": 149.5, "n": "1", "texto": "Marcar"}],
 "legenda_trocas": [["agenda pro", "AgendaPro"]],
 "camera": {"x": 0.5, "y": 0.38}
}
```

| Chave | O que faz |
|---|---|
| `remover` | trechos de fala que saem, por índice de palavra `[primeira, última]` |
| `remover_tempo` | janelas que saem pelo tempo (troca de janela, silêncio no fim) |
| `acelerar` | esperas sem fala (a ferramenta pensando, digitação): passam aceleradas e mudas, com "▶▶ 4x" na tela |
| `proibidos` | dado sensível com fala por cima: a tela congela no quadro de `antes` ou `depois`, e a fala segue |
| `mascaras` | retângulos por cima da tela, em pontos da tela (o `bounds` da gravação), entre `de` e `ate` |
| `zooms` | `escala` com centro `x`, `y`, ou `seguir: true` (segue o cursor); entram e saem com mola |
| `abertura`, `chamadas`, `capitulos` | texto por cima da tela; `em` é o segundo da gravação |
| `pausas` | `minima` (0,40 s), `sobra` (0,13 s de silêncio em cada borda), `limiar_db`, `voz_db` |
| `legenda_trocas` | troca o que o transcritor escreveu errado na legenda (`""` apaga) |
| `convite` | o fim do vídeo (`titulo`, `texto`, `endereco`); `false` tira |
| `trabalho` | outra pasta para a montagem (um disco externo, por exemplo) |

Tempos em segundos da gravação. O Screen Studio 4 grava a tela sem o cursor: o estúdio desenha o
cursor do macOS que o app guardou, com o anel de cada clique.

### O que cortar

Tirar muleta é o piso; o objetivo é a fala dinâmica e sem tropeço:
- **muletas**: "né", "ó", "certo", "tipo", "enfim", "tá bom" quando não dizem nada;
- **repetições coladas** ("uma uma") e **começos falsos** (a frase que a pessoa começou, errou e
  repetiu: sai a errada inteira);
- **o redundante** e o que **não é do assunto**: corte de conteúdo é decisão de editor, e a entrega
  diz o que saiu e por quê;
- **esperas** viram `acelerar`; **troca de janela** e **tela fora do assunto** viram `remover_tempo`;
- **dado sensível**: `proibidos` (com fala) ou `remover_tempo` (sem fala); o que fica visível por
  muito tempo, `mascaras`.

A borda de cada corte vai sozinha para o silêncio entre as palavras: o transcritor emenda a pausa
no começo da palavra seguinte, e o estúdio acha o começo real pela energia do áudio.

## 3. Plano, prova das emendas e portão 1

```bash
python3 scripts/gravacao.py plano demo-agenda      # saida/edicoes/demo-agenda/plano-de-edicao.md
python3 scripts/gravacao.py emendas demo-agenda    # prova cada corte
```

- O `plano` escreve o plano de edição: a duração antes e depois, cada corte com as palavras em
  volta, as muletas que ficaram, as palavras com um pedaço cortado, o texto na tela, a ordem da
  híbrida, as cenas, os cortes em pé e o texto que fica.
- O `emendas` **prova cada corte**: junta 1,6 s antes e 1,6 s depois da emenda, transcreve e confere
  se as palavras vizinhas saíram inteiras e as cortadas sumiram. Não deu de primeira, testa outros
  pontos de silêncio e fica com o melhor. `ok` é nota 0,99 ou mais; `??` pede ouvido: mude o corte
  (às vezes tirar a frase inteira resolve) ou, se a revisão ouviu e está limpa, ponha o primeiro
  índice em `emendas_aceitas`.
- Um subagente revisa o plano (com o modelo escrito no pedido, um mais forte: pede julgamento):
  corte que muda o sentido, muleta que ficou, frase que ficou sem começo.
- **Portão 1:** mostre o plano à pessoa (o conteúdo, não o caminho do arquivo) e, com o ok,
  `gravacao.py aprovar <id>`. Mudou o que sai, a ordem, as cenas, os textos ou os cortes em pé
  depois disso, pede ok de novo; zoom, câmera, bolinha, trocas de legenda e emendas aceitas não.

## 4. A fala editada e o portão 2

```bash
python3 scripts/gravacao.py audio demo-agenda
python3 scripts/gravacao.py conferir demo-agenda             # para com código 2 e o relatório
python3 scripts/gravacao.py conferir demo-agenda --aprovado
```

O `audio` monta a fala com 8 ms de rampa em cada emenda (sem estalo), passa-alta e -16 LUFS. O
`conferir` transcreve a fala editada e compara com o texto esperado: semelhança, cada diferença
com o segundo do vídeo, as muletas ouvidas e as emendas a ouvir. Um subagente lê
`conferencia.json` e ouve o que foi apontado. O `--aprovado` recusa corte sem prova, emenda baixa
sem aceite e semelhança abaixo de 85%. A legenda de todas as versões sai do que se ouve aqui.

## 5. A versão editada

```bash
python3 scripts/gravacao.py montar demo-agenda
python3 scripts/gravacao.py renderizar demo-agenda --versao editada --quadros 1200-1500   # prévia
python3 scripts/gravacao.py renderizar demo-agenda --versao editada
```

O `montar` corta a tela e a câmera em partes já na ordem e na velocidade do plano, confere o número
de quadros de cada uma e avisa onde a tela fica mais de 2,5 s sem novidade (nada muda, sem cursor
andando, zoom, chamada ou cena): lugar de pôr um zoom, uma chamada ou de acelerar. A prévia
(`--quadros`) roda sem os portões; o vídeo inteiro, só com os dois.

## 6. A versão híbrida

A fala da pessoa remontada num argumento, no molde das aulas:

```json
"hibrido": {
 "blocos": [
  {"nome": "problema", "de": 34.6, "ate": 44.2},
  {"nome": "contexto", "de": 0, "ate": 34.6},
  {"nome": "como funciona", "de": 44.2, "ate": 150},
  {"nome": "o que vem aí", "de": 410, "ate": 430}
 ],
 "cenas": [
  {"de": 34.6, "ate": 44.2, "rotulo": "O problema",
   "tela": {"tipo": "lista", "titulo": "O que falta numa agenda *comum*",
            "itens": [{"texto": "Avisar o conflito", "quando": "conflito"}, {"texto": "Remarcar sozinha", "quando": "remarcar"}]}}
 ],
 "capitulos": [{"em": 44.5, "n": "1", "texto": "Como funciona"}],
 "chamadas": [{"em": 120.0, "dur": 3, "texto": "Funciona no celular também"}]
}
```

- **A ordem:** problema, solução, usos, demonstrações, o que vem aí. Cada bloco leva o que ficou
  na edição entre `de` e `ate`; a borda vai para o silêncio mais próximo (marque-a entre duas
  palavras). A mesma fala em dois blocos é recusada; a que fica de fora aparece no plano.
- **As cenas** são as telas prontas das aulas (`capa`, `lista`, `colunas`, `fluxo`, `frase`,
  `numero`, `imagem`) por cima da voz da pessoa, com a câmera na bolinha. Cada item entra na palavra
  dita (`quando`), e palavra que a fala daquele trecho não tem é recusada: confira no que se ouve
  (`legenda_trocas` acerta o que o transcritor errou). Use cena onde a tela não ajuda: o problema,
  a ideia, um número, a lista do que vem.
- **O acabamento do Screen Studio:** `fatias` grava os cortes da híbrida numa **cópia** do projeto
  (clone, sem ocupar o disco de novo), com a câmera em bolinha e a legenda do app desligada. Peça à
  pessoa para abrir a cópia e exportar (Export, MP4, 1080p): o app não exporta sem clique.

```bash
python3 scripts/gravacao.py fatias demo-agenda --nome "Minha gravação (editada)"
python3 scripts/gravacao.py hibrido demo-agenda --exportacao "~/Downloads/Minha gravação (editada).mp4"
python3 scripts/gravacao.py renderizar demo-agenda --versao hibrida
```

- Sem a exportação (`hibrido` sem `--exportacao`), a tela é desenhada pelo estúdio, como na editada.
- A exportação não mostra o que o estúdio esconde: `fatias` e `hibrido` recusam trecho proibido ou
  máscara que não esteja coberto por uma cena. A exportação que não bate com as fatias (o projeto
  mudou depois) também é recusada.

## 7. Cortes em pé

```json
"reels": {
 "velocidade": 1.3,
 "convite": {"titulo": "Teste grátis", "texto": "o link está na bio", "endereco": "seusite.com.br"},
 "cortes": [
  {"id": "r1", "gancho": "Sua agenda ainda *marca conflito*?", "titulo": "Agenda sem conflito",
   "trechos": [[34.6, 44.2], [44.8, 56.9], [74.0, 97.2]]}
 ]
}
```

- Cada corte é uma narrativa curta: **gancho** (o ganho de quem assiste, nos 2 primeiros segundos,
  com a palavra forte entre asteriscos), **prova** (a ferramenta funcionando) e **convite**.
- Até 90 s depois da aceleração (`max_segundos` muda); abaixo de 15 s o estúdio avisa.
- A tela vai num cartão de 1080x1040 com zoom mais fechado, que segue o cursor quando não há zoom;
  a cena da híbrida que o corte atravessar (1,5 s ou mais) entra em pé; legenda palavra a palavra,
  câmera na bolinha no alto, barra de progresso e o título depois do gancho.

```bash
python3 scripts/gravacao.py reels demo-agenda
python3 scripts/gravacao.py renderizar demo-agenda --versao reels            # todos
python3 scripts/gravacao.py renderizar demo-agenda --versao reels --corte r1
```

## 8. Revisão e entrega

- Depois de cada render, as folhas de quadros (`ffmpeg -i video.mp4 -vf "fps=1/4,scale=480:-2,tile=5x4" folha-%02d.jpg`)
  passam por um subagente: dado sensível, zoom ruim, legenda errada, cena cortada.
- Mostre os vídeos e espere o ok. Com ele: `gravacao.py entregar <id> --destino <pasta>` copia os
  vídeos, as capas e as legendas (`.srt` e `.vtt`), confere a cópia e apaga a montagem. O projeto
  do Screen Studio e a cópia das fatias ficam onde estão.
- Na resposta final: onde ficaram os vídeos, a duração antes e depois, o que saiu da fala e por
  quê, o que foi escondido e o que ainda depende da pessoa.

## Comandos

| Comando | O que faz | O que recusa |
|---|---|---|
| `novo <id> --projeto <pasta>` | cria o roteiro | pasta que não é projeto do Screen Studio 4; gravação pausada |
| `transcrever` | a fala palavra a palavra, no computador | sem transcritor |
| `texto [--de --ate]` | palavras numeradas com o segundo | · |
| `plano` | o plano de edição | índice fora da fala; espera acelerada que cruza um proibido; corte em pé acima do máximo |
| `emendas [--corte N] [--refazer]` | prova cada corte | · |
| `aprovar` | **portão 1** | plano que não é o do roteiro atual |
| `audio` | a fala editada | plano velho |
| `conferir [--aprovado]` | **portão 2** | corte sem prova; emenda baixa sem aceite; semelhança abaixo de 85% |
| `montar` | a versão editada | fala editada velha |
| `fatias --nome` | os cortes numa cópia do projeto | sem o ok; dado sensível descoberto; cópia que já existe |
| `hibrido [--exportacao]` | a versão híbrida | fala em dois blocos; cena com palavra que a fala não tem; exportação que não bate |
| `reels` | os cortes em pé | corte acima do máximo; sem gancho |
| `renderizar --versao [--corte] [--quadros]` | o vídeo, em partes de 900 quadros | sem os dois portões (menos a prévia); roteiro mudado depois de preparar; menos de 5 GB livres |
| `entregar --destino` | copia e apaga a montagem | sem vídeo pronto; cópia que não bateu |

## O que já deu errado (e o estúdio já segura)

- **O transcritor do Screen Studio devolve o resultado guardado quando o caminho do arquivo se
  repete**, mesmo com o áudio mudado: cada transcrição vai com um nome novo.
- **A pausa entra no começo da palavra seguinte** na transcrição: o corte usa o começo real pela
  energia, e a emenda é provada antes de valer.
- **O render inteiro encheu o disco:** o Remotion grava cada quadro e copia cada vídeo usado para a
  pasta temporária. O estúdio renderiza em partes de 900 quadros, com a tela e a câmera cortadas
  por parte, e para entre uma parte e outra se o disco apertar.
- **Pasta temporária num disco externo formatado para Windows (NTFS pelo macFUSE) quebra o
  navegador do render.** A montagem pode ir para o disco externo (`trabalho`); a pasta temporária
  do sistema, não.
- **A cópia das fatias mostraria o dado escondido:** a máscara e a tela congelada são do estúdio;
  o Screen Studio exporta a tela como foi gravada. Por isso a trava das fatias.
