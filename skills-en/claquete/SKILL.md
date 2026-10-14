---
name: claquete
description: >-
  Entry point for Claquete.ai, the video studio Claude operates. It reads the person's brand,
  asks in a single round for the video type, the duration, the audience and the format (landscape,
  vertical or both), hands the work to the type skill and runs everything on its own, stopping only
  at the script and edit plan, the narration review and the delivery. Use it whenever the person says
  "I want to make a video", "make a video", "video for Instagram", "video for YouTube", "Reels",
  "lesson", "video lesson", "tutorial", "course", "track", "demo", "product demo", "quick tip",
  "brand video", "brand sting", "video ad", "avatar", "edit my recording", "Screen Studio", "cuts for
  Reels from my recording" or "what does Claquete do", even without naming the type. It also answers
  honestly about what is not ready yet.
metadata:
  resumo: Entry point, with type, duration, brand and the two-gate flow
---

# Claquete.ai: where a video starts

This skill takes the request, settles what is missing in one round and hands the work to the type
skill. From there Claude works on its own: it writes, reviews with subagents, records, narrates,
assembles and checks. It stops at three moments, and only those: the ok on the script and the edit
plan (**gate 1**), the narration review (**gate 2**) and the **delivery**.

## 1. The studio and the key

- The studio is the folder with `kit.config.json` (the installer creates `estudio-video/`). Every
  command runs from inside it.
- `python3 scripts/kit.py versao` must report 2.0.0 or higher (2.2.0 or higher to edit a person's
  recording). If it reports less, or the `plano` command does not exist:
  `npx github:dantaspaulo/claquete --atualizar` (keeps brand, scripts, recordings, `.env` and
  configuration).
- No studio yet: `npx github:dantaspaulo/claquete`. It needs Node 18 or higher; the installer takes
  care of the rest.
- The only key is `ELEVENLABS_API_KEY`, in the studio's `.env` or in the environment. Do not ask for
  another one. Never write a key into a project file.

## 2. The brand

Read `marca/marca.json` before asking anything. It comes from the installer's questionnaire or from
the claquete-marca skill.

| Field | What it is for |
|---|---|
| `nome`, `o_que_faz`, `publico` | the subject, the examples and the level of the explanation; `publico` already answers the audience question |
| `tom` | how the narration sounds: approachable and instructive, formal, casual or technical |
| `glossario` | terms of the field that appear as they are, never swapped for a synonym |
| `palavras_proibidas` | they go into neither the narration nor the screen |
| `chamada` | the invitation at the end of every video |
| `movimento` | sober, dynamic or editorial: how many chips and how much zoom |
| `cores`, `fontes`, `logo`, `fundo` | the look, carried into `kit.config.json` by `kit.py marca` |
| `material`, `design_system`, `site` | where to look for the brand's example, term and fact |

- Without `marca/marca.json`: say in one line that the video comes out in the studio's default look
  and offer "set up my brand" (claquete-marca skill). If the person wants to go ahead like that, go
  ahead.
- Is `tema.marca` in `kit.config.json` different from the brand's `nome`? Then the brand was not
  applied: run `python3 scripts/kit.py marca`.

## 3. One round of questions

Ask only what the request, the brand and the material do not answer. All in one message, with a ready
suggestion on each item, so the person only has to confirm:

1. **Type** (table below).
2. **Duration.** Lesson, walkthrough and track: 2, 3, 4 or 5 minutes, and the person chooses. Demo
   and tip: the type's range applies, and the duration comes out of the path through the tool.
3. **Audience**: who watches and what they need to walk away knowing. If the brand already says it,
   confirm.
4. **Format**: landscape (`h`, 1920×1080: website, YouTube, help center), vertical (`v`, 1080×1920:
   Reels, TikTok, Shorts) or both.
5. **Subject and source**: the text, the material or the system the content comes from. A fact and a
   number only go in with a source.
6. When there is a tool: the system's address and a **test account**.

## 4. The types

| Type (`--tipo`) | What it is | Duration | Skill |
|---|---|---|---|
| `aula` | a didactic, animated lesson, without showing a tool | 2 to 5 min, your pick | aula-animada |
| `demonstracao` | step by step through a task, recording the system | 1 to 4 min | tutorial-de-tela |
| `dica` | one feature only, straight to the point | 30 to 90 s | tutorial-de-tela |
| `caso` | a series: one walkthrough from start to finish, with the tool at work | each lesson 2 to 5 min | tutorial-de-tela |
| `trilha` | a course on one tool, one lesson per feature | each lesson 2 to 5 min | tutorial-de-tela |
| `exemplo` | only to test the studio | 10 s to 5 min | · |

A tip with no tool (one concept in one minute): type `dica`, with the animated screens from
aula-animada.

**The person already recorded** (in Screen Studio 4, with screen, camera and microphone) and wants
the video edited, a version with the reasoning reassembled or cuts for Reels: that is not a `kit.py`
type, it is the **gravacao-editada** skill, with `scripts/gravacao.py` (since 2.2). The voice is
theirs, no ElevenLabs; the two gates are the edit plan and the review of the edited narration.

Since 2.1, any type can have `animada` screens: React scenes with the React Bits components the
installer downloaded on this machine, photographed in time with the voice. That is the look of the
ChatADV lessons; the details are in the aula-animada skill ("Animated screens"). Prefer them in the
parts that call for illustration.

```bash
python3 scripts/kit.py novo <id> --tipo aula --minutos 3
python3 scripts/kit.py novo <id> --tipo demonstracao
```

The id takes only lowercase letters, numbers and hyphen. `montar` refuses a video outside the type's
range and, when `--minutos` is present, outside 20% above or below, without leaving the range: 2 min
accepts 120 to 144 s; 3 min, 144 to 216 s; 4 min, 192 to 288 s; 5 min, 240 to 300 s. Get the size right
before gate 1: `plano` shows the estimated duration.

## 5. The flow: on its own, with two gates

1. **Script.** The type skill writes `aulas/<id>.json` and runs `kit.py validar <id>` (free).
2. **Script review** by a subagent: facts, brand tone, glossary, forbidden words, sentences that are
   hard on the voice, duration. Claude fixes what it flags.
3. **Gate 1: script and edit plan.** `kit.py plano <id>` generates `saida/<id>/roteiro-e-plano.md`.
   Show the content to the person, not just the file path, and wait. Only with their ok:
   `kit.py aprovar <id>`. Any change to the file afterwards calls for a new ok; `narrar` refuses a
   script without approval or changed after it. A recording that does not exist yet (a `video` or
   `imagem` screen) does not block the gate: it shows up as a warning and in the "A gravar depois
   do ok" section of the plan, and only `montar` refuses it. The `de` field of `video` screens stays
   outside the ok: getting it right after recording does not call for a new ok. An `animada` screen
   enters the plan through `descricao`; the scene code is written after the ok.
4. **Execution.** It records the tool, when there is one, and narrates with ElevenLabs (the paid
   part).
5. **Gate 2: narration review.** `kit.py conferir <id>` generates `public/aulas/<id>/conferencia.json`
   and exits with code 2. A subagent checks each part. Approved:
   `kit.py conferir <id> --aprovado`. Rejected: Claude fixes it and narrates only that part again.
   Getting the pronunciation right does not change the script, and only the parts that use the word
   are narrated again; rewriting a sentence changes the script, and the new sentence goes back to the
   person (gate 1). Without local transcription, the person listens to the audio files listed in the
   report before `--aprovado`.
6. **Animated scenes**, if there are any: write them, `kit.py cenas <id> --previa`, review of the
   previews by a subagent, and `kit.py cenas <id>` (the full capture). `fazer` photographs the
   pending ones on its own.
7. **Assembly.** `montar`, `renderizar`, `finalizar`: pacing, duration, sound at -14 LUFS, captions
   and contact sheet. `montar` always prepares both formats; `--formatos` (`h`, `v` or `h,v`, default
   `h`) applies to `renderizar`, `finalizar` and `fazer`.
8. **Contact sheet review** by a subagent: cut-off text, empty screen, bad zoom, sensitive data.
   Claude fixes it and assembles again.
9. **Delivery.** Show the finished video and wait for the ok. With it:
   `kit.py entregar <id> --destino <pasta>`.

`kit.py fazer <id> --formatos h,v` runs everything in order and stops at the gates. Exit code 2 is a
deliberate stop (message `AGUARDANDO`, with what is missing); 1 is an error (`PAROU`, with the
reason). Read the message and follow what it says. The details of each step are in the aula-animada
and tutorial-de-tela skills.

### The subagents

Claude does not check its own work off the top of its head: it opens a subagent of its own session,
always with the model written in the request.

| Role | When | Model |
|---|---|---|
| Script reviewer | before gate 1 | a stronger one (opus, for example): it calls for judgment |
| Narration checker | at gate 2 | a fast one (sonnet, for example): checklist-driven checking |
| Contact sheet reviewer | after `finalizar` | a fast one (sonnet, for example) |
| Brand material reader | in the claquete-marca skill, with large material | a fast one (sonnet, for example) |

- Never let the subagent inherit the session model, and never use the most expensive model by
  default.
- One subagent per task, one at a time. Nothing in a loop.
- The subagent flags; Claude is the one who fixes. After fixing, the same review runs again.
- Never loosen a guardrail to get through: do not lower `similaridade_minima`, do not raise
  `tela_parada_segundos`, do not drop a forbidden word, do not put into `travas.aceitar` a word the
  voice said wrong.

## 6. Motion design

The installer brings along the iart.ai motion design skills (MIT). They decide the language; the
studio executes with what it already has (screen type, entrances timed to the narration, chips,
zooms, colors, background).

| Skill | Where it comes in |
|---|---|
| motion-art-direction | before the script: turns the brand and `movimento` into a few rules for the whole video |
| shot-composition | composition of each screen, zoom focus, safe area for vertical |
| animation-principles | the spacing of the entrances and of the chips |
| color-motion | the brand palette: accent, background, supporting tones and contrast |
| beat-sync-editing | short videos with music: cuts and zooms near the beat |
| logo-animation | brand sting (set apart for now, see section 7) |
| motion-background | animated background, only in a piece of its own |
| hairline-create | the isometric line drawing (33 figures from `@lucasmarkes/hairline`), for the `animada` screen that calls for illustration |
| remotion-video | only when the studio code (`src/`) has to be touched |
| after-effects | only if the person works in After Effects |

Not installed (installation with `--sem-motion`, or no internet)? Follow the rules of the type
skills. To add them: `npx github:dantaspaulo/claquete --atualizar`.

## 7. What is not ready yet

Say what can be done today and do not promise the rest.

| Request | Arrives in | What works today |
|---|---|---|
| Presenter avatar (Higgsfield as the main one, HeyGen as the alternative) | 2.3 | no avatar. A vertical tip or demo, narrated by the brand voice. The chosen provider is already stored in `marca.json` (`avatar`) |
| Demo ad (vertical, no person, 20 to 35 s) | 2.3 | a vertical `dica` (`--formatos v`) with what the viewer gains in the first sentence; the floor for a tip is 30 s |
| Viral cut of a video that is not from Screen Studio (live, podcast, another app) | 2.4 | from a Screen Studio 4 recording, it already comes out: gravacao-editada skill (`reels`); from another video, the studio's vertical with the brand voice |
| Carousel and 4:5 image | 2.3 | not yet: the studio only makes 16:9 and 9:16 |
| Brand sting | 2.3 | the logo-animation skill, with remotion-video, can assemble a short sting of its own, outside the studio guardrails; it does not go into the start and the end of videos by itself |
| Editing a recording from another app (Recordly or any video) | 2.4 | from Screen Studio 4, it already comes out whole (gravacao-editada skill). From another app: exported to MP4, the video goes in as a `video` screen in a demo, with cuts, speed-up, zoom and the ElevenLabs voice on top; the original sound does not go in |
| Instruction on a phone | 2.4 | a site at phone size can be recorded and narrated in vertical; the phone's system screens (installing the app, allowing notifications), not yet |

## 8. The machine

- During recording, the AI operates a browser of its own and, if the session controls the computer,
  the person's as well. Ask them to leave the machine free: do not touch the browser the AI is using
  and close whatever is heavy. A loaded machine records with stutter.
- Rendering uses a lot of memory. One video at a time; `renderizar --concorrencia 2` eases it.
- Disk: the assembly of each video takes hundreds of MB until `entregar`, and the recordings stay in
  `public/gravacoes/`. Check the free space before recording (on macOS and Linux, `df -h .`):
  recording in Playwright does not go through `kit.py`. With less than 5 GB free, stop and warn.
  `renderizar` already refuses on its own below that, and `validar` and `plano` warn.

## 9. Delivery

- `kit.py entregar <id> --destino <pasta>` copies the final video, the captions and the page
  versions, checks the copy and deletes the assembly. Only the final video stays.
- Redoing later narrates again, and the voice is paid. That is why delivery only comes after the
  person's ok on the finished video, and the page version (`--pagina`, video-na-pagina skill) comes
  out before it.
- In the final answer, say: where the video ended up, the duration, what the reviews found and what
  was fixed, what was hidden or replaced with dummy data, and what still depends on the person.
