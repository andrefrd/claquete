# Termos: pt-BR → en-US

Base de termos da tradução da Claquete.ai. **Todo texto em inglês deste repositório sai daqui.** Sem isto,
cada arquivo inventa o seu vocabulário e o produto fica com três nomes para a mesma coisa.

Duas regras antes da tabela:

1. **O que não se traduz.** Nome de produto, nome de comando, caminho de pasta, chave de JSON, campo de
   arquivo, nome de biblioteca. São identificadores: o código, o teste e a documentação casam por eles.
2. **O idioma é dado, não código.** A escolha feita no instalador vira um campo em `kit.config.json`
   (`"idioma": "pt-BR"` ou `"en-US"`), e é dele que saem voz, pronúncia, convite, transcrição e as
   mensagens dos scripts.

## 1. Produto e nomes próprios (nunca traduzir)

| pt-BR | en-US | Por quê |
|---|---|---|
| Claquete.ai | Claquete.ai | nome do produto |
| ChatADV, PostADV, PSD Software | iguais | nomes de produto |
| Claude, Remotion, React Bits, Playwright, ElevenLabs, Screen Studio, Vite, Higgsfield, HeyGen | iguais | nomes de terceiros |
| iart.ai, motion-design-skills | iguais | nome de repo de terceiros |
| Raquel | *(voz en-US: ver §7)* | nome de voz, não palavra traduzível |

## 2. Comandos e caminhos (nunca traduzir)

Os subcomandos do `kit.py` e do `gravacao.py`, os nomes de pasta gerados e as chaves de JSON são o
**contrato do parser**. Ficam como estão; o que ganham é **alias em inglês** (ver §8).

`novo` · `validar` · `plano` · `aprovar` · `narrar` · `conferir` · `cenas` · `montar` · `renderizar` ·
`finalizar` · `entregar` · `fazer` · `marca` · `voz` · `versao` · `transcrever` · `texto` · `emendas` ·
`audio` · `hibrido` · `reels` · `fatias` · `quadros`

`aulas/` · `edicoes/` · `marca/` · `material/` · `saida/` · `cenas/` · `gravar/` · `public/` · `estudio-video/` ·
`avulsos/` · `kit.config.json` · `marca.json` · `plano.json` · `VERSAO` · `conferencia.json` · `cenas.json`

Chaves de JSON: `fala` · `tela` · `tipo` · `rotulo` · `titulo` · `kicker` · `sub` · `itens` · `texto` ·
`quando` · `chips` · `destaques` · `cabecalho` · `imagem` · `video` · `animada` · `cena` · `descricao` ·
`foco` · `pausas` · `remover` · `acelerar` · `proibidos` · `mascaras` · `zooms` · `chamadas` · `capitulos` ·
`emendas_aceitas` · `legenda_trocas` · `minutos` · `formato` · `provedor` · `voice_id` · `model_id`

Valores de enum casados por parser (não traduzir): `capa` · `lista` · `colunas` · `fluxo` · `frase` ·
`numero` · `h` · `v` · `h,v` · `elevenlabs` · `eleven_v4` · `small`/`base`/`tiny`/`medium` · `higgsfield` · `heygen`

## 3. Vocabulário do produto

| pt-BR | en-US | Nota |
|---|---|---|
| estúdio | studio | a pasta com `kit.config.json` |
| aula | lesson | o vídeo didático. "videoaula" → "video lesson" |
| aula animada | animated lesson | |
| demonstração / demo | demo | "demo of the tool" |
| tutorial de tela | screen tutorial | só como descrição; a skill continua se chamando `tutorial-de-tela` (nome de pasta, §2) |
| dica rápida | quick tip | |
| caso completo | full walkthrough / case study | "caso" sozinho: "walkthrough" |
| trilha | track | "trilha de uma ferramenta" → "tool track" |
| gravação | recording | |
| gravação editada | edited recording | |
| gravação híbrida | hybrid recording | |
| corte viral / corte em pé | viral cut / vertical cut | "em pé" sozinho → "vertical" |
| deitado | landscape | formato `h` |
| em pé | vertical | formato `v`; "portrait" só se o contexto pedir |
| vinheta de marca | brand sting | |
| avatar apresentador | presenter avatar | |
| anúncio demonstrativo | demo ad | |
| carrossel | carousel | |
| vídeo para página | video for the web | |

## 4. Vocabulário da produção

| pt-BR | en-US | Nota |
|---|---|---|
| roteiro | script | |
| plano de edição | edit plan | |
| portão | gate | "portão 1" → "gate 1" |
| trava | guardrail | substantivo; o verbo "travar" → "block"/"refuse" |
| marca | brand | nunca "mark" |
| voz | voice | |
| fala | narration | o texto falado; "a fala de cada parte" → "the narration in each part" |
| narração | narration | |
| narrado | narrated | |
| locução | voice-over | |
| legenda | captions | a que aparece no vídeo; nunca "legend" |
| folha de quadros | contact sheet | |
| montagem | assembly | "apaga a montagem" → "deletes the assembly" |
| entrega | delivery | "entregar" → "deliver" |
| tela | screen | no roteiro, "a tela que vai com ela" → "the screen that goes with it" |
| tela animada | animated screen | |
| cena | scene | |
| peça | piece | componente da cena |
| ficha / chips | chips | manter "chips" |
| destaque | emphasis | realce no texto |
| transição | transition | |
| emenda | splice | "cada emenda é provada" → "every splice is proven" |
| muleta | filler word | "né", "certo" → "like", "you know" |
| pausa | pause | |
| espera | wait | |
| silêncio | silence | |
| aceleração | speed-up | "esperas aceleradas" → "sped-up waits" |
| zoom com mola | spring zoom | |
| foco | focus | o retângulo do zoom |
| borda | edge | |
| tela parada | static screen | a trava de 2,5 s |
| dado sensível | sensitive data | |
| conta de teste | test account | |
| conta fictícia | dummy data | |
| transcrição | transcription | |
| transcritor | transcriber | |
| revisão | review | |
| subagente | subagent | |
| sessão | session | |
| conferência | review report | `kit.py conferir` gera um relatório |
| semelhança | similarity | |
| duração | duration | |
| público | audience | |
| tom | tone | |
| glossário | glossary | |
| pronúncia | pronunciation | |
| sotaque | accent | |
| movimento | motion | "estilo de movimento" → "motion style" |
| fundo | background | |
| cor de destaque | accent color | |
| fonte | font | |
| janela | window | a janela do app no vídeo |
| bolinha | bubble | "câmera na bolinha" → "camera in the bubble" |
| cursor | cursor | |
| clique | click | |
| cartão | card | |

## 5. A tela pronta (valores fixos, documentar em inglês sem traduzir o valor)

`capa` → cover · `lista` → list · `colunas` → columns · `fluxo` → flow · `frase` → quote ·
`numero` → number · `imagem` → image · `video` → video · `animada` → animated

O `README` em inglês escreve os nomes em inglês **e** mostra o valor real entre crases, para ninguém
tentar usar uma palavra que o parser não aceita: `lista` (list).

## 6. Registro e voz

- **Inglês, não "português traduzido".** Reescreva a frase; não siga a ordem das palavras do original.
- **Segunda pessoa direta.** "Você" → "you"; imperativos curtos ("Deixe uns 10 GB livres" → "Keep about 10 GB free").
- **Travessão e dois pontos:** o original usa `·` e `—` como pontuação de marca. Mantenha, com espaço em volta.
- **Markdown e emoji:** inalterados.
- **O que o produto recusa em português, ele recusa em inglês.** "travessão" no `validar` é em-dash: a
  mesma regra vale nos dois idiomas e o texto em inglês deve dizer que é o travessão longo.
- **Título de seção:** caixa de frase — só a primeira palavra e os nomes próprios em maiúscula
  ("How Claude works", não "How Claude Works").
- **Artigo com nome próprio:** "o Claude" → "Claude" (sem "the"): "How Claude works", nunca "How the
  Claude works".
- **Números e unidades:** `2.5 s`, `-14 LUFS`, `1920×1080`, `10 GB` — sem tradução, vírgula decimal vira ponto.

## 7. Voz, idioma e conteúdo gerado

| | pt-BR | en-US |
|---|---|---|
| `idioma` em `kit.config.json` | `pt-BR` | `en-US` |
| voz padrão | Raquel (pt-BR) | a voz en-US escolhida (ver abaixo) |
| locale da transcrição | `pt` / `pt_BR` | `en` / `en_US` |
| convite: título | `Gostou da aula?` | `Enjoyed this lesson?` |
| convite: texto | `Veja as outras em` | `Watch the others at` |
| muletas (`gravacao.py`) | `né, ó, certo, enfim, tipo, hum` | `like, right, well, so, actually, basically` (só uma palavra cada: ver §7) |
| palavras proibidas (exemplo do gravador) | `senha, cpf` | `password, ssn` |

O `pronuncia` (mapa palavra escrita → como a voz diz) é **conteúdo do idioma**: as chaves em pt-BR
(`IA`, `INSS`, `PJe`) são inúteis em inglês e o mapa en-US traz siglas e nomes ingleses.

**Muleta em inglês é uma palavra só.** O `bruta()` de `gravacao.py:104-106` compara a muleta com
**um token** da transcrição (`ws[i]["w"]`), não com a frase: `"you know"` vira `youknow` e nunca casa
`you`. A lista en-US fica com termos de uma palavra (`like`, `right`, `well`, `so`) — `"you know"`,
`"I mean"` e `"kind of"` entrariam inertes, sem erro nenhum.

**Números e homófonos em inglês ficam vazios.** O `NUMEROS` (`kit.py:57-61`) e o `HOMOFONOS`
(`:64-66`) existem para casar o que o transcritor devolve diferente do roteiro. Em inglês, mapear
palavras funcionais é armadilha: `to`→`2`, `for`→`4`, `ate`→`8` injetam falso-igual e falso-diferente
na comparação de `conferir`. Sem um transcritor en-US rodado de verdade, qualquer lista é chute — e
chute aqui polui o relatório da revisão. O honesto é a conferência ficar só com a semelhança.

A voz padrão em en-US **não pode ser inventada**: tem de existir na biblioteca pública da ElevenLabs
(é voz pública, como a Raquel) e o par `voice_id` + `dono_publico` tem de vir do registro oficial.
Não escreva um `voice_id` de memória.

## 8. Aliases em inglês (o que ganha tradução no código)

O comando e a flag **em português continuam funcionando** — são o contrato e a retrocompatibilidade.
O inglês entra como alias:

| CLI | alias en-US |
|---|---|
| `--tudo` | `--all` |
| `--sim` | `--yes` |
| `--atualizar` | `--update` |
| `--projeto` | `--project` |
| `--estudio` | `--studio` |
| `--sem-ferramentas` | `--no-tools` |
| `--sem-motion` | `--no-motion` |
| `--sem-marca` | `--no-brand` |
| `--sem-cenas` | `--no-scenes` |
| `--sem-reactbits` | `--no-reactbits` |
| `--transcricao-local` | `--local-transcription` |
| `--desinstalar` | `--uninstall` |
| `--versao` | `--version` |

`--skills`, `--global`, `--help`, `-h` já são ingleses e não precisam de alias.
`--idioma` / `--lang` (novo): escolhe o idioma, com valor `pt-BR` ou `en-US`.

## 9. Nome do projeto em inglês

O produto chama-se Claquete.ai nos dois idiomas — é a marca, e o README em inglês explica de onde vem
(claquete = clapperboard), em uma linha, em vez de tentar traduzir. O método, o estúdio e as skills
têm nomes em inglês conforme §3; o repositório continua `github:dantaspaulo/claquete`.

## 10. O que este PR decide (e o que fica de fora)

Decidido, e vale registrar porque alguém vai perguntar:

- **As mensagens dos scripts ficam em código, não no `kit.config.json`.** O `--atualizar` usa uma
  mesclagem que nunca sobrescreve o que já está lá — é o que protege a marca e as cores da pessoa.
  Se as mensagens e os números de língua morassem no config, um erro nosso ficaria congelado na
  máquina de todo mundo. Em `scripts/idioma.py`, o `--atualizar` copia o arquivo inteiro e conserta.
- **O pt-BR não se move.** Os valores em português continuam no topo do `kit.config.json`, chave por
  chave, porque `assinatura_parte` hasheia `voz` e `pronuncia` inteiros: mover a estrutura faria toda
  narração já paga ser narrada — e cobrada — de novo.
- **Aliases, não renomeação.** `--tudo` continua funcionando; `--all` entra como alias. Renomear
  quebraria todo comando já escrito no README, nas skills e na memória de quem usa.
- **Os exemplos embarcados ficam em português.** `aulas/exemplo.json` e os outros alimentam as
  asserções da suíte, que casam texto em português. Traduzi-los quebraria testes por um motivo que
  nada tem a ver com idioma. Um `exemplo-en.json` entra depois, como conteúdo, com teste próprio.
- **Ajuda e `description` do `argparse` ficam em pt-BR**, e os subcomandos também: são contrato do
  parser e, para o Claude, o subcomando é identificador, não texto.
- **`ritmo` em inglês começa igual ao português** (2.5 palavras/s), sem medição. É ausência de dado,
  não palpite disfarçado: o efeito é um aviso de duração na primeira revisão. Para medir, narre uma
  parte em inglês e compare `duracao_audio(mp3)` com `len(fala.split()) / x`.
- **`cenas/index.html` e `gravar/demo/index.html` mantêm `lang="pt-BR"`:** são a ferramenta que
  fotografa e grava a tela, não o vídeo que a pessoa entrega.
- **A voz da Lauren não foi ouvida.** A arquitetura garante que o `voice_id` e o `dono_publico` certos
  chegam à API; não garante que ela soa bem em texto técnico. Só revisão humana fecha isso.
