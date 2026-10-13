#!/usr/bin/env python3
"""Transcrição palavra a palavra com o faster-whisper, local e gratuita, no mesmo formato do transcritor que vem dentro
do Screen Studio 4: uma linha JSON por palavra, {"type": "word", "word", "start", "end", "confidence", "arquivo"}.
Roda no .venv do estúdio (o instalador cria com --transcricao-local); o gravacao.py chama sozinho quando não há o
transcritor do Screen Studio, ou com CLAQUETE_TRANSCRITOR=whisper.

  .venv/bin/python scripts/palavras_whisper.py [--locale pt_BR] [--modelo small] <audio.wav> [<outro.wav> ...]
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locale", default="pt_BR")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("audios", nargs="+")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print(json.dumps({"type": "error", "message": "faster-whisper não está instalado neste Python (.venv do estúdio)"}))
        sys.exit(1)
    modelo = WhisperModel(a.modelo, compute_type="int8")
    idioma = a.locale.split("_")[0].split("-")[0].lower()
    for i, arq in enumerate(a.audios):
        segmentos, _ = modelo.transcribe(arq, language=idioma, word_timestamps=True, vad_filter=False)
        for seg in segmentos:
            for w in seg.words or []:
                print(json.dumps({"type": "word", "word": w.word, "start": round(w.start, 3), "end": round(w.end, 3),
                                  "confidence": round(w.probability, 3), "arquivo": i}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
