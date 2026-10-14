# Versões

Formato: [versão semântica](https://semver.org/lang/pt-BR/). A versão de cada entrega fica no `package.json`, na tag do
Git (`vX.Y.Z`) e na página de versões do GitHub, sempre iguais.

- **X.0.0**: mudança grande, que pode exigir reinstalar ou mudar o jeito de usar (a 2.0, por exemplo).
- **X.Y.0**: melhoria ou recurso novo que não quebra nada (2.1, 2.2...).
- **X.Y.Z**: correção (2.1.1, 2.1.2...).

## Não lançado

<sub>O número da versão fica com o mantenedor: o roadmap já reserva a 2.3 para avatar, anúncio e carrossel.</sub>

Inglês: a Claquete fala os dois idiomas. O português continua sendo o padrão, do jeito que sempre foi —
quem já usa não muda nada. Quem quer em inglês escolhe na primeira pergunta do instalador, ou
`npx github:dantaspaulo/claquete --idioma en-US`.

- **A pergunta de idioma, no começo.** O instalador pergunta o idioma antes de qualquer coisa, porque
  ele decide duas de uma vez: quais skills copiar e o que vai para a configuração do estúdio. Em
  inglês ele sugere `English (US)` já marcado quando o sistema está em inglês (`LANG`/`LC_ALL`); o
  Enter aceita. Sem terminal interativo (`--tudo`, CI), o padrão segue sendo o português. Trocar
  depois: `npx github:dantaspaulo/claquete --atualizar --idioma en-US`.
- **`skills-en/` com as seis skills em inglês**, com os mesmos nomes de pasta das portuguesas — é por
  eles que o `--desinstalar` remove e que a skill de entrada chama as outras. As frases que acionam
  cada skill ("quero fazer um vídeo", "edita minha gravação") têm equivalentes em inglês.
- **Voz, pronúncia e convite por idioma.** O inglês tem voz própria (Lauren — Instructional Voice,
  Elearning, da biblioteca pública da ElevenLabs, o mesmo perfil da Raquel), o próprio dicionário de
  pronúncia (`AI` → "A I", `SQL` → "sequel") e o próprio convite de fim de vídeo. Ficam em
  `linguas.en-US`, no `kit.config.json`.
- **O idioma atravessa a geração:** a transcrição local passa a receber o idioma por argumento (antes
  o inglês era transcrito como português, sem erro nenhum), as muletas da gravação editada
  ("like", "right", "well" no lugar de "né", "certo"), a busca de sigla, o tamanho do bloco de legenda,
  o formato do número que conta na tela (1.500 em português, 1,500 em inglês) e o locale do roteiro de edição, que nasce no idioma do
  estúdio.
- **O português não se move.** Os valores em português continuam onde sempre estiveram, chave por
  chave. É de propósito: a assinatura que decide se uma parte precisa ser narrada de novo inclui a
  voz e a pronúncia, então mover a estrutura faria toda narração já paga ser narrada — e cobrada — de
  novo. Há teste que confere que a assinatura de hoje é a mesma de antes desta versão.
- **As opções com nome em inglês:** `--all`, `--yes`, `--update`, `--project`, `--studio`, `--no-tools`,
  `--no-motion`, `--no-brand`, `--no-scenes`, `--no-reactbits`, `--local-transcription`, `--uninstall`,
  `--version`. As portuguesas continuam funcionando: renomear quebraria tudo o que já está escrito.
- **`README.en.md`**, com seletor de idioma no topo dos dois READMEs, e **`docs/i18n/TERMOS.md`**, o
  termo a termo que rege a tradução e registra o que ficou de fora desta entrega (e por quê).

## 2.2.0 · 13/10/2026

Gravação editada: a sua gravação do Screen Studio 4 vira três vídeos, com a sua voz e sem abrir o app. Quem tem a 2.x
atualiza com `npx github:dantaspaulo/claquete --atualizar`.

- **Skill nova `gravacao-editada` e `scripts/gravacao.py`:** lê o projeto do Screen Studio 4 (tela, microfone, câmera,
  cursor e cliques) sem mexer nele e transcreve a fala palavra a palavra no computador: com o transcritor que vem dentro
  do Screen Studio 4 (a fala da Apple, macOS 26 ou mais novo) ou com a transcrição local do estúdio
  (`CLAQUETE_TRANSCRITOR=whisper`, `scripts/palavras_whisper.py`). Nenhuma API.
- **Versão editada:** cortes por palavra (muletas, repetições, frases erradas), pausas encolhidas, esperas aceleradas e
  mudas com "▶▶ 4x" na tela, trecho proibido com a tela congelada por baixo da fala, máscaras por tempo, zoom com mola,
  o cursor do macOS e os cliques desenhados pelo estúdio (o Screen Studio 4 grava a tela sem o cursor), câmera na
  bolinha, abertura, chamadas, capítulos, legenda do que se ouve (`.srt` e `.vtt`) e o convite da marca.
- **Cada emenda é provada:** a borda do corte vai para o silêncio pela energia do áudio (o transcritor emenda a pausa no
  começo da palavra seguinte) e o `emendas` transcreve 1,6 s antes e 1,6 s depois de cada corte, testando outros pontos
  de silêncio quando o primeiro não fica limpo. Cada transcrição vai com um nome de arquivo novo: o transcritor do Screen
  Studio devolve o resultado guardado quando o caminho se repete.
- **Versão híbrida:** a fala remontada em blocos numa ordem de raciocínio, com as telas prontas das aulas (capa, lista,
  colunas, fluxo, frase, número, imagem) por cima da voz, cada item entrando na palavra dita, e a câmera na bolinha. O
  `fatias` grava os cortes numa cópia do projeto (clone APFS no macOS), com a câmera em bolinha e a legenda do app
  desligada; a pessoa exporta e o `hibrido --exportacao` usa a tela com o acabamento do Screen Studio. Sem a exportação, a
  tela é desenhada pelo estúdio.
- **Cortes em pé:** cada corte junta trechos numa narrativa (gancho, prova, convite) de até 90 s, a 1,3x; a tela num
  cartão de 1080x1040 com zoom mais fechado, as cenas da híbrida em pé, legenda palavra a palavra, câmera no alto e o
  gancho saindo antes de o título entrar.
- **Dois portões:** o plano de edição (`plano`, `aprovar`: o que sai, a ordem da híbrida, as cenas, os textos e os cortes
  em pé; zoom e câmera ficam fora do ok) e a fala editada (`conferir`: transcrita de novo e comparada com o texto
  esperado; `--aprovado` recusa corte sem prova, emenda duvidosa sem aceite e menos de 85% de semelhança).
- **Travas:** a cópia para o Screen Studio é recusada se fosse mostrar trecho proibido ou máscara sem uma cena por
  cima; exportação que não bate com os cortes, a mesma fala em dois blocos, cena que entra numa palavra que a fala não
  tem e corte em pé acima do máximo também. O projeto original nunca é escrito, e cópia que já existe não é sobrescrita.
- **Render para máquina de disco curto:** em partes de 900 quadros, com a tela e a câmera cortadas por parte e já na
  ordem da linha do tempo, número de quadros conferido em cada parte, e parada entre uma parte e outra se o disco
  apertar. O `montar` avisa onde a tela fica mais de 2,5 s sem novidade.
- **Testes:** 34 casos novos no `teste.py`, com uma gravação do Screen Studio de mentira (tons no lugar das palavras e um
  transcritor que os reconhece), sem gastar nada; cada trava nova foi provada por mutação.
- O instalador mantém `edicoes/` no `--atualizar`. Roteiro: **2.3** redes (avatar, anúncio demonstrativo, carrossel e
  imagem 4:5) e vinheta de marca; **2.4** instrução no celular e gravações de outros apps (Recordly, qualquer vídeo).

## 2.1.0 · 09/10/2026

Telas animadas: o visual das aulas do ChatADV agora sai de qualquer estúdio. Quem tem a 2.0 atualiza com
`npx github:dantaspaulo/claquete --atualizar`.

- **Tela `animada`:** a cena é um componente React em `cenas/src/aulas/<id>.jsx`, escrito depois do ok ao roteiro (o plano
  mostra a `descricao` de cada uma e lista as cenas a escrever). `kit.py cenas <id>` compila o app de cenas (Vite + React +
  motion), abre cada cena com o relógio da página controlado e fotografa quadro a quadro, deitada e em pé, no segundo
  de cada palavra da voz. `--previa` tira cinco fotos de cada cena; o `fazer` fotografa sozinho o que estiver pendente.
- **Peças prontas** em `cenas/src/ilustra.jsx`, nas cores e fontes da marca: título palavra a palavra, cena com o texto
  fixo fora da câmera, câmera com zoom que só aceita foco inteiro (o resto escurece), balões de conversa, digitação,
  documento que se escreve, itens com visto, contador, placa que vira, explosão, selo, esfera de energia, fundo vivo
  (aurora, partículas, feixes) e mais.
- **React Bits na máquina de quem instala:** o instalador baixa do reactbits.dev 12 componentes grátis (SplitText,
  BlurText, ShinyText, GradientText, RotatingText, TextType, CountUp, AnimatedList, Orb, Aurora, Beams, Particles) e, com
  uma licença do React Bits Pro (opcional, pedida junto da chave da ElevenLabs), os 6 que as aulas do ChatADV usam.
  Sem eles, cada peça usa a versão própria, só com motion.
- **Licença protegida por mecanismo:** nenhum componente do React Bits entra neste repositório (a licença deles não deixa
  redistribuir). O `teste.py` recusa componente versionado, e o pre-commit (`.githooks`, ligado com
  `git config core.hooksPath .githooks`) recusa o commit.
- **Travas da captura:** erro na cena, palavra que a fala não tem, peça cortada pela metade na borda da câmera, quadro
  vazio e tela parada por mais de 2,5 s. O `montar` recusa tela animada não fotografada, ou que mudou depois (código da
  cena, componentes, tempo da voz, duração ou tema).
- **Telas prontas mais bonitas:** título que entra desfocando, etiqueta em pílula, luz que passeia atrás da capa e da
  frase, aspas grandes na frase, número com brilho, cartões em degradê, janela com brilho de vidro e fundo com pontos
  que derivam. Os tempos de entrada não mudaram.
- Instalador: `--sem-cenas` e `--sem-reactbits`; o `--sem-ferramentas` também pula o navegador do Playwright.
  `CLAQUETE_CHROMIUM` usa um Chrome que já existe na máquina para fotografar as cenas.
- Próximas: **2.2** redes (avatar, anúncio demonstrativo, corte viral, carrossel e imagem 4:5) e vinheta de marca;
  **2.3** edição das suas gravações e instrução no celular.

## 2.0.0 · 09/10/2026

Mudança grande: o fluxo, as skills e a instalação foram reorganizados. Quem tem a 1.x atualiza com
`npx github:dantaspaulo/claquete --atualizar` (roteiros, gravações, chaves e configuração ficam).

- **Tipos de vídeo com duração:** aula, caso e trilha (de 2 a 5 minutos, escolhidos ao começar o projeto), demonstração
  (1 a 4 min) e dica (30 a 90 s). `kit.py novo <id> --tipo aula --minutos 3`; o `montar` recusa o que sai da duração.
- **Dois portões de verdade:** o roteiro com o plano de edição (`plano` e `aprovar`; o `narrar` recusa sem ok) e a
  revisão da fala (`conferir`; o `montar` recusa sem `--aprovado`).
- **Sem OpenAI:** a revisão da fala é da própria sessão do Claude, com subagentes. Transcrição local e gratuita
  (faster-whisper, num `.venv` do estúdio) como opção. A única chave é a da ElevenLabs.
- **Sua marca:** questionário na instalação (nome, público, redes, cores, fontes, logo, movimento, tom, palavras
  proibidas, glossário, voz e chamada) e material da marca por pasta, HTML, `.md` ou link. `kit.py marca` aplica ao estúdio.
- **Skills novas:** `claquete` (porta de entrada) e `claquete-marca`. `aula-animada` e `tutorial-de-tela` reescritas
  para os tipos, os portões e os subagentes.
- **Motion design:** as skills da [iart.ai](https://github.com/iart-ai/motion-design-skills) (MIT) são instaladas junto.
- **Só o vídeo final fica:** `kit.py entregar <id> --destino <pasta>` copia, confere e apaga a montagem.
- **Testes dos portões:** `python3 scripts/teste.py` no estúdio (sem gastar nada), com os portões provados por mutação.
- **Demonstração aprovada antes de gravar:** o plano mostra o caminho na ferramenta (campo `caminho`) e lista o que se
  grava depois do ok; acertar o `de` de uma gravação não pede ok novo.
- **A marca inteira:** fundo claro leva o texto, os painéis e o tom suave junto, e qualquer fonte do Google Fonts entra
  sozinha (`src/fontes.gen.ts`, refeito no `marca` e no `montar`). Fonte fora do Google Fonts é recusada com aviso.
- **Logo da marca** no encerramento de todo vídeo.
- **Mais guardas:** o render recusa com menos de 5 GB livres; a narração de uma parte só se paga de novo quando a fala,
  a voz ou a pronúncia de uma palavra dela muda; o `montar` sempre prepara os dois formatos; o `finalizar --pagina` roda
  de novo sobre um vídeo já finalizado.
- Instalador: `--atualizar`, `--versao`, `--ajuda`, `--sem-motion`, `--sem-marca` e `--transcricao-local`; opção
  desconhecida mostra o uso e para (antes, `--help` rodava a instalação inteira). Tema padrão escuro com
  verde no lugar do champanhe. README com 12 tipos de vídeo em três grupos e o modo autônomo; dois exemplos novos
  (instrução no celular e corte viral narrado).
- Próximas: **2.1** redes (avatar com Higgsfield como principal e HeyGen como alternativa, anúncio demonstrativo, corte
  viral, carrossel e imagem 4:5) e vinheta de marca; **2.2** edição das suas gravações (Screen Studio, Recordly e
  qualquer vídeo) e instrução no celular.

## 1.2.0 · 09/10/2026

- Nome novo: **Claquete.ai** (antes `kit-video-ia`). O repositório virou `dantaspaulo/claquete`; o endereço antigo e o
  `npx github:dantaspaulo/kit-video-ia` continuam funcionando.
- README reorganizado nos quatro tipos de vídeo (demonstração de ferramenta, aula animada, redes e edição de gravação),
  com um exemplo de cada, feitos com o método no ChatADV. Os vídeos de exemplo estão na página desta versão.
- Saíram os exemplos antigos de cor champanhe.
- `package.json` acertado: estava em 1.0.0 enquanto a última versão publicada era a 1.1.0.
- Nada mudou no instalador nem no estúdio: os textos internos deles ainda dizem `kit-video-ia` e mudam na 2.0.

## 1.1.0 · 07/10/2026

- Instalação completa, voz Raquel pronta e fundo de papel de parede.

## 1.0.0 · 07/10/2026

- Primeira versão: skills `aula-animada`, `tutorial-de-tela` e `video-na-pagina` e o estúdio em Remotion.
