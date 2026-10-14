---
name: tutorial-de-tela
description: >-
  Demo of a tool, quick tip, full walkthrough and tool track, recording a real system in the
  Claquete.ai studio. Claude maps the system, writes the usability script and the edit plan (the
  path, where to cut, where to speed up, where to zoom in) for the person to approve, records with
  Playwright (visible cursor, blurred data, forbidden text discards the recording), narrates with
  the ElevenLabs voice, runs the narration and the contact sheet past subagents and delivers the
  reviewed video. Use it whenever the person asks for "video tutorial", "demo", "product demo",
  "how-to video", "record my screen", "step-by-step walkthrough of the system", "feature video",
  "quick tip", "screencast", "onboarding video", "course on the tool", "track", "a case from start
  to finish" or "series showing the system", even without mentioning a recording. For a concept
  lesson with no tool, use aula-animada.
metadata:
  resumo: Demo, tip, walkthrough and track recording a real system
---

# Demo, tip, walkthrough and track

Three steps: **plan** (usability script and edit plan, with the person's ok), **record** the path
through the system (no voice, no rush, with test data) and **narrate on top**, like a lesson whose
screens are clips of the recording. The rules for narration, voice, pacing, the two gates, the
subagents and the delivery are the ones from the aula-animada skill: read it if you haven't yet.
Here is what changes.

## The types

| Type (`--tipo`) | What it is | Duration |
|---|---|---|
| `demonstracao` | one task from start to finish | 1 to 4 min |
| `dica` | one feature only, straight to the point | 30 to 90 s |
| `caso` | series: one case from start to finish, one lesson per step | each lesson 2 to 5 min (`--minutos`) |
| `trilha` | course on one tool, one lesson per feature | each lesson 2 to 5 min (`--minutos`) |

```bash
python3 scripts/kit.py novo cadastro-cliente --tipo demonstracao
python3 scripts/kit.py novo trilha-agenda-03-lembretes --tipo trilha --minutos 3
```

Demo and tip don't take `--minutos`: the range for the type applies, and the duration comes out of
the path.

## Before planning: what to ask

In a single round (the claquete skill may have asked already), with a ready suggestion:
1. **The path**: what the video shows, from start to finish, and the result the viewer wants to
   have.
2. **Where**: the system's address, and whether a login is needed.
3. **Account and data**: test account and dummy data. **Never record with a client's real data.**
4. **What must not show up**: names, emails, amounts, documents. That becomes `esconder` and
   `proibidos`.
5. **Format** (landscape, vertical or both) and, for a case and a track, the duration of each
   lesson.

Also read `marca/marca.json` (tone, audience, glossary, forbidden words, call to action), as in
aula-animada.

## Map the tool

Before writing, get to know the path: open the system, walk through the screens, note down the
selector of each button and field. A dry run with `gravar.mjs` (below) is free and shows whether
each step finds its target. Dry run with the test account only.

### Track: the course on a tool

1. **Map it**: list the tool's features (menus, screens, main actions).
2. **One lesson per feature**, 2 to 5 minutes. Feature too big: split it. Feature too small:
   becomes a `dica`.
3. **Order it by how people learn**: first what you use on day one (sign in, set up, the main
   task), then what depends on that, finally the advanced stuff. No lesson uses something an
   earlier one hasn't shown.
4. **Each lesson is an id**, numbered in order: `trilha-<ferramenta>-01-<recurso>`, `-02-...`.
5. Show the track map (lesson, feature, order, duration) along with the script of the first
   lesson, at gate 1. Each lesson goes through both gates.

### Case: a series from start to finish

- A fictional but believable case, with the same data from start to finish (the same fictional
  client, the same numbers): the series shows continuity.
- One lesson per step of the case, each 2 to 5 minutes, with a numbered id (`caso-<nome>-01-...`).
- Each lesson opens by recalling where the case stopped and closes by saying what comes next.
  Between the recorded steps, animated screens (`fluxo`, `lista`, `frase`) explain the why.
- Record the steps in order: the state of the system at the end of one is the start of the next.

## Gate 1: usability script and edit plan

Everything in a single document, `saida/<id>/roteiro-e-plano.md`, so the person can approve it all
at once. The recording doesn't exist yet at this point, and the studio knows it: `plano` and
`aprovar` treat the missing `video` or `imagem` screen file as a warning, and `montar` is what
refuses it.

**Usability script**: what the viewer wants to do, where they start from, each step (one action
per step), the expected result, and the common mistake or limit worth flagging.

**Edit plan**, part by part:
- **the path**: which clip of the recording the part shows;
- **where it cuts**: each part starts at a `de` (the second of the recording). The stretch between
  the end of one part and the `de` of the next doesn't appear: waits, loading and long typing stay
  out;
- **where it speeds up**: `velocidade` (1.5 or 2, for example) on whatever must appear but is slow;
- **where it zooms in**: `zooms`, with the `foco` on the field, button or result, on the word where
  the voice says it.

How to put it together:
1. Write the recording script (`gravar/<nome>.json`, below) and the lesson file
   (`aulas/<id>.json`), with the `video` screens pointing to the recording that doesn't exist yet
   (`gravacoes/<nome>.mp4`), each with its provisional `de`, `velocidade` and `zooms`. Open with a
   `capa` (what the video shows) and close with a `lista` or a `frase` (what to remember). At the
   top of the JSON, set the `caminho`: the list of steps in the tool, in plain words (template in
   `aulas/tutorial-exemplo.json`).
2. `python3 scripts/kit.py validar <id>`. Before recording, the missing recording file comes out as
   a warning, not as an error. The program prints "parte N: arquivo gravacoes/<nome>.mp4 não existe
   em public/ (grave depois do ok do roteiro)": the file is missing, record after the script is ok.
3. **Script reviewer**: the aula-animada subagent (strongest model written in the request), with
   three more items: every step of the path has its part; no step shows real data; `esconder` and
   `proibidos` cover everything the person said must not show up.
4. `python3 scripts/kit.py plano <id>` writes the plan: the **Caminho na ferramenta (o que será
   gravado)** section, coming from the `caminho`, and then the parts with the edit plan of each one.
   The **A gravar depois do ok** section lists the files that will be recorded. The account and
   dummy data used, what gets blurred (`esconder`) and what discards the recording (`proibidos`)
   live in the recording script, not in the lesson file: tell the person about them when showing the
   plan (or list them as items of the `caminho`, so they go into the ok).
5. Show it to the person. The files under "A gravar depois do ok" are expected: explain that the
   recording comes after the ok. **Stop and wait.**

The ok covers the path, the narration, the cuts, the speed-ups and the zooms. The `caminho` goes
into the signature of the ok: change one step and it asks for a new ok. The `de` of the `video`
screens doesn't: swapping the provisional `de` for the real second from the marks is executing the
approved plan, and the ok still holds. Any other change (a narration line, a step, a cut, a zoom)
goes back to the person before `aprovar`.

## Record

Script in JSON (template in `gravar/exemplo.json`, which records the demo page into `gravar/demo/`):

```json
{
  "nome": "cadastro-cliente",
  "largura": 1280, "altura": 720, "escala": 1,
  "sessao": "sessao.json",
  "esconder": [".email-do-usuario", "#saldo"],
  "proibidos": ["@empresa.com.br", "CPF"],
  "passos": [
    { "ir": "https://sistema.exemplo.com/clientes", "esperar": 1000, "marca": "lista" },
    { "clicar": "text=Novo cliente", "marca": "novo" },
    { "digitar": { "em": "#nome", "texto": "Maria Exemplo", "atraso": 40 } },
    { "escolher": { "em": "#plano", "valor": "anual" } },
    { "clicar": "button[type=submit]", "esperar": 2000, "marca": "salvo" }
  ]
}
```

```bash
cd estudio-video
npx playwright install chromium        # once (the installer offers it)
node gravar/gravar.mjs gravar/<roteiro>.json
```

- Steps: `ir`, `clicar`, `pairar`, `digitar` (`atraso` in ms per letter), `escolher`, `apertar`
  (key), `rolar` (pixels), `esperar` (ms). Without `esperar`, each step waits 350 ms.
- The cursor appears and moves to each target; the click sinks in.
- **`esconder`** blurs the selectors in the recording. **`proibidos`**: if one of those texts shows
  up on the screen, the recording is **discarded** and the program exits with code 3. Adjust and
  record again.
- The `proibidos` guardrail reads the page text after each step. It doesn't see what was typed
  inside a field, what is in an image, or what appears and disappears between two steps. That's why
  the contact sheet also looks for sensitive data.
- **Login**: record the session beforehand (`npx playwright codegen --save-storage=sessao.json
  <url>`) and point `"sessao"` at it. Never put a password in the script. The session file
  (`sessao*.json`) doesn't go into the repository.
- The recording browser is Playwright's own. Ask the person to leave the machine free and close
  anything heavy: a loaded machine records choppy. Check the disk before recording (on macOS and
  Linux, `df -h .`; the recording doesn't go through `kit.py`); with less than 5 GB free, stop and
  warn. The render afterwards refuses by itself below that.
- It writes `public/gravacoes/<nome>.mp4` and `<nome>.marcas.json`: the second each step started
  at, with the `marca` you gave.

## After recording: fixing the plan

1. Swap each provisional `de` for the second of the step in `public/gravacoes/<nome>.marcas.json`
   (a bit earlier, if the part should show the cursor arriving).
2. Check each step in a frame of the recording: the click landed, the response loaded, nothing real
   showed up.
   ```bash
   mkdir -p saida/<id>/quadros
   ffmpeg -ss <segundo> -i public/gravacoes/<nome>.mp4 -frames:v 1 saida/<id>/quadros/passo-1.jpg
   ```
3. The part can't go past the end of the recording: `de` + (narration duration × `velocidade`) fits
   in what's left. The exact duration only comes out in the narration; estimate about 0.36 s per
   word.
4. `kit.py validar <id>`: now the recording file exists, and `montar` requires it. If only the `de`
   changed, the previous ok still holds, with no new `aprovar`. If more than that changed (a
   narration line, a step of the `caminho`, a cut, a zoom): show the person the difference, then
   `plano` and a new ok.

## Narrate on top

`video` screens pointing to the recording (template: `aulas/tutorial-exemplo.json`):

```json
{ "fala": "Next, choose the yearly plan.", "rotulo": "Step 2",
  "tela": { "tipo": "video", "arquivo": "gravacoes/cadastro-cliente.mp4", "de": 4.6,
            "velocidade": 1.5, "legenda": "Choose the plan",
            "zooms": [{ "quando": "plan", "foco": [0.15, 0.3, 0.85, 0.6] }],
            "chips": [{ "texto": "yearly plan", "quando": "yearly" }] } }
```

- **One part per step** of the recording. The narration says what to do and why, it doesn't
  describe the obvious ("click the blue button").
- `legenda` is the label inside the window; the chips (`chips`) also go into the window.
- **Zoom whose focus includes the whole element**: the rest darkens (spotlight). If the focus cuts
  a field in half, widen the focus. The camera zooms in at most 3x.

### Landscape and vertical: the zoom moves

The `foco` is measured in the window, and the window changes with the format. A 16:9 recording
(1280×720) fills:
- **landscape**: the full height, and the width from 7.7% to 92.3% of the window;
- **vertical**: the full width, and only the strip from 25% to 75% of the height.

For a target that sits, in the recording, at fraction `a` of the width and `b` of the height (from
0 to 1):
- landscape: `x = 0.077 + 0.847 × a` and `y = b`;
- vertical: `x = a` and `y = 0.252 + 0.496 × b`.

The same file doesn't get both right. Only one format: use its math. Both, with a good zoom in
each:
1. Do the landscape one with the normal id, until it passes gate 2.
2. Copy the file to `aulas/<id>-empe.json`, with the converted focuses. The vertical frame has
   little room: focus on one field, one button, one stretch of the response; a wide focus barely
   moves in.
3. Copy `public/aulas/<id>/parte-*.mp3` and `parte-*.json` to `public/aulas/<id>-empe/`: `narrar`
   recognizes the same narration, voice and pronunciation and doesn't pay again.
4. The copy goes through the gates like the others: `plano <id>-empe`, show it to the person (only
   the focuses changed), `aprovar <id>-empe` with the ok, and `conferir <id>-empe` (the narration
   reviewer checks the same audio).
5. `--formatos h` on the original and `--formatos v` on the copy (in `renderizar`, in `finalizar`
   and in `fazer`; `montar` always prepares both).

Another option: record again in a narrower window (`largura` 900, `altura` 1000, for example), which
fills the vertical frame better. Then the vertical cut has its own recording and `de`.

## Gate 2, assembly and delivery

The same as in aula-animada: `fazer <id> --formatos ...` narrates and stops at gate 2; the narration
reviewer checks `public/aulas/<id>/conferencia.json`; `conferir <id> --aprovado`; `fazer` again
assembles, renders and finalizes; the sheet reviewer looks at the frames; you show the video to the
person and, with the ok, `entregar`.

### Pacing in the recording

The pacing review in `montar` doesn't apply to `video` screens (the recording already moves). The
static screen meter in `finalizar` does apply, and it measures the window only: a recording that
stands still for 2.5 s or more (waiting to load, someone reading) is refused. Solve it in the plan
already: cut with `de`, speed up with `velocidade`, or put a zoom or a chip on the right word.

### Tip: short video, for the feed

- One idea, one feature. The first sentence states the viewer's gain; then it shows it; it closes
  with the brand's call to action.
- Vertical (`v`) for Reels, TikTok and Shorts, 30 to 90 s.
- With music (`trilha.arquivo` in `kit.config.json`), the beat-sync-editing skill helps pick the
  music and place cuts (`de`) and zooms near the beats. The timing is still the voice's. The track
  goes into `montar`: you can add the music, assemble the tip and put the track back to what it
  was.
- Direction, composition and palette: the same motion design skills as in aula-animada.

### Contact sheet and privacy

The sheet reviewer (subagent with a fast model written in the request) looks at
`saida/<id>/<id>-h-folha.jpg` (and the vertical one) as in aula-animada, and here looks with extra
care for:
- **sensitive data**: name, email, phone, document, amount, address in the browser bar,
  notification that popped up on the screen;
- **zoom**: focus in the right place, whole element in the light, no black bar in the vertical
  frame;
- a loading or error screen left in the cut.

Sensitive data found doesn't go into the delivery: put it in `esconder` or `proibidos` and record
again. Tell the person what showed up and what changed, fix the `de` from the new marks (no new ok
needed) and run from `montar` on. If the finding also changed a step, a cut or a zoom, that stretch
goes back to the person and asks for `aprovar`. The narration doesn't change, so the voice isn't
generated again.

## Delivery

- The same as aula-animada: the video ready for the person, the ok, `entregar <id> --destino
  <pasta>`.
- Tell the person what was hidden or replaced with dummy data.
- The recording stays in `public/gravacoes/` (`entregar` doesn't delete it). It's large and only
  useful for assembling again: ask whether you can delete it, and only one that no other lesson
  uses (in a case or a track, several lessons may use the same one).
- For a product page or help center: the video-na-pagina skill, before `entregar`.

## Privacy, in short

- Test account and dummy data, always. Never a client's real data.
- Never a password in the script; log in through the session file, which doesn't go into the
  repository.
- `esconder` for what may show up blurred; `proibidos` for what must not show up at all.
- Discarded recording (code 3): adjust the path and record again. Never remove a text from
  `proibidos` just to pass.
- The sheet reviewer looks for sensitive data in every video, and the finding goes back to the
  recording, never to the delivery.
