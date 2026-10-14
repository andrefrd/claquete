---
name: claquete-marca
description: >-
  Sets up or refreshes a Claquete.ai brand. Reads the material the person provides (folder, HTML,
  .md, PDF, images, logos), the website and the links saved in marca/marca.json; extracts the name,
  hex colors, fonts, logo, tone and terms of the field; completes marca.json without overwriting the
  person's answers (and asks when the material contradicts them); applies it to the studio with
  kit.py marca; and shows a sample in the new look for approval. Use it when the person says "set up
  my brand", "refresh my brand", "use my brand guidelines", "my design system", "change the video
  colors", "change the font", "add my logo", "change the end invitation", "change the voice" or
  "ban this word", and when another Claquete skill cannot find marca/marca.json.
metadata:
  resumo: Reads brand material, completes marca.json and shows a sample
---

# How the brand reaches the videos

Everything Claquete knows about the brand lives in `marca/marca.json`, inside the studio (the folder
with `kit.config.json`). The look goes into `kit.config.json` with `python3 scripts/kit.py marca`.
The other details (tone, audience, glossary, invitation) are read by the skills before they write each
script.

## What is in marca.json

These are the keys saved by the installer's questionnaire. Keep the names unchanged: `kit.py marca`
and the other skills read them.

| Key | What it is | Where it goes |
|---|---|---|
| `nome`, `o_que_faz`, `publico` | who the brand is, what it does, who it speaks to | script; `nome` becomes `tema.marca` |
| `site`, `instagram`, `tiktok` | addresses | `site` becomes the invitation address if `chamada` has none |
| `material` | list of `{ "arquivo": "marca/material/..." }` or `{ "link": "https://..." }` | reading |
| `design_system` | path or link | reading |
| `fundo` | `escuro` or `claro` | color selection |
| `cores.principal`, `cores.secundaria`, `cores.fundo`, `cores.texto` | hex colors | `tema.destaque`, `tema.destaque2` (without a secondary color, repeats the primary), `tema.fundo`, `tema.texto` |
| `fontes.titulos`, `fontes.texto` | name on Google Fonts | `tema.fonte_titulo`, `tema.fonte_texto` |
| `logo` | `marca/logo.svg` or `.png`, file in `public/marca/` | `tema.logo`: appears at the end of every video |
| `movimento` | sober, dynamic or editorial | script: how many chips and how much zoom |
| `tom` | approachable and instructive, formal, casual or technical | script |
| `palavras_proibidas` | list | `travas.proibidas_na_fala` |
| `glossario` | terms that must not be replaced with synonyms | script and reviews |
| `voz` | `{ "nome": "Raquel" }` or `{ "nome": "...", "voice_id": "..." }` | `voz.elevenlabs` |
| `chamada` | `texto`, `endereco`, `linha` | `convite.titulo`, `convite.endereco`, `convite.texto` |
| `avatar.provedor` | `higgsfield`, `heygen` or no avatar | saved for version 2.3 |

`cores.secundaria` is not collected by the questionnaire: add it when the material includes a second
brand color. Neither are `cores.fundo2`, `cores.janela` and `cores.suave`: they are optional and become
`tema.fundo2`, `tema.janela` and `tema.suave`; without them, `kit.py marca` derives them from `fundo`
(section 4).

## 1. Read what is already there

- Read `marca/marca.json` and list `marca/material/`.
- **No marca.json**: ask all the questionnaire questions in one round, with suggestions drawn from
  the material or website, and create the file with the keys in the table (plus
  `"versao_questionario": 1`). For material the person gives you as a path, copy it into
  `marca/material/` and record it in `material`.
- **"Refresh my brand"**: ask whether they want to answer everything again or just change what they
  asked for. Before rewriting, keep a copy of the current file (`marca/marca.json.bak-<data>`).

## 2. Read the material

| Source | What to look for |
|---|---|
| HTML and CSS | color variables (`--primary`, `--brand`...), `font-family`, the Google Fonts link, the title, invitation copy |
| `.md` and PDF | brand guidelines: colors, typography, tone of voice, "do" and "don't", terms of the field |
| images and logo folder | the logo (prefer SVG; PNG with a transparent background), the versions for dark and light backgrounds |
| design system | its colors and fonts take precedence over other sources |
| website and links | open the page with the session's page-reading tool |

Instagram and TikTok often require a login. If you cannot open them, say so and continue without them.

**Large amounts of material** (many files, a long PDF, a multi-page website): hand the reading to a
subagent with a fast model named explicitly in the request (sonnet, for example), never inherited
from the session. Ask it to return each item with its source (file and excerpt):

- name, what the brand does and its audience;
- hex colors and the role of each (primary, secondary, background, text);
- title and body fonts, and whether they are on Google Fonts;
- logo files for dark and light backgrounds;
- tone: how the brand speaks (casual or formal address, short or long sentences, humor or no humor),
  with two or three examples from the material;
- terms of the field that always appear the same way (the glossary);
- words and expressions the material forbids;
- the invitation the brand uses in posts and on its website.

A color sampled only from an image is approximate. Prefer a hex value written in the guidelines,
CSS or design system, and tell the person when there is none.

## 3. Merge without overwriting

- **Keep what the person answered.** An empty field, or one with the installer's default value, can
  take what the material says; report that in the summary.
- Installer brand defaults for both languages: name "Minha marca"; primary color `#2EE59D`;
  background `#0F1114` (dark) or `#F6F7F5` (light); text `#F1F4F2` or `#111814`;
  fonts Instrument Serif and Inter; tone "próximo e didático"; motion "dinâmico". The default
  voice Raquel and invitation "Conheça" plus the name are pt-BR defaults. The en-US studio has its
  own voice (Lauren) and invitation under `linguas.en-US` in `kit.config.json`.
- **The person's answer conflicts with the material** (color, font, name, invitation): ask about all
  conflicts in one round, with both options side by side. Do not choose on your own.
- Lists (`glossario`, `palavras_proibidas`): combine them without duplicates.
- New logo: copy it to `public/marca/logo.<extensão>` (keep the previous one under a different name,
  if there is one) and save `"logo": "marca/logo.<extensão>"`.

## 4. Apply it to the studio

```bash
python3 scripts/kit.py marca
```

This carries colors, fonts, name, logo, invitation, forbidden words and voice into `kit.config.json`,
and handles two things that used to be manual:

- **Supporting tones.** `kit.py marca` derives `tema.texto`, `tema.fundo2`, `tema.janela` and
  `tema.suave` from `fundo`: a dark background gets light text; a light background gets dark text
  and light panels. If `marca.json` specifies these colors (`cores.texto`, `cores.fundo2`,
  `cores.janela`, `cores.suave`), the person's choices take precedence. Otherwise, only adjust
  `kit.config.json` by hand for combinations that fail the contrast check below (the color-motion
  skill can help), and remember that running `kit.py marca` again regenerates these four from
  `marca.json`.
- **Fonts.** Any Google Fonts font is included automatically: the studio generates
  `src/fontes.gen.ts` during `marca`, `validar`, `plano` and `montar`, so you do not need to edit
  `src/fontes.ts` or restore the font after `--atualizar`. A font unavailable on Google Fonts is
  rejected with a clear error: suggest the closest match.

What it does not do, and you do:

- **Contrast.** Check text against `janela` and `fundo`; `destaque` against `janela` and `fundo`;
  and `fundo` against `destaque` (the label above the window and the invitation address). Minimum
  ratio: 4.5, measured with the command below.
- **The background behind the window.** `tema.fundo_imagem` defaults to `fundos/esmeralda.jpg`.
  Switch to `fundos/champagne.jpg`, `fundos/oceano.jpg`, a brand photo in `public/`, or leave it
  empty for gradient lights in the brand colors.
- **Voice.** With `voz.voice_id`, run `python3 scripts/kit.py voz`: it checks that the voice is in
  the ElevenLabs account and generates `saida/teste-voz.mp3` for the person to hear. If a library
  voice is not yet in the account, the person adds it on the ElevenLabs website, and you run it again.

Contrast between two colors (the result is the ratio; below 4.5, darken or lighten one of them):

```bash
python3 -c "
import sys
def lum(h):
    c = [int(h.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
a, b = sorted([lum(sys.argv[1]), lum(sys.argv[2])])
print(round((b + 0.05) / (a + 0.05), 1))
" '#2EE59D' '#0F1114'
```

## 5. The sample

Before calling the brand ready, show the new look in a short video. Use `exemplo` (five parts,
about 630 characters of narration):

1. **The example has already been narrated and reviewed** (`public/aulas/exemplo/plano.json` exists):
   run `python3 scripts/kit.py montar exemplo`, then `renderizar exemplo` and `finalizar exemplo`
   (`--formatos h`, `v` or `h,v` only on `renderizar` and `finalizar`; `montar` already prepares both).
   The look is read during `montar`; the voice is not generated again. If the voice changed, narrate
   again (step 2).
2. **It has not**: narration costs money, so ask first ("the sample uses about 630 characters of
   ElevenLabs voice"). With the person's yes, replace the example's `cabecalho` with the brand name,
   run `kit.py plano exemplo` and `kit.py aprovar exemplo` (their yes to the sample is its gate 1),
   then `kit.py fazer exemplo --formatos h` (or `h,v`). It stops at the narration review: the
   narration checker, a subagent with a fast model named explicitly in the request, reads
   `public/aulas/exemplo/conferencia.json`; once approved, run `kit.py conferir exemplo --aprovado`
   and `fazer` again. If the example contains a word forbidden by the brand, change the sentence
   before `aprovar`.
3. Show `saida/exemplo/exemplo-h-folha.jpg` (16 frames) and the video
   `saida/exemplo/exemplo-h.mp4`. Ask what to change. For a change to color, font, background, logo
   or invitation: run `kit.py marca` (or edit `kit.config.json`) and repeat from `montar` onward;
   the voice stays the same.
4. With their ok, the brand is ready. The sample can stay where it is, or go to the person's folder
   with `kit.py entregar exemplo --destino <pasta>` (which deletes its assembly).

## 6. Motion design and the brand

With the iart.ai motion design skills, when installed:

- **color-motion**: the palette based on the brand colors, supporting tones (`fundo2`, `janela`,
  `suave`) and contrast.
- **motion-art-direction**: turns the brand into a motion language. If the material calls for
  something different from the answer given for `movimento`, ask, as with any conflict.
- **logo-animation**: the brand sting. For now it remains separate; the brand sting type arrives in
  2.3.

## 7. Wrap up

Tell the person briefly: what came from the material (with sources), which answers they gave and
kept, what you asked and what they answered, and what was left out (a font not on Google Fonts,
which the studio rejects; an approximate color; a link that did not open). From then on, every
script uses this brand.
