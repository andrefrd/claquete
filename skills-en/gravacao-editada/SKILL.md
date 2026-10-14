---
name: gravacao-editada
description: >-
  Edits a Screen Studio 4 recording (screen, camera and microphone) without opening the app and
  without an API, into three versions: the edited one (no filler words, repeats, false starts or
  waits, with zoom, cursor, camera in the bubble and captions of what you hear), the hybrid one (the
  narration rebuilt into an order of reasoning, the screen with the Screen Studio finish and lesson
  scenes over the voice) and the vertical cuts for Reels, TikTok and Shorts (up to 90 s, at 1.3x,
  hook, proof and invite). Transcribes on your own computer, proves every splice by transcribing
  before and after the cut and stops at two gates. Use it whenever the person says "edit my
  recording", "Screen Studio", "cut the ums and the you knows", "cut the pauses", "make it dynamic",
  "rebuild the reasoning", "hybrid version", "cuts for Reels from my recording", "viral cut of my
  recording" or sends a .screenstudio folder.
metadata:
  resumo: Screen Studio recording edited, hybrid and in vertical cuts
---

# Edited recording, hybrid and vertical cuts

The person recorded in Screen Studio 4 (screen, camera and microphone) and wants the video ready.
Claude transcribes the narration on the computer, decides what goes out, proves every splice, shows
the plan, and the studio builds three versions from the same recording:

| Version | What it is | Command |
|---|---|---|
| **edited** | the recording in the order it was made, without filler words, repeats, false starts and waits; zoom, cursor, clicks, camera in the bubble and captions of what you hear | `montar` |
| **hybrid** | the narration rebuilt into an order of reasoning (problem, solution, uses, demos, what's next), the screen with the Screen Studio finish and lesson scenes over the voice | `hibrido` |
| **vertical cuts** | each cut joins clips into a short narrative (hook, proof, invite), up to 90 s, at 1.3x, the screen in a card with a tighter zoom | `reels` |

The Screen Studio project is only read. The assembly goes to `saida/edicoes/<id>/`, and the only new
file outside it is the copy of the slices (`fatias`), next to the project.

## What you need

- **Screen Studio 4.x**, with the recording in a single session (a paused recording becomes several
  sessions, and this version refuses it). Project saved in 3.x: open and save it in 4.x first.
- **A word transcriber, on the computer.** Screen Studio 4 ships one (Apple's speech, which asks for
  macOS 26 or newer) and the studio uses it on its own. Without it, or on an older macOS, the studio's
  local transcription (`npx github:dantaspaulo/claquete --atualizar --transcricao-local`) with
  `CLAQUETE_TRANSCRITOR=whisper`. No API, no key.
- About 10 GB free on the system disk: the render refuses below 5 GB.

## Before you start: what to ask

In a single round, with a suggestion ready:
1. **The recording**: the `.screenstudio` folder (usually in `~/Screen Studio Projects`).
2. **Who it is for and where it goes**: customer group, website, YouTube, Reels. That decides the versions.
3. **The versions**: edited, hybrid, vertical cuts (how many).
4. **What must not appear**: emails, accounts, amounts, other windows, saved passwords.
5. **The closing invite**: the brand's (`kit.config.json`) or another one for this video.

## 1. Transcribe and read the narration

```bash
python3 scripts/gravacao.py novo demo-agenda --projeto "~/Screen Studio Projects/My recording.screenstudio"
python3 scripts/gravacao.py transcrever demo-agenda
python3 scripts/gravacao.py texto demo-agenda --de 0 --ate 120
```

The `texto` shows each word with its index and the second (`12:like@34.10`); the ones already in the
cuts appear in brackets. Read the whole narration before cutting, in 2-minute windows.

To find what must not appear, make contact sheets of the screen (one frame every 3 s, 90 s per
sheet) and read them all (a subagent, with the model written in the request):

```bash
ffmpeg -i "<projeto>/recording/channel-1-display-0.m3u8" -vf "fps=1/3,scale=480:-2,tile=6x5" folha-%02d.jpg
```

If you find a piece of data, look for the exact frame with `fps=10` around it: in a real recording, the
list of accounts showed up 0.4 s after the end of the narration.

## 2. The edit script (`edicoes/<id>.json`)

```json
{
 "titulo": "Calendar: schedule and reschedule without conflict",
 "projeto": "/Users/you/Screen Studio Projects/My recording.screenstudio",
 "remover": [[12, 12], [40, 47]],
 "remover_tempo": [[305.4, 309.05]],
 "acelerar": [{"de": 382.2, "ate": 388.1, "vel": 4}],
 "proibidos": [{"de": 460.5, "ate": 461.4, "antes": 460.4, "depois": 461.5}],
 "mascaras": [{"de": 68.9, "ate": 99.6, "cor": "#ffffff", "retangulos": [[343, 611, 236, 26]]}],
 "zooms": [{"de": 44.7, "ate": 57.0, "escala": 1.5, "x": 640, "y": 430}, {"de": 90, "ate": 96, "seguir": true}],
 "abertura": {"kicker": "What's new", "titulo": "Calendar *without conflict*", "sub": "in two minutes", "ate": 4},
 "chamadas": [{"em": 284.4, "dur": 3.6, "texto": "The password is not saved"}],
 "capitulos": [{"em": 149.5, "n": "1", "texto": "Schedule"}],
 "legenda_trocas": [["agenda pro", "AgendaPro"]],
 "camera": {"x": 0.5, "y": 0.38}
}
```

| Key | What it does |
|---|---|
| `remover` | narration stretches that go out, by word index `[first, last]` |
| `remover_tempo` | windows that go out by time (window switch, silence at the end) |
| `acelerar` | waits with no narration (the tool thinking, typing): they run sped up and muted, with "▶▶ 4x" on screen |
| `proibidos` | sensitive data with narration over it: the screen freezes on the `antes` or `depois` frame, and the narration goes on |
| `mascaras` | rectangles over the screen, in screen points (the recording's `bounds`), between `de` and `ate` |
| `zooms` | `escala` with center `x`, `y`, or `seguir: true` (follows the cursor); they come in and out with a spring |
| `abertura`, `chamadas`, `capitulos` | text over the screen; `em` is the second in the recording |
| `pausas` | `minima` (0.40 s), `sobra` (0.13 s of silence on each edge), `limiar_db`, `voz_db` |
| `legenda_trocas` | replaces what the transcriber got wrong in the captions (`""` erases it) |
| `convite` | the end of the video (`titulo`, `texto`, `endereco`); `false` takes it out |
| `trabalho` | another folder for the assembly (an external disk, for example) |

Times in seconds of the recording. Screen Studio 4 records the screen without the cursor: the studio
draws the macOS cursor the app saved, with the ring of every click.

### What to cut

Cutting filler words is the floor; the goal is narration that is dynamic and stumble-free:
- **filler words**: "like", "you know", "I mean", "kind of", "um", "right" when they mean nothing;
- **repeats stuck together** ("the the") and **false starts** (the sentence the person began, got wrong
  and repeated: the wrong one goes out entirely);
- **the redundant** and **what is off-topic**: cutting content is the editor's decision, and the
  delivery says what went out and why;
- **waits** become `acelerar`; **window switch** and **screen off-topic** become `remover_tempo`;
- **sensitive data**: `proibidos` (with narration) or `remover_tempo` (without narration); what stays
  visible for a long time, `mascaras`.

The edge of every cut goes on its own to the silence between words: the transcriber splices the pause
at the start of the next word, and the studio finds the real start from the audio energy.

## 3. Plan, proof of the splices and gate 1

```bash
python3 scripts/gravacao.py plano demo-agenda      # saida/edicoes/demo-agenda/plano-de-edicao.md
python3 scripts/gravacao.py emendas demo-agenda    # proves every cut
```

- The `plano` writes the edit plan: the duration before and after, every cut with the words around
  it, the filler words that stayed, the words with a piece cut off, the text on screen, the order of
  the hybrid, the scenes, the vertical cuts and the text that stays.
- The `emendas` **proves every cut**: it joins 1.6 s before and 1.6 s after the splice, transcribes and
  checks whether the neighboring words came out whole and the cut ones disappeared. If it did not
  work on the first try, it tests other silence points and keeps the best. `ok` is a score of 0.99 or
  more; `??` asks for an ear: change the cut (sometimes removing the whole sentence does it) or, if
  the review listened and it is clean, put the first index in `emendas_aceitas`.
- A subagent reviews the plan (with the model written in the request, a stronger one: it asks for
  judgment): a cut that changes the meaning, a filler word that stayed, a sentence left without a
  start.
- **Gate 1:** show the plan to the person (the content, not the file path) and, with the ok,
  `gravacao.py aprovar <id>`. If what goes out, the order, the scenes, the texts or the vertical cuts
  change after that, it asks for ok again; zoom, camera, bubble, caption replacements and accepted
  splices do not.

## 4. The edited narration and gate 2

```bash
python3 scripts/gravacao.py audio demo-agenda
python3 scripts/gravacao.py conferir demo-agenda             # stops with code 2 and the report
python3 scripts/gravacao.py conferir demo-agenda --aprovado
```

The `audio` assembles the narration with an 8 ms ramp on every splice (no click), high-pass and
-16 LUFS. The `conferir` transcribes the edited narration and compares it with the expected text:
similarity, every difference with the second in the video, the filler words heard and the splices to
listen to. A subagent reads `conferencia.json` and listens to what was flagged. The `--aprovado`
refuses a cut without proof, a low splice without acceptance and similarity below 85%. The captions
of all versions come from what is heard here.

## 5. The edited version

```bash
python3 scripts/gravacao.py montar demo-agenda
python3 scripts/gravacao.py renderizar demo-agenda --versao editada --quadros 1200-1500   # preview
python3 scripts/gravacao.py renderizar demo-agenda --versao editada
```

The `montar` cuts the screen and the camera into parts already in the order and at the speed of the
plan, checks the number of frames of each one and warns where the screen stays more than 2.5 s
without anything new (nothing changes, no cursor moving, zoom, callout or scene): a place to put a
zoom, a callout or a speed-up. The preview (`--quadros`) runs without the gates; the whole video,
only with both.

## 6. The hybrid version

The person's narration rebuilt into an argument, in the shape of the lessons:

```json
"hibrido": {
 "blocos": [
  {"nome": "problem", "de": 34.6, "ate": 44.2},
  {"nome": "context", "de": 0, "ate": 34.6},
  {"nome": "how it works", "de": 44.2, "ate": 150},
  {"nome": "what's next", "de": 410, "ate": 430}
 ],
 "cenas": [
  {"de": 34.6, "ate": 44.2, "rotulo": "The problem",
   "tela": {"tipo": "lista", "titulo": "What a *regular* calendar is missing",
            "itens": [{"texto": "Warn about the conflict", "quando": "conflict"}, {"texto": "Reschedule on its own", "quando": "reschedule"}]}}
 ],
 "capitulos": [{"em": 44.5, "n": "1", "texto": "How it works"}],
 "chamadas": [{"em": 120.0, "dur": 3, "texto": "It works on mobile too"}]
}
```

- **The order:** problem, solution, uses, demos, what's next. Each block takes what stayed in the edit
  between `de` and `ate`; the edge goes to the nearest silence (mark it between two words). The same
  narration in two blocks is refused; what is left out shows up in the plan.
- **The scenes** are the ready screens from the lessons (`capa`, `lista`, `colunas`, `fluxo`, `frase`,
  `numero`, `imagem`) over the person's voice, with the camera in the bubble. Every item comes in on
  the spoken word (`quando`), and a word the narration of that stretch does not have is refused: check
  it in what is heard (`legenda_trocas` fixes what the transcriber got wrong). Use a scene where the
  screen does not help: the problem, the idea, a number, the list of what's next.
- **The Screen Studio finish:** `fatias` writes the hybrid cuts into a **copy** of the project (a
  clone, without taking up the disk again), with the camera in the bubble and the app's captions
  turned off. Ask the person to open the copy and export (Export, MP4, 1080p): the app does not export
  without a click.

```bash
python3 scripts/gravacao.py fatias demo-agenda --nome "My recording (edited)"
python3 scripts/gravacao.py hibrido demo-agenda --exportacao "~/Downloads/My recording (edited).mp4"
python3 scripts/gravacao.py renderizar demo-agenda --versao hibrida
```

- Without the export (`hibrido` without `--exportacao`), the screen is drawn by the studio, as in the
  edited one.
- The export does not show what the studio hides: `fatias` and `hibrido` refuse a forbidden stretch or
  a mask that is not covered by a scene. An export that does not match the slices (the project changed
  afterwards) is also refused.

## 7. Vertical cuts

```json
"reels": {
 "velocidade": 1.3,
 "convite": {"titulo": "Free trial", "texto": "the link is in the bio", "endereco": "yoursite.com"},
 "cortes": [
  {"id": "r1", "gancho": "Does your calendar still *double-book*?", "titulo": "Calendar without conflict",
   "trechos": [[34.6, 44.2], [44.8, 56.9], [74.0, 97.2]]}
 ]
}
```

- Each cut is a short narrative: **hook** (what the viewer gets, in the first 2 seconds, with the
  strong word between asterisks), **proof** (the tool working) and **invite**.
- Up to 90 s after the speed-up (`max_segundos` changes it); below 15 s the studio warns.
- The screen goes in a 1080x1040 card with a tighter zoom, which follows the cursor when there is no
  zoom; the hybrid scene the cut crosses (1.5 s or more) comes in vertical; word-by-word captions,
  camera in the bubble at the top, progress bar and the title after the hook.

```bash
python3 scripts/gravacao.py reels demo-agenda
python3 scripts/gravacao.py renderizar demo-agenda --versao reels            # all
python3 scripts/gravacao.py renderizar demo-agenda --versao reels --corte r1
```

## 8. Review and delivery

- After every render, the contact sheets (`ffmpeg -i video.mp4 -vf "fps=1/4,scale=480:-2,tile=5x4" folha-%02d.jpg`)
  go through a subagent: sensitive data, bad zoom, wrong captions, cut scene.
- Show the videos and wait for the ok. With it: `gravacao.py entregar <id> --destino <pasta>` copies
  the videos, the covers and the captions (`.srt` and `.vtt`), checks the copy and deletes the
  assembly. The Screen Studio project and the copy of the slices stay where they are.
- In the final answer: where the videos ended up, the duration before and after, what went out of the
  narration and why, what was hidden and what still depends on the person.

## Commands

| Command | What it does | What it refuses |
|---|---|---|
| `novo <id> --projeto <pasta>` | creates the script | a folder that is not a Screen Studio 4 project; a paused recording |
| `transcrever` | the narration word by word, on the computer | without a transcriber |
| `texto [--de --ate]` | numbered words with the second | · |
| `plano` | the edit plan | an index outside the narration; a sped-up wait that crosses something forbidden; a vertical cut above the maximum |
| `emendas [--corte N] [--refazer]` | proves every cut | · |
| `aprovar` | **gate 1** | a plan that is not the one of the current script |
| `audio` | the edited narration | an old plan |
| `conferir [--aprovado]` | **gate 2** | a cut without proof; a low splice without acceptance; similarity below 85% |
| `montar` | the edited version | an old edited narration |
| `fatias --nome` | the cuts in a copy of the project | without the ok; sensitive data left uncovered; a copy that already exists |
| `hibrido [--exportacao]` | the hybrid version | narration in two blocks; a scene with a word the narration does not have; an export that does not match |
| `reels` | the vertical cuts | a cut above the maximum; without a hook |
| `renderizar --versao [--corte] [--quadros]` | the video, in parts of 900 frames | without both gates (except the preview); a script changed after preparing; less than 5 GB free |
| `entregar --destino` | copies and deletes the assembly | without a finished video; a copy that did not match |

## What has already gone wrong (and the studio already guards against)

- **The Screen Studio transcriber returns the stored result when the file path repeats**, even with the
  audio changed: every transcription goes with a new name.
- **The pause comes in at the start of the next word** in the transcription: the cut uses the real start
  from the energy, and the splice is proven before it counts.
- **The whole render filled the disk:** Remotion writes every frame and copies every video it uses to
  the temporary folder. The studio renders in parts of 900 frames, with the screen and the camera cut
  per part, and stops between one part and the next if the disk gets tight.
- **A temporary folder on an external disk formatted for Windows (NTFS through macFUSE) breaks the
  render browser.** The assembly can go to the external disk (`trabalho`); the system temporary folder
  cannot.
- **The copy of the slices would show the hidden data:** the mask and the frozen screen belong to the
  studio; Screen Studio exports the screen as it was recorded. That is why there is a guardrail on the
  slices.
