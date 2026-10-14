---
name: video-na-pagina
description: >-
  Prepares a Claquete.ai video (or any MP4) for publishing on a landing page, website, blog or help
  center: lightweight H.264 and AV1 versions, poster, .vtt captions, the right player HTML for each
  use case (silent hero on loop or lesson with controls), loading that does not weigh the page down,
  and accessibility. Use it when the person asks to "put the video on the site", "video on the
  landing page", "background video", "make the video lighter", "video in the help center",
  "player", "video poster" or "captions on the video".
metadata:
  resumo: Lightweight, accessible video on a page or in a help center
---

# Video on a page

## Generate the versions

Studio video, **before `entregar`** (it deletes the assembly):
```bash
cd estudio-video
python3 scripts/kit.py fazer <id> --formatos h --pagina
```
Use the same `--formatos` as the video (`h`, `v` or `h,v`). The `finalizar --pagina` also runs over an
already finalized video (without the raw render file, and without normalizing the audio again), so
this is all you need:
```bash
python3 scripts/kit.py finalizar <id> --formatos h --pagina
```
If there is no render at all, it stops with "não há render" (there is no render): in that case, run
`renderizar <id> --formatos h` first. The `fazer ... --pagina` works too, but it renders again (the
voice is not generated again).
Output goes to `saida/<id>/`: `<id>-h-pagina.mp4` (H.264, plays everywhere), `<id>-h-pagina-av1.mp4`
(AV1, ~25% smaller, if ffmpeg has `libsvtav1`), the poster `<id>-h-pagina-poster.webp` (or `.jpg`,
if ffmpeg does not have `libwebp`) and `<id>.vtt`. `entregar` takes them all to the destination folder.

Video already delivered, or any other MP4:
```bash
ffmpeg -i entrada.mp4 -c:v libx264 -preset slow -crf 28 -c:a aac -b:a 96k -movflags +faststart saida.mp4
ffmpeg -i entrada.mp4 -c:v libsvtav1 -preset 6 -crf 42 -c:a libopus -b:a 80k -movflags +faststart saida-av1.mp4
ffmpeg -ss 1 -i entrada.mp4 -frames:v 1 poster.jpg
```

Weight target: up to ~2 MB per minute for the H.264 page version. `-movflags +faststart` always (the
video starts playing before it finishes downloading): the H.264 and AV1 versions from
`finalizar --pagina` and from the commands above already come with it.

## The HTML

**Lesson or tutorial** (with audio, controls, captions):
```html
<video controls preload="none" playsinline width="1920" height="1080"
       poster="/videos/aula-poster.jpg" style="width:100%;height:auto;border-radius:12px">
  <source src="/videos/aula-av1.mp4" type='video/mp4; codecs="av01.0.08M.08"'>
  <source src="/videos/aula.mp4" type="video/mp4">
  <track kind="captions" src="/videos/aula.vtt" srclang="en-US" label="English" default>
</video>
```

**Background video at the top of the page** (silent, on loop, never the heaviest thing on the page):
```html
<video autoplay muted loop playsinline preload="metadata" poster="/videos/hero-poster.jpg"
       width="1920" height="1080" aria-hidden="true">
  <source src="/videos/hero-av1.mp4" type='video/mp4; codecs="av01.0.08M.08"'>
  <source src="/videos/hero.mp4" type="video/mp4">
</video>
<style>@media (prefers-reduced-motion: reduce){ video[autoplay]{ display:none } }</style>
```

- **AV1 first, H.264 as fallback**: the browser picks the first one it knows how to play.
- **`width` and `height`** keep the page from jumping when the video loads.
- **Poster** is what shows first and counts as the largest image on the page: keep it light
  (webp or jpg ~60 KB).
- `preload="none"` on a lesson (it only downloads on play); `metadata` on a background.
- `.vtt` captions whenever there is speech. A background video cannot carry information that only it
  shows.
- Anyone who prefers less motion (`prefers-reduced-motion`) never sees the animated background.

## Help center and platforms

- **Help center** (Chatwoot, Zendesk, Intercom...): upload the page MP4 to public storage under a
  **unique, dated** name (`aula-1-20261006.mp4`); if you swap the video, swap the name too, because
  the address gets cached. A player that requires CORS (apps) needs the
  `Access-Control-Allow-Origin` header on the storage.
- **YouTube**: the final `<id>-h.mp4` (not the page version) and the `.srt` as captions.
- **Reels, TikTok, Shorts**: the `<id>-v.mp4` (vertical). The captions are already burned into the
  video.

## Check before saying it is live

Open the published page in a private window: the poster appears, the video plays, the captions turn
on, and on mobile the video does not overflow the width. Check the video address with
`curl -sI <url>` (200, `content-type: video/mp4`).
