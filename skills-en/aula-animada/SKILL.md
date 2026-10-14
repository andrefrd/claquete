---
name: aula-animada
description: >-
  Creates a 2 to 5 minute NARRATED ANIMATED LESSON, with the duration chosen by the person, in the
  Claquete.ai studio: a script in parts in the brand's tone and glossary, one idea per screen, an
  ElevenLabs voice, word-for-word captions, screens that come in on the second the voice says the
  word, and motion direction with the motion design skills. It works on its own and stops at two
  gates (the script and edit plan before narrating; the narration review by a subagent before
  assembling), checks pacing, duration and sound, and delivers the landscape and/or vertical video,
  deleting the assembly. Always use it when the person asks for "narrated lesson", "animated
  lesson", "lesson in a video", "video lesson", "explain a concept in a video", "educational video",
  "lesson for the help center", "lesson series" or "turn this text into a lesson", even if they
  don't say "animated". To show a tool working, use tutorial-de-tela.
metadata:
  resumo: Narrated and animated lesson of 2 to 5 min, from topic to delivered video
---

# Narrated animated lesson

The result is a short lesson: a window with the screen of the moment, the label above it, the
word-for-word captions below, and the voice carrying it. Every element comes in **on the second the
voice says its word**, and nothing stays still for more than 2.5 s. It all comes from a single file,
`aulas/<id>.json`, through the studio (the folder with `kit.config.json`; the installer creates
`estudio-video/`). Every command runs from inside it.

Claude does everything on its own and stops only at **gate 1** (script and edit plan), at **gate 2**
(narration review) and at **delivery**.

## Before you write

1. **Read the brand** in `marca/marca.json`: `publico`, `tom`, `glossario`, `palavras_proibidas`,
   `chamada` and `movimento`. Without the file, the lesson comes out in the default look; offer
   "configure my brand" (the claquete-marca skill).
2. **Ask everything in one round** — whatever the request and the brand don't answer (the claquete
   skill may have asked already), with a ready suggestion:
   - **topic and audience**: who watches and what they need to walk away knowing, in one sentence;
   - **duration**: 2, 3, 4 or 5 minutes, the person chooses;
   - **format**: landscape (`h`, for a website, YouTube, a help center), vertical (`v`, for Reels and
     phones) or both;
   - **source**: their text, article or notes. Facts and numbers only come in with a source.
3. **Create the file**: `python3 scripts/kit.py novo <id> --tipo aula --minutos 3` (id in lowercase
   letters, numbers and hyphens).

## The right length

`montar` refuses a lesson more than 20% off the chosen duration, above or below, and outside 2 to 5
minutes. `plano` shows the estimate before any spending. The real voice comes out a little faster
or slower than the estimate: aim for the middle of the range.

| Duration | Accepted range | Aim for | Parts |
|---|---|---|---|
| 2 min | 120 to 144 s | about 340 words | 11 or 12 |
| 3 min | 144 to 216 s | about 470 words | 15 or 16 |
| 4 min | 192 to 288 s | about 620 words | 20 or 21 |
| 5 min | 240 to 300 s | about 700 words | 23 or 24 |

The numbers assume the default voice speed (1.1) and the 4 s invite at the end. Over 5 minutes:
split it into two lessons.

## The lesson file

`aulas/<id>.json`. Full template in `aulas/exemplo.json`.

```json
{
  "titulo": "Lesson name",
  "cabecalho": "Series · Lesson 1",
  "tipo": "aula",
  "minutos": 3,
  "destaques": ["words", "that", "come", "out", "colored", "in", "the", "captions"],
  "partes": [
    {
      "fala": "What the voice says on this screen.",
      "rotulo": "Label above the window",
      "tela": { "tipo": "lista", "kicker": "Label", "titulo": "Title with *emphasis*",
                "itens": [{ "texto": "one", "quando": "word" }, "two", "three"],
                "chips": [{ "texto": "chip", "quando": "other" }] }
    }
  ]
}
```

| type | fields | what it's for |
|---|---|---|
| `capa` | `kicker`, `titulo`, `sub` | opening |
| `lista` | `kicker`, `titulo`, `itens` (up to 5) | the points of one idea |
| `colunas` | `titulo`, `esquerda` and `direita` (`titulo`, `itens`) | before and after, this and that |
| `fluxo` | `kicker`, `titulo`, `passos` (up to 5), `nota` | steps in sequence |
| `frase` | `kicker`, `titulo`, `sub` | a strong statement |
| `numero` | `kicker`, `de`, `para`, `legenda` | a number that counts up to the value |
| `imagem` | `arquivo` (in `public/`), `legenda`, `zooms` | a photo or illustration |
| `video` | `arquivo`, `de`, `velocidade`, `legenda`, `zooms` | a screen recording (tutorial-de-tela skill) |
| `animada` | `descricao`, `cena` (default `Cena<N>`), `chips` | a React scene, the richest screen (see "Animated screens") |

- `*text*` in the title gets emphasis.
- **`quando`** ties the entrance to the spoken word (`"word"`, or `"word#2"` for the second time).
  Without `quando`, the items spread evenly across the narration.
- **`chips`** are chips that come in on the spoken word: the simplest way to put something new on
  screen.
- **`zooms`**: `{ "quando": "word", "foco": [x0, y0, x1, y1], "ate": "word" }`, with the focus in
  fractions of the window. The camera frames the whole focus and darkens the rest (it never cuts it
  in half).

## How to write the narration

- **One idea per part**, 20 to 40 words (8 to 14 s).
- First part: what the lesson shows and why it matters to the audience. Last one: the recap and the
  bridge to the brand's call to action, which the end invite shows.
- The screen **summarizes** the narration, it doesn't repeat it: a short title, items of a few
  words.
- **In the brand's tone** (`tom`). With no brand: the tone of someone explaining to a colleague,
  short sentences, second person, no unexplained jargon.
- **Glossary**: the term appears as it is, in the narration and on screen, never swapped for a
  synonym, not even to vary.
- **Forbidden words**: not in the narration (`validar` refuses) and not on screen (nothing refuses:
  check it yourself).
- State the limitation clearly (what the thing doesn't do). Facts and numbers only with a source.
- **No em-dash** (the voice reads it badly; `validar` refuses it in the narration and in the
  on-screen text).

### Writing for the voice (what the narration review rejects)

- A year written as digits (`2022`), not spelled out.
- Words that sound alike ("there" and "their"). Swap the construction out ("the reasons").
- An ambiguous article: "it's the model" can sound like "it's a model". Change the sentence.
- Agreement the way the voice will say it ("the AI was fast").
- Acronyms and foreign names: put the pronunciation in `kit.config.json` → `pronuncia`
  (`"AI": "ay-eye"`) **before narrating**. Changing a word's pronunciation later only requires
  re-narrating the parts that use that word (see "Changed after the ok").
- A word the transcriber always writes differently and that the voice says right (a brand name):
  `travas.aceitar` (`"Wize": "wise"`).

## Pacing: nothing still for more than 2.5 s

Every 2.5 s at most, something **new** on screen: an item coming in, a chip, a number counting, a
zoom. Pulsing and floating don't count. Two guardrails:
1. `montar` works out from the narration timings when each element comes in and **refuses** the
   part that goes more than 2.5 s with nothing new, saying where.
2. `finalizar` measures the finished video (only the window area, without the captions) and refuses
   a static screen.

Solve it in the script, before gate 1: **roughly one new thing every 5 spoken words** (2.5 s of
voice is about 6 words). A `quando` on every item, chips where the narration runs on with no new
item, or the part split in two. That way `montar` won't refuse after the ok.

## Motion direction

With the motion design skills from iart.ai (the installer brings them along). They decide; the
studio executes with what it already has: screen type, `quando`, chips, zooms, colors and
background.

- **motion-art-direction**, before the script: turn the brand's `movimento` and `tom` into three or
  four rules that hold for the whole lesson, so everything looks like it came from the same hand.
  - Restrained: only the chips the pacing calls for, a rare zoom, more `lista` and `fluxo`.
  - Dynamic: shorter parts, more chips, `numero` and `colunas` to turn the page.
  - Editorial: `capa` and `frase` with a strong title and `*emphasis*`, few items per screen.
- **shot-composition**: one point of attention per screen; a short title that also fits the vertical
  format (the vertical window is narrow); the zoom's `foco` takes the whole element.
- **animation-principles**: space the entrances out. Items all arriving at the end of the
  narration, or three in the same second, wear the viewer out. One entrance every 1 to 2.5 s is the
  studio's rhythm.
- **color-motion**: the brand palette with contrast (text over the window, emphasis over the
  background) and the supporting tones (details in the claquete-marca skill).
- **logo-animation**: the brand sting. Today it stands on its own; the studio doesn't fit it into
  the start and end of lessons (the vinheta type arrives in 2.3). The brand logo already appears in
  the closing.
- **hairline-create**: the isometric line drawing, when the `animada` screen calls for a figure and
  not a whole scene. The 33 figures from `@lucasmarkes/hairline` (MIT) are already in `cenas/`;
  prefer the ready-made piece to drawing from scratch, and write a new figure only if none of them
  fits.
- An illustration, visual metaphor or animation the ready-made types don't do: use the `animada`
  screen (below), not new code in `src/cenas/` (the installer's `--atualizar` replaces the `src/`
  folder).

## Animated screens (React scenes)

The `animada` screen is the richest: a React scene with motion and the React Bits components the
installer downloaded onto the person's machine, photographed frame by frame with the page clock
controlled, on the second of each spoken word, landscape and vertical. Use it in the parts that call for
an illustration (a concept, a metaphor, a conversation, a document, a number) and leave `lista`,
`fluxo` and `frase` for the rest: a good lesson mixes the two.

**In the script (before the ok):** `{"tipo": "animada", "cena": "Cena3", "descricao": "what the scene
shows"}`. The `descricao` is what the person approves at gate 1: say what comes in and on which word
("the document writes itself; size, tone and structure get a check when they're said"). The scene
code **doesn't exist yet**: the plan lists the scenes to write.

**After the ok and the narration review**, write `cenas/src/aulas/<id>.jsx` (full template:
`cenas/src/aulas/animada-exemplo.jsx`):

```jsx
import { Cena, Documento, Item, Placa, useArea, C } from "../ilustra.jsx";

export function Cena3({ b }) {           // b("word") = the second in the scene when the voice says the word
  const { w, h } = useArea();            // the camera area: it changes from landscape to vertical
  return (
    <Cena kicker="2 · Format" titulo="Show the *format*" texto="Size, tone and structure." textoEm={b("size,")}>
      <Documento em={b("example")} largura={w * 0.32} style={{ position: "absolute", left: w * 0.06, top: h * 0.08 }} />
      <Item em={b("size,")} marca={b("size,") + 0.3} texto="Size" icone="Ruler" />
    </Cena>
  );
}
```

- **`<Cena>`**: the text (kicker, title, supporting text, `lado`) stays fixed outside the camera and is
  never cut; the children sit in the camera area, in its coordinates (0,0 in the corner). Landscape: text
  on the left and an area of ~790 x 610 on the right (with `cheia`, the title on top and the area across
  the full width). Vertical: text on top and an area of 800 x ~600 below. **Position in fractions of `w`
  and `h`**: the same scene comes out in both formats.
- `animado` uses React Bits' animated text in the title; `fundo="aurora" | "particulas" | "feixes"` puts
  in a living background.
- **Camera:** `quadros={[[b("word"), { s: 1.3, foco: [x0, y0, x1, y1] }, 0.6], [b("other"), { s: 1 }, 0.4]]}`.
  Every zoom has a `foco` (in area coordinates), which comes in whole; the rest darkens.
  `tremores={[b("impact")]}` shakes it.
- **Pieces** (`cenas/src/ilustra.jsx`, in the brand's colors and fonts): `Surge`, `Depois` (builds between two
  seconds), `Titulo`, `TituloRB`, `Texto`, `Kicker`, `Pilula`, `Cartao`, `Item` (with a check), `ListaViva`,
  `Balao`, `Digitando`, `Escreve`, `Digita`, `Documento`, `Agente`, `Selo`, `Anel`, `Fio`, `Cronometro`,
  `Tecla`, `Assinatura`, `Carimbo`, `NumeroGrande`, `Contador`, `Placa`, `Gira`, `TextoVeloz`,
  `TextoBrilho`, `TextoGradiente`, `Decifra`, `Palavrao`, `Explosao`, `Chuva`, `Velocidade`, `Holofote`,
  `Flutua`, `Orbe`, `Globo`, `FundoVivo`.
- **React Bits:** the pieces `Orbe`, `FundoVivo`, `Contador`, `Gira`, `Digita`, `TextoBrilho`,
  `TextoGradiente`, `TituloRB`, `TextoVeloz`, `ListaViva` and `Globo` use the React Bits component when it's
  in `cenas/src/components/react-bits/` (the installer downloads it; with the Pro license, six more) and
  fall back to a version of their own when it isn't. You can use a component directly: `import { RB } from
  "../rb.js"` and `<RB.Aurora ... />`, always with a plan B (`RB.Aurora ? ... : ...`), because someone
  else's studio may not have it. **Never copy a React Bits component out of that folder, and never send it
  to anyone**: the license doesn't allow redistribution.
- **Pacing:** one new thing every 2 s, tied to the words (`b("...")`). Pulsing and floating don't count.

**Check and photograph:**
1. `python3 scripts/kit.py cenas <id> --previa`: five shots of each scene, landscape and vertical, in
   `saida/<id>/previa-NN-h.jpg` and `previa-NN-v.jpg`, plus the cut guard. **Preview reviewer:** a subagent
   with a fast model named in the request (sonnet) opens the images and points out cut-off text, overlapping
   pieces, too much empty area, color off the brand, and anything that doesn't match the approved
   `descricao`. Fix it and take the preview again.
2. `python3 scripts/kit.py cenas <id>`: the full capture (about 13 s of machine time per second of scene, in
   both formats). It refuses a scene error, a word the narration doesn't have, a piece cut in half at the
   camera edge, an empty frame and a static screen. `fazer` runs this on its own for the pending scenes.
3. `montar` refuses an animated screen that hasn't been photographed or that changed afterwards (scene code,
   components, voice timing, duration, theme): photograph just that part again (`cenas <id> --partes 3`).

If the capture says it couldn't open the browser: `npx playwright install chromium` in the studio (or
`CLAQUETE_CHROMIUM=<path to a Chrome>`). Without the scenes app (`cenas/node_modules`): `cd cenas && npm install`.

## The flow

### 1. Script and review

- Write `aulas/<id>.json` and run `python3 scripts/kit.py validar <id>` (free) until there's no error.
- **Script reviewer**: a subagent with a stronger model named in the request (opus, for example),
  because the task calls for judgment. Never inheriting the session's model. Pass it the lesson
  file, `marca/marca.json` and the source. It returns, part by part:
  - a fact or number with no source;
  - off the brand's tone or the audience's level;
  - a glossary term swapped for a synonym; a forbidden word in the narration or on screen;
  - a sentence that's hard for the voice (words that sound alike, a year, an acronym with no
    pronunciation, an ambiguous article);
  - a screen that repeats the narration instead of summarizing it;
  - a stretch of more than about 6 words with nothing new on screen;
  - an estimated duration far from the middle of the range.
- Fix everything and validate again.

### 2. Gate 1: script and edit plan

- `python3 scripts/kit.py plano <id>` generates `saida/<id>/roteiro-e-plano.md`: every part with the
  narration, the screen, what comes in on each word, the chips and the zooms, and the estimated
  duration. An `imagem` or `video` screen with a file that doesn't exist yet is just a warning here
  (section "A gravar depois do ok", to record after the ok); `montar` refuses it.
- Show the person the content in the conversation, not just the file path. **Stop and wait.**
- With the ok: `python3 scripts/kit.py aprovar <id>`. Asked for a change: change it, generate the
  plan again and show it once more.

### 3. Narrate

`python3 scripts/kit.py fazer <id> --formatos h,v` narrates each part on ElevenLabs (the paid part)
and stops at gate 2 (code 2). A part already voiced with the same narration text, voice and
pronunciation isn't narrated again.

### 4. Gate 2: narration review

`conferir` (`fazer` already runs it) generates `public/aulas/<id>/conferencia.json`. For each part:
- `fala` (the script) and `falado` (what went to the voice, with `pronuncia` applied);
- `audio` and `duracao`;
- `alertas`: words that sound alike, a year in the text, an acronym with no pronunciation;
- with local transcription (faster-whisper, which the installer offers): `ouvido`, `similaridade`
  (0 to 1), `diferencas` and `situacao`: `ok` (from `travas.similaridade_minima`, 0.9), `revisar`
  (from 0.75 up to there: the subagent decides) or `reprovada` (below 0.75: `--aprovado` refuses).
  Simple numbers spelled out and in digits ("two" and "2") count as equal.

**Narration checker**: a subagent with a fast model named in the request (sonnet, for example):
it's a checklist-driven review. It doesn't listen; it reads. It returns each part as approved or
rejected, with the reason and the fix:
- **Exact narration**: does `ouvido` say the same as `fala`? A difference that changes the meaning
  rejects it. A difference of spelling only ("e-mail" and "email") doesn't.
- **Pronunciation and acronyms**: an acronym or foreign name the transcriber wrote wrong means the
  voice said it wrong.
- **Years**: read as a number.
- **Words that sound alike** (`alertas`): does the meaning survive from hearing alone?
- **Glossary**: every term said as it is.
- **Duration**: far from about 0.36 s per word (a strange pause, a cut stretch) calls for a listen.

With no local transcription, `ouvido` comes back empty. The subagent checks the text side (`falado`,
`alertas`, glossary), and **the person listens to the audios listed in the report** before the ok.
Say which parts it flagged for a careful listen.

- **Approved**: `python3 scripts/kit.py conferir <id> --aprovado`.
- **Rejected**: fix it and narrate only that part. Never loosen the guardrail.
  - Pronunciation, acronym or year: fix `kit.config.json` → `pronuncia`. The script doesn't change:
    `python3 scripts/kit.py narrar <id> --partes 3` and `conferir <id>` again.
  - A sentence that has to change (words that sound alike, an ambiguous article, a flipped meaning):
    rewriting changes the approved script, and `narrar` refuses. Show the person the sentence before
    and after; with the ok, `aprovar <id>`, `narrar <id> --partes 3` and `conferir <id>`.
  - The transcriber writes a word the voice says correctly differently: `travas.aceitar`. Only when
    the audio is right.
- `--aprovado` refuses if any part came out `reprovada`, or if the narration changed after the
  report.

### 5. Animated scenes (only if the lesson has an `animada` screen)

Write the scenes and photograph them (section "Animated screens"): preview, preview review by a
subagent, capture. `fazer` photographs the pending ones on its own, but the reviewed preview comes
first.

### 6. Assemble, render, finish

- `python3 scripts/kit.py fazer <id> --formatos h,v` again (it skips the voice and the review already
  done), or part by part: `montar`, `renderizar`, `finalizar`. `montar` always prepares both formats;
  `--formatos` (default `h`) applies to `renderizar` and `finalizar`.
- `montar` refuses: a `quando` word the narration doesn't have; more than 2.5 s with nothing new (it
  says the part and the second); a duration outside the range.
- `finalizar` normalizes the sound to -14 LUFS, generates the `.vtt` and `.srt` captions and the
  contact sheet, and refuses a static screen in the finished video. It deletes the raw render file,
  but it runs again over the already finished video (without the raw file, and without normalizing
  the sound again). With no render at all, it stops with "não há render" (there is no render): that's
  when you render.
- To see it in the browser before the render: `npm run studio`, after `montar`.

### 7. Contact sheet review

`saida/<id>/<id>-h-folha.jpg` (and `<id>-v-folha.jpg`): 16 frames from the video. **Sheet reviewer**: a
subagent with a fast model named in the request (sonnet, for example), which opens the images and points out:
- cut-off text, spilling out of the window or wrapping badly;
- an empty screen;
- a bad zoom (the focus cuts an element);
- captions over something important;
- a color, font or logo off the brand;
- sensitive data.

To see an exact moment, it pulls a frame. The second is in `public/aulas/<id>/plano.json` (the part's
`inicio` plus the word's `ini`):

```bash
mkdir -p saida/<id>/quadros
ffmpeg -ss <segundo> -i saida/<id>/<id>-h.mp4 -frames:v 1 saida/<id>/quadros/q1.jpg
```

Fix what it points out and run from `montar` onward.

### 8. Changed after the ok

- **Any change to the lesson file after `aprovar`**, even a chip or a zoom focus: show the person
  just the difference and ask for a new ok; with it, `aprovar <id>` again. `fazer` and `narrar` stop
  in the meantime.
- A screen-only change doesn't generate the voice again: run from `montar` onward.
- A narration change: narrate only the changed parts (`narrar <id> --partes 2,5`), then `conferir`.
- **Watch the cost**: changing the `voz` (or the model) changes the signature of **every** part.
  After that, narrate only with `--partes` and continue with `conferir`, `montar`, `renderizar` and
  `finalizar` separately. `fazer`, and `narrar` without `--partes`, would narrate the whole lesson
  again. Changing the `pronuncia` of one word, on the other hand, only changes the parts whose
  narration uses that word: `narrar` without `--partes` redoes just those.

### 9. Delivery

- Show the finished video (`saida/<id>/<id>-h.mp4`, `<id>-v.mp4`), the duration and what the reviews
  found and fixed. **Stop and wait for the ok.**
- Going on a page? Generate the lightweight version before delivering (video-na-pagina skill).
- With the ok: `python3 scripts/kit.py entregar <id> --destino <pasta>`. It copies the final video,
  the captions and the page versions, checks the copy and deletes the assembly (`public/aulas/<id>/`
  and `saida/<id>/`). The final video and the lesson file stay. Redoing it later narrates again, and
  the voice is paid for.

## Commands

```bash
cd estudio-video
python3 scripts/kit.py novo <id> --tipo aula --minutos 3
python3 scripts/kit.py validar <id>                     # free
python3 scripts/kit.py plano <id>                       # gate 1: show it and wait for the ok
python3 scripts/kit.py aprovar <id>                     # only with the person's ok
python3 scripts/kit.py fazer <id> --formatos h,v        # narrates and stops at gate 2
python3 scripts/kit.py conferir <id> --aprovado         # after the narration review
python3 scripts/kit.py cenas <id> --previa              # animated screens: shots to check the design
python3 scripts/kit.py cenas <id>                       # animated screens: the full capture
python3 scripts/kit.py fazer <id> --formatos h,v        # assembles, renders and finishes
python3 scripts/kit.py entregar <id> --destino <pasta>  # after the ok on the finished video
```

Part by part: `narrar <id> [--partes 2,5]`, `conferir <id>`, `montar <id>` (always h and v),
`renderizar <id> --formatos h,v [--concorrencia 2]`, `finalizar <id> --formatos h,v [--pagina]`.
Exit code 2 is a gate (message `AGUARDANDO`, waiting); 1 is an error (`PAROU`, stopped).

## The voice

- ElevenLabs only. The only key is `ELEVENLABS_API_KEY`, in the studio's `.env` (the installer
  creates it) or in the environment; never in a versioned file.
- It ships with **Raquel**, a public voice in Brazilian Portuguese, on the `eleven_v4` model. The
  brand voice (`voz.voice_id` in `marca.json`) comes in with `kit.py marca`. `python3 scripts/kit.py
  voz` checks the voice on the account and generates `saida/teste-voz.mp3`.
- `voz.velocidade` (default 1.1) is applied after synthesis, and the word timings follow along.
  `pausa_entre_partes`: 0.35 s.
- ElevenLabs charges per character. A 3 minute lesson has about 2,500.

## The look

- `kit.py marca` carries the brand's colors, fonts, name, logo, invite and forbidden words into the
  `kit.config.json`, derives the supporting tones from the background (a light one gets dark text)
  and generates the Google Fonts links on its own. What it doesn't get right (the contrast check) is
  in the claquete-marca skill.
- `tema.fundo_imagem`: the blurred photo behind the window (ready-made: `fundos/champagne.jpg`,
  `fundos/oceano.jpg`, `fundos/esmeralda.jpg`; empty = gradient lights in the brand colors).
- Background music: `trilha.arquivo` (a file in `public/`) and `trilha.volume` (default 0.07).
- No recording app needed: the window, shadow, background and zoom come from the studio itself.

## Time and machine

- Narration: 1 to 2 minutes. Render: about 1 minute of machine time per minute of video, per format
  (`--concorrencia 2` keeps the machine lighter). One lesson at a time.
- `renderizar` refuses on its own with less than 5 GB free, and `validar` and `plano` warn. Before
  recording a screen (the Playwright recording doesn't go through `kit.py`), check the disk (on macOS
  and Linux, `df -h .`) and, with less than 5 GB free, stop and warn.
