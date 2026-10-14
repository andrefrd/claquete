#!/usr/bin/env python3
"""Claquete.ai: a sua gravação do Screen Studio 4 editada sem abrir o app, em três versões.

  python3 scripts/gravacao.py novo <id> --projeto "<pasta .screenstudio>"   cria edicoes/<id>.json
  python3 scripts/gravacao.py transcrever <id>                   a fala palavra a palavra, no próprio computador
  python3 scripts/gravacao.py texto <id> [--de 30 --ate 90]      palavras numeradas com o tempo, para escrever os cortes
  python3 scripts/gravacao.py plano <id>                         cortes e pausas -> plano de edição para a pessoa ler
  python3 scripts/gravacao.py emendas <id> [--corte 12] [--refazer]  PROVA cada corte, transcrevendo 1,6 s antes e depois
  python3 scripts/gravacao.py aprovar <id>                       PORTÃO 1: o ok da pessoa ao plano de edição
  python3 scripts/gravacao.py audio <id>                         a fala editada, emendas sem estalo, volume das redes
  python3 scripts/gravacao.py conferir <id> [--aprovado]         PORTÃO 2: transcreve a fala editada e compara
  python3 scripts/gravacao.py montar <id>                        versão editada: tela, câmera, cursor, zoom e legenda
  python3 scripts/gravacao.py fatias <id> --nome "<nome>"        os cortes numa CÓPIA do projeto, câmera em bolinha
  python3 scripts/gravacao.py hibrido <id> [--exportacao a.mp4]  versão híbrida: a fala numa ordem nova, com cenas
  python3 scripts/gravacao.py reels <id>                         cortes em pé, a 1,3x, de até 90 s
  python3 scripts/gravacao.py renderizar <id> --versao editada|hibrida|reels [--corte r1] [--quadros 0-299]
  python3 scripts/gravacao.py entregar <id> --destino <pasta>    copia os vídeos prontos e apaga a montagem

O projeto do Screen Studio só é lido: o que se escreve vai para saida/edicoes/<id>/ (ou para "trabalho", no roteiro) e,
no `fatias`, para uma cópia nova ao lado do projeto. Transcrição sem API: o transcritor que vem dentro do Screen Studio 4
(fala da Apple, macOS 26 ou mais novo) ou o faster-whisper do estúdio (.venv). Só biblioteca padrão do Python, ffmpeg e
Node (npx remotion). Código de saída 2 = parada de propósito num portão; 1 = erro.
"""
import argparse
import array
import bisect
import hashlib
import json
import math
import os
import random
import re
import shlex
import shutil
import string
import subprocess
import sys
import tempfile
import time
import wave
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit as K  # noqa: E402

Erro, Portao = K.Erro, K.Portao
RAIZ = K.RAIZ
EDICOES = RAIZ / "edicoes"
SAIDA = RAIZ / "saida" / "edicoes"
FPS = K.FPS
PARTE = 900                  # quadros por parte do render (o Remotion guarda cada quadro e cada vídeo na pasta temporária)
JANELA = 0.01                # energia em janelas de 10 ms
CONTEXTO = 1.6               # segundos de cada lado da emenda na prova
NOTA_EMENDA = 0.99
SEMELHANCA_REVISAR, SEMELHANCA_MINIMA = 0.95, 0.85
MINIMO_LIVRE_GB = K.MINIMO_LIVRE_GB
LIVRE_POR_PARTE_GB = 1.0
ENCERRAMENTO = 4.0
CONVITE_REEL = 2.6
REEL_MAXIMO = 90
TELAS_CENA = {"capa", "lista", "colunas", "fluxo", "frase", "numero", "imagem"}
PAUSAS = {"limiar_db": -42, "voz_db": -43, "minima": 0.40, "sobra": 0.13}
# As muletas são do IDIOMA (scripts/idioma.py): em inglês são outras, e a lista do português aplicada a uma
# fala inglesa não acha nada. O roteiro da edição pode sobrescrever com a chave "muletas".
def muletas_de(r, c=None):
    if r.get("muletas"):
        return r["muletas"]
    return K.lin(c or K.cfg(), "muletas")
# Fora da assinatura do ok: o que só ajusta o visual ou registra a revisão. O resto (o que sai, a ordem, as cenas, os
# textos na tela, os cortes em pé) muda o que a pessoa aprovou e pede ok novo.
NAO_ASSINA = {"zooms", "camera", "bolha", "emendas_aceitas", "legenda_trocas", "trabalho"}
PREPARA = {"editada": "montar", "hibrida": "hibrido", "reels": "reels"}
APP = "Screen Studio.app/Contents/Resources/app.asar.unpacked/bin/transcribe-audio"


# ── utilidades ───────────────────────────────────────────────────────────

def ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def gravar(p, obj):
    # escrita direta (sem cópia de atributos): funciona também em disco externo formatado para Windows
    Path(p).write_text(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def resumo(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def resumo_arquivo(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()[:12]


def roda(cmd, **kw):
    return K.roda([str(c) for c in cmd], **kw)


def norm(w):
    n = K.norm(w)
    return K.lin(K.cfg(), "numeros").get(n, n)


def bruta(w):
    """minúscula e sem pontuação, com acento: "ó" (muleta) não é "o" (artigo)."""
    return re.sub(r"[^\w]", "", w.lower())


def mmss(s):
    return f"{int(s // 60)}:{s % 60:04.1f}"


def roteiro(id_):
    if not re.fullmatch(r"[a-z0-9-]+", id_ or ""):
        raise Erro("id: só letras minúsculas, números e hífen")
    arq = EDICOES / f"{id_}.json"
    if not arq.exists():
        raise Erro(f"não achei edicoes/{id_}.json: crie com gravacao.py novo {id_} --projeto <pasta .screenstudio>")
    r = ler(arq)
    r["_id"] = id_
    return r


def pasta(r):
    base = Path(r["trabalho"]).expanduser() if r.get("trabalho") else SAIDA
    d = base / r["_id"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def assinatura(r):
    return resumo({k: v for k, v in r.items() if not k.startswith("_") and k not in NAO_ASSINA})


def roteiro_inteiro(r):
    return resumo({k: v for k, v in r.items() if not k.startswith("_")})


def arq_aprovacao(r):
    return EDICOES / f"{r['_id']}.aprovado.json"


def aprovado(r):
    a = arq_aprovacao(r)
    return a.exists() and ler(a).get("assinatura") == assinatura(r)


def disco_livre_gb(*pastas):
    return min(shutil.disk_usage(p).free for p in pastas) / 1e9


_CODIFICADORES = []


def codificador(taxa):
    if not _CODIFICADORES:
        _CODIFICADORES.append(subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout)
    if "h264_videotoolbox" in _CODIFICADORES[0]:
        return ["-c:v", "h264_videotoolbox", "-b:v", taxa, "-g", "15"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-g", "15"]


def duracao(arq):
    return float(roda(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq]).stdout.strip())


def quadros_do_video(arq):
    r = roda(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets",
              "-of", "csv=p=0", arq])
    return int(r.stdout.strip().split(",")[0])


# ── o projeto do Screen Studio (só leitura) ──────────────────────────────────

class Gravacao:
    """Um projeto do Screen Studio 4.x: a tela, o microfone, a câmera, o cursor e os cliques, como o app gravou."""

    def __init__(self, projeto):
        self.p = Path(str(projeto)).expanduser()
        self.rec = self.p / "recording"
        if not (self.p / "project.json").exists() or not (self.rec / "metadata.json").exists():
            raise Erro(f"{self.p} não é um projeto do Screen Studio (falta project.json ou recording/metadata.json)")
        meta = ler(self.p / "meta.json") if (self.p / "meta.json").exists() else {}
        self.versao = str(meta.get("json", {}).get("version", "?"))
        if not self.versao.startswith("4."):
            raise Erro(f"o projeto é do Screen Studio {self.versao}: a edição lê o formato do 4.x (abra e salve no 4.x antes)")
        por_tipo = {x.get("type"): x for x in ler(self.rec / "metadata.json").get("recorders", [])}

        def sessao(tipo, obrigatoria=True):
            x = por_tipo.get(tipo)
            if not x or not x.get("sessions"):
                if obrigatoria:
                    raise Erro(f"a gravação não tem {tipo}")
                return None
            if len(x["sessions"]) != 1:
                raise Erro(f"a gravação foi pausada ({len(x['sessions'])} sessões): esta versão edita gravação de uma sessão só")
            return x["sessions"][0]

        tela = sessao("display")
        b = tela["bounds"]
        self.tela = self.rec / tela["outputFilename"]
        self.bx, self.by, self.W, self.H = b["x"], b["y"], int(b["width"]) // 2 * 2, int(b["height"]) // 2 * 2
        self.t0 = tela["processTimeStartMs"]
        self.duracao = tela["durationMs"] / 1000
        self.mic = self.rec / sessao("microphone")["outputFilename"]
        cam = sessao("webcam", False)
        self.camera = self.rec / cam["outputFilename"] if cam else None
        entrada = sessao("input", False) or {}
        self.movimentos = self.rec / entrada["mouseMovesFilename"] if entrada.get("mouseMovesFilename") else None
        self.cliques_arq = self.rec / entrada["mouseClicksFilename"] if entrada.get("mouseClicksFilename") else None
        cur = por_tipo.get("cursor") or {}
        self.cursores_pasta = self.rec / cur["cursorImagesFolder"] if cur.get("cursorImagesFolder") else None
        self.cursores_info = self.rec / cur["cursorsInfoFile"] if cur.get("cursorsInfoFile") else None
        for f in (self.tela, self.mic):
            if not f.exists():
                raise Erro(f"falta {f.name} na gravação")

    def cursor(self):
        if not self.movimentos or not self.movimentos.exists():
            return [], []
        serie = sorted(((m["processTimeMs"] - self.t0) / 1000, m["x"] - self.bx, m["y"] - self.by, m.get("cursorId") or "arrow")
                       for m in ler(self.movimentos))
        return serie, [s[0] for s in serie]

    def cliques(self):
        if not self.cliques_arq or not self.cliques_arq.exists():
            return []
        return [((c["processTimeMs"] - self.t0) / 1000, c["x"] - self.bx, c["y"] - self.by) for c in ler(self.cliques_arq)
                if c.get("type") == "mouseDown"]

    def cursores(self):
        if not self.cursores_info or not self.cursores_info.exists() or not self.cursores_pasta:
            return {}
        return {c["id"]: {"hx": c["hotSpot"]["x"], "hy": c["hotSpot"]["y"], "w": c["standardSize"]["width"], "h": c["standardSize"]["height"]}
                for c in ler(self.cursores_info) if (self.cursores_pasta / f"{c['id']}.png").exists()}


# ── transcrição (no próprio computador) ─────────────────────────────────────

def transcritor():
    """(modo, comando). Os dois falam o mesmo formato: uma linha JSON por palavra ({"type": "word", "word", "start", "end"})."""
    venv = RAIZ / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    whisper = ["lote", [str(venv), str(RAIZ / "scripts" / "palavras_whisper.py"), "--modelo",
                        K.cfg().get("conferencia", {}).get("modelo_local", "small")]]
    escolha = os.environ.get("CLAQUETE_TRANSCRITOR", "").strip()
    if escolha == "whisper":
        if not venv.exists():
            raise Erro("CLAQUETE_TRANSCRITOR=whisper, mas o estúdio não tem a transcrição local: "
                       "npx github:dantaspaulo/claquete --atualizar --transcricao-local")
        return whisper
    if escolha:
        return ["um", shlex.split(escolha)]
    for base in (Path("/Applications"), Path.home() / "Applications"):
        if (base / APP).exists():
            return ["um", [str(base / APP)]]
    if venv.exists():
        return whisper
    raise Erro("sem transcritor de palavras: instale o Screen Studio 4 (ele traz o transcritor da Apple, que pede macOS 26 ou "
               "mais novo) ou a transcrição local do estúdio (npx github:dantaspaulo/claquete --atualizar --transcricao-local)")


def _palavras(saida):
    por = {}
    for linha in saida.splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if d.get("type") == "error":
            raise Erro(f"a transcrição falhou: {d.get('message')} (no macOS anterior ao 26, use CLAQUETE_TRANSCRITOR=whisper)")
        if d.get("type") == "word" and str(d.get("word", "")).strip():
            por.setdefault(int(d.get("arquivo", 0)), []).append(
                {"w": d["word"].strip(), "s": round(float(d["start"]), 3), "e": round(float(d["end"]), 3),
                 "c": round(float(d.get("confidence", 1)), 2)})
    return por


_CONTA = [0]


def transcrever(wavs, locale):
    """Uma lista de palavras por arquivo. Cada arquivo vai com um nome que nunca se repete: o transcritor do Screen Studio
    devolve o resultado guardado quando o caminho se repete, mesmo que o áudio tenha mudado."""
    modo, cmd = transcritor()
    unicos = []
    for w in wavs:
        _CONTA[0] += 1
        u = Path(w).with_name(f".t{os.getpid()}-{time.time_ns()}-{_CONTA[0]}-{Path(w).name}")
        try:
            os.link(w, u)
        except OSError:
            shutil.copyfile(w, u)
        unicos.append(u)
    try:
        if modo == "lote":
            r = subprocess.run(cmd + ["--locale", locale, *map(str, unicos)], capture_output=True, text=True)
            if r.returncode:
                raise Erro(f"a transcrição local falhou: {r.stderr.strip()[-600:]}")
            por = _palavras(r.stdout)
            return [por.get(i, []) for i in range(len(unicos))]
        out = []
        for u in unicos:
            r = subprocess.run(cmd + [str(u), "--locale", locale], capture_output=True, text=True)
            out.append(_palavras(r.stdout).get(0, []))
        return out
    finally:
        for u in unicos:
            u.unlink(missing_ok=True)


def wav_mono(origem, destino, taxa, extra=()):
    roda(["ffmpeg", "-v", "error", "-y", "-i", origem, *extra, "-ac", "1", "-ar", str(taxa), destino])


def amostras(wav):
    with wave.open(str(wav)) as w:
        sr = w.getframerate()
        a = array.array("h", w.readframes(w.getnframes()))
    if sys.byteorder == "big":
        a.byteswap()
    return sr, a


def energia(wav):
    """dB RMS a cada 10 ms (0 dB = escala cheia)."""
    sr, a = amostras(wav)
    n = int(sr * JANELA)
    out = []
    for i in range(0, len(a) - n + 1, n):
        s = sum(v * v for v in a[i:i + n])
        rms = math.sqrt(s / n) / 32768
        out.append(round(20 * math.log10(rms), 1) if rms > 1e-7 else -140.0)
    return out


def dados_transcricao(r):
    d = pasta(r) / "transcricao"
    if not (d / "palavras.json").exists():
        raise Erro(f"a gravação ainda não foi transcrita: gravacao.py transcrever {r['_id']}")
    return ler(d / "palavras.json"), ler(d / "energia.json"), d


# ── o plano: cortes por palavra, pausas, esperas, trechos proibidos ─────────────

def vale(en, ini, fim):
    """instante de menor energia em [ini, fim]: a emenda cai no silêncio entre as palavras."""
    a, b = max(0, int(ini / JANELA)), min(len(en) - 1, int(fim / JANELA))
    if b <= a:
        return round(ini, 3)
    m = min(range(a, b + 1), key=lambda i: (en[i], -i))
    return round(m * JANELA + JANELA / 2, 3)


def vales(en, ini, fim, n=3):
    """até n mínimos locais de energia em [ini, fim], do mais baixo para o mais alto, a 40 ms um do outro."""
    a, b = max(1, int(ini / JANELA)), min(len(en) - 2, int(fim / JANELA))
    loc = sorted((en[i], i) for i in range(a, b + 1) if en[i] <= en[i - 1] and en[i] <= en[i + 1])
    out = []
    for _, i in loc:
        if all(abs(i - k) >= 4 for k in out):
            out.append(i)
        if len(out) == n:
            break
    return [round(i * JANELA + JANELA / 2, 3) for i in out] or [round((ini + fim) / 2, 3)]


def ataques(ws, en, voz_db):
    """começo e fim reais de cada palavra pela energia. O transcritor da Apple costuma emendar os intervalos: a palavra
    depois de uma pausa começa onde a anterior acabou, com a pausa dentro dela; o som de verdade fica no fim do intervalo."""
    out = []
    for w in ws:
        a = int(w["s"] / JANELA)
        b = max(a + 1, int(w["e"] / JANELA))
        voz = [i for i in range(a, min(b, len(en))) if en[i] >= voz_db
               and sum(1 for k in range(i, min(i + 5, len(en))) if en[k] >= voz_db) >= 3]
        out.append((voz[0] * JANELA, (voz[-1] + 1) * JANELA, voz) if voz else (w["s"], w["e"], []))
    return out


def silencios(en, ini, fim, limiar, minimo):
    out, a = [], None
    i0, i1 = int(ini / JANELA), min(len(en), int(fim / JANELA))
    for i in range(i0, i1 + 1):
        baixo = i < i1 and en[i] < limiar
        if baixo and a is None:
            a = i
        elif not baixo and a is not None:
            if (i - a) * JANELA >= minimo:
                out.append((a * JANELA, i * JANELA))
            a = None
    return out


def intervalos_menos(base, tirar):
    out = []
    for a, b in base:
        cur = [(a, b)]
        for x, y in tirar:
            nxt = []
            for p, q in cur:
                if y <= p or x >= q:
                    nxt.append((p, q))
                else:
                    if x > p:
                        nxt.append((p, x))
                    if y < q:
                        nxt.append((y, q))
            cur = nxt
        out += cur
    return [(a, b) for a, b in out if b - a > 0.02]


def emenda_padrao(en, at, ws, i, j, fim_total):
    ini = vale(en, at[i][0] - 0.25, at[i][0] + 0.02)
    fim = vale(en, at[j + 1][0] - 0.25, at[j + 1][0] + 0.02) if j + 1 < len(ws) else fim_total
    return ini, fim


def montar_linha(pecas, fator=1.0):
    """peças em tempo da gravação -> linha do tempo de saída, em quadros inteiros (cada peça começa num quadro)."""
    t, out = 0.0, []
    for p in pecas:
        vel = p["vel"] * fator
        q0 = round(t * FPS)
        t += (p["fim"] - p["ini"]) / vel
        q1 = round(t * FPS)
        if q1 > q0:
            out.append({**p, "vel": round(vel, 6), "q0": q0, "q1": q1})
    return out


def emendas_validas(r, ws):
    arq = pasta(r) / "transcricao" / "emendas.json"
    if not arq.exists():
        return {}
    e = ler(arq)
    if e.get("palavras") != resumo(ws):
        return {}   # a transcrição mudou: os índices não são mais os mesmos
    return {tuple(x["corte"]): x for x in e.get("cortes", [])}


def calcular_plano(r, ws, en):
    cfg = {**PAUSAS, **r.get("pausas", {})}
    limiar, pausa_min, sobra = cfg["limiar_db"], cfg["minima"], cfg["sobra"]
    fim_total = min(float(r.get("fim", 1e9)), ws[-1]["e"] + 0.4, len(en) * JANELA)
    at = ataques(ws, en, cfg["voz_db"])
    emendas = emendas_validas(r, ws)
    tirar = []
    for c in r.get("remover", []):
        if not (isinstance(c, list) and len(c) == 2 and 0 <= c[0] <= c[1] < len(ws)):
            raise Erro(f"corte {c}: use [primeira, última] com os índices do 'texto' (0 a {len(ws) - 1})")
        e = emendas.get(tuple(c))
        tirar.append((e["ini"], e["fim"]) if e else emenda_padrao(en, at, ws, c[0], c[1], fim_total))
    tirar += [tuple(x) for x in r.get("remover_tempo", [])]
    inicio = max(0.0, float(r.get("inicio", ws[0]["s"] - 0.25)))
    acel = []
    for a in r.get("acelerar", []):
        if not 1 < a.get("vel", 0) <= 16:
            raise Erro(f"acelerar {a}: 'vel' entre 1 e 16 (4 = quatro vezes mais rápido)")
        de, ate = max(a["de"], inicio), min(a["ate"], fim_total)
        if ate - de > 0.05:
            acel.append((de, ate, a["vel"]))
    mantidos = intervalos_menos([(inicio, fim_total)], sorted(tirar) + [(a, b) for a, b, _ in acel])

    # pausas longas encolhem; as bordas de cada trecho ficam com no máximo `sobra` de silêncio
    segs = []
    for a, b in mantidos:
        cur = a
        for x, y in silencios(en, a, b, limiar, pausa_min):
            if x <= a + 0.001:
                cur = max(a, y - sobra)
                continue
            if y >= b - JANELA * 1.5:
                b = min(b, x + sobra)
                break
            segs.append((cur, x + sobra))
            cur = y - sobra
        if b - cur > 0.04:
            segs.append((cur, b))
    trechos = [{"ini": round(a, 3), "fim": round(b, 3), "vel": 1, "mudo": False} for a, b in segs]
    trechos += [{"ini": a, "fim": b, "vel": v, "mudo": True} for a, b, v in acel]
    trechos.sort(key=lambda s: s["ini"])

    # trechos proibidos de aparecer (dado sensível, outra janela): a fala que fica por cima congela a tela
    for p in r.get("proibidos", []):
        de, ate = p["de"], p["ate"]
        antes, depois = p.get("antes", de - 0.1), p.get("depois", ate + 0.1)
        if not (antes <= de and depois >= ate):
            raise Erro(f"proibido {p}: 'antes' é um instante antes de 'de' e 'depois', um instante depois de 'ate'")
        novo = []
        for s in trechos:
            if s["fim"] <= de or s["ini"] >= ate:
                novo.append(s)
                continue
            if s["mudo"]:
                raise Erro(f"o trecho acelerado {s['ini']}-{s['fim']} cruza o proibido {de}-{ate}: corte a espera ou ajuste")
            if s["ini"] < de:
                novo.append({**s, "fim": de})
            meio = {**s, "ini": max(s["ini"], de), "fim": min(s["fim"], ate)}
            meio["congelar"] = antes if (meio["ini"] + meio["fim"]) / 2 < (de + ate) / 2 else depois
            novo.append(meio)
            if s["fim"] > ate:
                novo.append({**s, "ini": ate})
        trechos = novo
    linha = montar_linha(trechos)
    if not linha:
        raise Erro("não sobrou nada da gravação: confira 'remover', 'remover_tempo' e 'fim'")

    # palavra que fica: a maior parte do som dela cai num trecho com fala
    fica, parciais = [], []
    for i, w in enumerate(ws):
        voz = at[i][2] or [int((w["s"] + w["e"]) / 2 / JANELA)]
        dentro = sum(1 for f in voz if any(s["ini"] <= f * JANELA < s["fim"] and not s["mudo"] for s in linha))
        if dentro / len(voz) >= 0.5:
            fica.append(i)
            if at[i][2] and dentro / len(voz) < 0.85:
                parciais.append(i)
    return {"trechos": linha, "fica": fica, "parciais": parciais, "quadros": linha[-1]["q1"], "fim_total": round(fim_total, 3),
            "ataque": {str(i): round(at[i][0], 3) for i in fica}}


def chave_do_plano(r, ws):
    usados = {k: r.get(k) for k in ("remover", "remover_tempo", "acelerar", "proibidos", "pausas", "fim", "inicio")}
    emendas = sorted([e["corte"], e["ini"], e["fim"]] for e in emendas_validas(r, ws).values())
    return resumo([resumo(ws), usados, emendas])


def plano_atual(r):
    ws, _, d = dados_transcricao(r)
    arq = d.parent / "plano.json"
    if not arq.exists():
        raise Erro(f"falta o plano: gravacao.py plano {r['_id']}")
    p = ler(arq)
    if p.get("chave") != chave_do_plano(r, ws):
        raise Erro(f"o roteiro (ou a transcrição, ou as emendas) mudou depois do plano: gravacao.py plano {r['_id']}")
    return p


# ── versões: a ordem nova (híbrida) e os cortes em pé ─────────────────────────

def chave_peca(t):
    return (round(t["ini"], 3), round(t["fim"], 3))


def recortar(trechos, de, ate, en):
    """o que ficou na edição entre [de, ate) da gravação. Borda que cai no meio de um trecho de fala vai para o ponto
    mais baixo de energia a até 0,25 s dela (o silêncio entre duas palavras): marque as bordas entre palavras (texto)."""
    def ajusta(x):
        dentro = any(t["ini"] + 0.05 < x < t["fim"] - 0.05 for t in trechos if not t["mudo"])
        return vale(en, x - 0.25, x + 0.25) if dentro else x
    a0, b0 = ajusta(de), ajusta(ate)
    out = []
    for t in trechos:
        a, b = max(t["ini"], a0), min(t["fim"], b0)
        if b - a > 0.04:
            out.append({**{k: v for k, v in t.items() if k not in ("q0", "q1")}, "ini": round(a, 3), "fim": round(b, 3)})
    return out


def sobrepoe(p, pecas):
    return next((q for q in pecas if q["ini"] < p["fim"] - 0.02 and p["ini"] < q["fim"] - 0.02), None)


def linha_hibrida(r, plano, en):
    """Os blocos da fala na ordem nova: cada um leva o que ficou na edição entre o seu 'de' e o seu 'ate'. A mesma fala
    não entra em dois blocos, e o que fica de fora volta na lista para a pessoa saber o que saiu."""
    h = r.get("hibrido") or {}
    blocos = h.get("blocos") or []
    if not blocos:
        raise Erro("o roteiro não tem 'hibrido.blocos' (a fala na ordem nova, em blocos de tempo da gravação)")
    pecas = []
    for b in blocos:
        nome = b.get("nome") or f"{b['de']}-{b['ate']}"
        dentro = recortar(plano["trechos"], b["de"], b["ate"], en)
        if not any(not p["mudo"] for p in dentro):
            raise Erro(f"o bloco '{nome}' ({b['de']} a {b['ate']} s) não tem nada da fala que ficou na edição")
        for p in dentro:
            outra = sobrepoe(p, pecas)
            if outra:
                raise Erro(f"a fala de {p['ini']}-{p['fim']} s está em dois blocos ('{outra['bloco']}' e '{nome}'): sairia duas vezes")
            pecas.append({**p, "bloco": nome})
    linha = montar_linha(pecas)
    fatias = sorted(linha, key=lambda t: t["ini"])
    ss, acc = {}, 0.0
    for t in fatias:
        ss[chave_peca(t)] = acc
        acc += (t["fim"] - t["ini"]) / t["vel"]
    for t in linha:
        t["ss"] = round(ss[chave_peca(t)], 4)
    fala = [(t["ini"], t["fim"]) for t in plano["trechos"] if not t["mudo"]]
    fora = [x for x in intervalos_menos(fala, sorted((t["ini"], t["fim"]) for t in linha)) if x[1] - x[0] > 0.3]
    return linha, fora, round(acc, 3)


def linha_reel(plano, corte, vel, en):
    pecas = []
    for de, ate in corte["trechos"]:
        dentro = recortar(plano["trechos"], de, ate, en)
        if not any(not p["mudo"] for p in dentro):
            raise Erro(f"o corte '{corte['id']}': o trecho {de}-{ate} s não tem nada da fala que ficou na edição")
        for p in dentro:
            if sobrepoe(p, pecas):
                raise Erro(f"o corte '{corte['id']}' repete a fala de {p['ini']}-{p['fim']} s")
            pecas.append(p)
    return montar_linha(pecas, vel)


def tempos_fala(linha):
    """por quadro de saída: o segundo da gravação que se ouve (None nos trechos mudos)."""
    out = []
    for t in linha:
        for q in range(t["q0"], t["q1"]):
            out.append(None if t["mudo"] else t["ini"] + (q - t["q0"]) / FPS * t["vel"])
    return out


def corridas(tf, de, ate, minimo=0):
    """trechos contínuos de quadros cuja fala cai em [de, ate)."""
    out, a = [], None
    for q in range(len(tf) + 1):
        dentro = q < len(tf) and tf[q] is not None and de <= tf[q] < ate
        if dentro and a is None:
            a = q
        elif not dentro and a is not None:
            if q - a >= minimo:
                out.append((a, q))
            a = None
    return out


# ── as palavras ouvidas, em qualquer linha do tempo ──────────────────────────

def ancorar(ouvido, linha):
    """palavras ouvidas na fala editada -> tempo da gravação. A âncora é o FIM da palavra (o transcritor emenda a pausa no
    começo da seguinte); se o fim cai num trecho mudo, tenta o começo."""
    tf = tempos_fala(linha)
    out = []
    for w in ouvido:
        s, e = w["s"], w["e"]
        for anc in (e - min(0.15, (e - s) / 2), s + min(0.08, (e - s) / 2)):
            q = int(anc * FPS)
            if 0 <= q < len(tf) and tf[q] is not None:
                f = tf[q] + (anc * FPS - q) / FPS
                out.append({"w": w["w"], "a": round(f, 3), "s": round(f - min(0.35, max(0.0, anc - s)), 3)})
                break
    return out


def palavras_na_linha(fonte, linha):
    out = []
    for w in fonte:
        t = next((t for t in linha if not t["mudo"] and t["ini"] <= w["a"] < t["fim"]), None)
        if t:
            ini = max(t["ini"], w["s"])
            out.append({"w": w["w"], "q": round(t["q0"] + (ini - t["ini"]) / t["vel"] * FPS)})
    out.sort(key=lambda p: p["q"])
    return [p for k, p in enumerate(out) if not (k and norm(p["w"]) == norm(out[k - 1]["w"]) and p["q"] - out[k - 1]["q"] < FPS)]


def trocar(palavras, trocas):
    """'legenda_trocas': [["agenda pro", "AgendaPro"], ...] troca o que o transcritor escreveu errado (de palavra em palavra)."""
    for de, para in trocas:
        alvo, novo = [norm(x) for x in de.split()], para.split()
        k = 0
        while alvo and k <= len(palavras) - len(alvo):
            if [norm(p["w"]) for p in palavras[k:k + len(alvo)]] == alvo:
                qs = [p["q"] for p in palavras[k:k + len(alvo)]]
                palavras[k:k + len(alvo)] = [{"w": w, "q": qs[min(j, len(qs) - 1)]} for j, w in enumerate(novo)]
                k += len(novo)
            else:
                k += 1
    return palavras


def maiusculas(palavras, inicios=()):
    marcas = {next((k for k, p in enumerate(palavras) if p["q"] >= q), None) for q in inicios}
    for k, p in enumerate(palavras):
        ant = palavras[k - 1]["w"] if k else "."
        if (ant[-1:] in ".?!:" or k in marcas) and p["w"][:1].islower():
            p["w"] = p["w"][0].upper() + p["w"][1:]
    return palavras


def frases_de(palavras, quebras=(), letras=None):
    letras = letras or K.lin(K.cfg(), "frases")
    frases, cur = [], []
    for k, it in enumerate(palavras):
        cur.append(it)
        prox = palavras[k + 1] if k + 1 < len(palavras) else None
        txt = " ".join(x["w"] for x in cur)
        if (prox is None or it["w"][-1:] in ".?!:" or prox["q"] - it["q"] > FPS * 1.6 or len(txt) + len(prox["w"]) > letras
                or any(it["q"] < q <= prox["q"] for q in quebras)):
            fim = min(prox["q"] if prox else it["q"] + FPS, it["q"] + int(FPS * 1.4))
            frases.append({"q0": cur[0]["q"], "q1": max(fim, cur[0]["q"] + 12), "palavras": cur})
            cur = []
    for a, b in zip(frases, frases[1:]):
        a["q1"] = min(a["q1"], b["q0"])
    return frases


def blocos_reel(palavras):
    """legenda do corte em pé: blocos curtos, em palavras e letras, do tamanho do idioma."""
    palavras_max, letras_max = K.lin(K.cfg(), "reel")
    blocos, cur = [], []
    for i, p in enumerate(palavras):
        cur.append(p)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        if (prox is None or len(cur) >= palavras_max or sum(len(x["w"]) for x in cur) >= letras_max or p["w"][-1:] in ".?!:,"
                or prox["q"] - p["q"] > FPS * 0.9):
            fim = min(prox["q"] if prox else p["q"] + FPS, p["q"] + int(FPS * 1.2))
            blocos.append({"q0": cur[0]["q"], "q1": max(fim, cur[0]["q"] + 8), "palavras": cur})
            cur = []
    for a, b in zip(blocos, blocos[1:]):
        a["q1"] = min(a["q1"], b["q0"])
    return blocos


def marcas_da_tela(tela):
    out = []
    for campo in ("itens", "passos"):
        out += [it.get("quando") for it in tela.get(campo, []) if isinstance(it, dict)]
    for lado in ("esquerda", "direita"):
        out += [it.get("quando") for it in tela.get(lado, {}).get("itens", []) if isinstance(it, dict)]
    out += [c.get("quando") for c in tela.get("chips", [])]
    return [m for m in out if m]


def cenas_na_linha(cenas, linha, palavras, estrito, minimo=0):
    """cenas das aulas por cima da fala. Cada uma cobre a fala de [de, ate) da gravação e entra pelas palavras ditas
    ('quando' dos itens, como nas aulas)."""
    tf = tempos_fala(linha)
    out = []
    for c in cenas:
        tela = c.get("tela") or {}
        if tela.get("tipo") not in TELAS_CENA:
            raise Erro(f"cena {c.get('de')}-{c.get('ate')}: a tela é um de {sorted(TELAS_CENA)}")
        runs = corridas(tf, c["de"], c["ate"], minimo)
        if estrito and len(runs) != 1:
            raise Erro(f"a cena {c['de']}-{c['ate']} s " + ("não cai na versão híbrida" if not runs else
                       "cruza blocos da ordem nova: divida em duas cenas"))
        for q0, q1 in runs:
            ps = [{"p": p["w"], "ini": round((p["q"] - q0) / FPS, 3)} for p in palavras if q0 <= p["q"] < q1]
            for k, p in enumerate(ps):
                p["fim"] = round(ps[k + 1]["ini"] if k + 1 < len(ps) else (q1 - q0) / FPS, 3)
            if estrito:
                ditas = [K.norm(p["p"]) for p in ps]
                for m in marcas_da_tela(tela):
                    alvo, _, vez = m.partition("#")
                    if ditas.count(K.norm(alvo)) < int(vez or 1):
                        raise Erro(f"a cena {c['de']}-{c['ate']} s marca '{m}', que a fala dela não tem (o que se ouve: "
                                   f"{' '.join(p['p'] for p in ps)[:160]})")
            out.append({"q0": q0, "q1": q1, "tela": tela, "rotulo": c.get("rotulo"), "palavras": ps})
    return out


def copiar_imagens(cenas, pub):
    for c in cenas:
        t = c["tela"]
        if t.get("tipo") == "imagem":
            origem = RAIZ / "public" / t.get("arquivo", "")
            if not t.get("arquivo") or not origem.is_file():
                raise Erro(f"a cena usa a imagem '{t.get('arquivo')}', que não existe em public/")
            (pub / t["arquivo"]).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, pub / t["arquivo"])


# ── mídia por parte, já na ordem e na velocidade da linha ───────────────────────

def pedacos(linha, p):
    a0, a1 = p * PARTE, (p + 1) * PARTE
    for t in linha:
        x0, x1 = max(a0, t["q0"]), min(a1, t["q1"])
        if x1 > x0:
            yield t, x0, x1


def midia_partes(linha, origem, pub, nome, filtro, taxa, exportacao=None):
    """Um vídeo por parte do render, com os pedaços já na ordem da linha (o Remotion só toca, sem pular de trecho em
    trecho). exportacao=(escala,) lê o vídeo exportado pelo Screen Studio, em que as fatias já vêm aceleradas."""
    total = linha[-1]["q1"]
    marca = resumo([linha, str(origem), filtro, taxa, exportacao])[:8]
    feitos = []
    for p in range((total + PARTE - 1) // PARTE):
        arq = pub / f"{nome}-{marca}-{p:02d}.mp4"
        feitos.append(arq.name)
        if arq.exists():
            continue
        entradas, filtros = [], []
        for k, (t, x0, x1) in enumerate(pedacos(linha, p)):
            n = x1 - x0
            if exportacao:
                ini, vel = (t["ss"] + (x0 - t["q0"]) / FPS) * exportacao[0], 1.0
            elif t.get("congelar") is not None:
                entradas += ["-ss", f"{t['congelar']:.3f}", "-t", "1", "-i", origem]
                filtros.append(f"[{k}:v]{filtro},trim=end_frame=1,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop={n},"
                               f"trim=end_frame={n}[v{k}]")
                continue
            else:
                ini, vel = t["ini"] + (x0 - t["q0"]) / FPS * t["vel"], t["vel"]
            entradas += ["-ss", f"{max(0.0, ini):.3f}", "-t", f"{n / FPS * vel + 0.5:.3f}", "-i", origem]
            filtros.append(f"[{k}:v]setpts=(PTS-STARTPTS)/{vel:.6f},{filtro},tpad=stop_mode=clone:stop={n},"
                           f"trim=end_frame={n},setpts=PTS-STARTPTS[v{k}]")
        k = len(filtros)
        filtros.append("".join(f"[v{j}]" for j in range(k)) + f"concat=n={k}:v=1:a=0[o]")
        tmp = arq.with_name(arq.stem + ".tmp.mp4")
        roda(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros), "-map", "[o]", *codificador(taxa),
              "-pix_fmt", "yuv420p", "-an", tmp])
        esperado = min(PARTE, total - p * PARTE)
        if quadros_do_video(tmp) != esperado:
            raise Erro(f"{arq.name}: saiu com {quadros_do_video(tmp)} quadros, eram {esperado} (a fala sairia fora de sincronia)")
        tmp.rename(arq)
    for velho in pub.glob(f"{nome}-*.mp4"):
        if velho.name not in feitos:
            velho.unlink()
    return feitos


def audio_da_linha(linha, origem, destino, lufs, passa_alta=False, exportacao=None):
    """A fala na ordem e na velocidade da linha. Os pedaços se juntam amostra a amostra, com 8 ms de rampa em cada emenda
    (sem estalo), e cada um começa no quadro da sua peça; trecho mudo vira silêncio. A aceleração dos cortes em pé entra
    no fim, de uma vez (atempo), e o volume é medido em duas passadas (loudnorm)."""
    falas = {round(t["vel"], 6) for t in linha if not t["mudo"]}
    if len(falas) > 1:
        raise Erro(f"a linha mistura velocidades de fala ({sorted(falas)}): acelere só as esperas (mudas)")
    f = 1.0 if exportacao or not falas else falas.pop()
    destino = Path(destino)
    fonte = Path(origem)
    try:
        with wave.open(str(fonte)) as w:
            pronta = w.getframerate() == 48000 and w.getnchannels() == 1 and w.getsampwidth() == 2
    except (wave.Error, EOFError, OSError):
        pronta = False
    if not pronta:
        fonte = destino.with_name(destino.stem + "-fonte.wav")
        wav_mono(origem, fonte, 48000)
    sr, src = amostras(fonte)
    if fonte != Path(origem):
        fonte.unlink()
    out = array.array("h")
    rampa = int(sr * 0.008)
    for t in linha:
        a, b = round(t["q0"] / FPS * f * sr), round(t["q1"] / FPS * f * sr)
        n = b - a
        if t["mudo"]:
            out.extend(array.array("h", bytes(2 * n)))
            continue
        s0 = int(round((t["ss"] * exportacao[0] if exportacao else t["ini"]) * sr))
        pedaco = src[s0:s0 + n]
        if len(pedaco) < n:
            pedaco.extend(array.array("h", bytes(2 * (n - len(pedaco)))))
        for k in range(min(rampa, n // 2)):
            pedaco[k] = int(pedaco[k] * k / rampa)
            pedaco[n - 1 - k] = int(pedaco[n - 1 - k] * k / rampa)
        out.extend(pedaco)
    if sys.byteorder == "big":
        out.byteswap()
    bruto = destino.with_name(destino.stem + "-bruto.wav")
    with wave.open(str(bruto), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(out.tobytes())
    total = linha[-1]["q1"] / FPS
    pre = (f"atempo={f:.6f}," if abs(f - 1) > 1e-6 else "") + ("highpass=f=70," if passa_alta else "")
    medida = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(bruto), "-af", f"{pre}loudnorm=I={lufs}:TP=-1.5:LRA=11:print_format=json",
                             "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", medida)[-1])
    filtro = (f"{pre}loudnorm=I={lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
              f"apad=whole_dur={total:.6f},atrim=duration={total:.6f}")
    roda(["ffmpeg", "-v", "error", "-y", "-i", bruto, "-af", filtro, "-ar", "48000", "-ac", "2", destino])
    bruto.unlink()
    if abs(duracao(destino) - total) > 0.06:
        raise Erro(f"a fala saiu com {duracao(destino):.2f} s, a linha tem {total:.2f} s")
    return m["input_i"]


# ── por quadro: cursor, zoom, cliques (a tela gravada, desenhada pelo estúdio) ───────

def mola(valores, k=0.16, amortece=0.72):
    out, x, v = [], valores[0], 0.0
    for alvo in valores:
        v = v * amortece + (alvo - x) * k
        x += v
        out.append(x)
    return out


def posicao(serie, ts, t, janela=0.05):
    a, b = bisect.bisect_left(ts, t - janela), bisect.bisect_right(ts, t + janela)
    if b > a:
        xs = serie[a:b]
        return sum(s[1] for s in xs) / len(xs), sum(s[2] for s in xs) / len(xs), xs[-1][3]
    k = max(0, a - 1)
    return serie[k][1], serie[k][2], serie[k][3]


def camada_tela(linha, g, r, pub, nome="tela", bolha_mudo=True):
    """A tela da gravação desenhada pelo estúdio: o vídeo (o Screen Studio 4 grava sem o cursor), o cursor do macOS que o
    app guardou, os cliques, o zoom com mola e as máscaras. Por quadro: [escala, x, y, cursorX, cursorY, cursor,
    visível, segundo da tela, aceleração mostrada, bolinha]."""
    W, H = g.W, g.H
    partes = midia_partes(linha, g.tela, pub, nome, f"fps={FPS},scale={W}:{H},setsar=1,format=yuv420p", "8M")
    serie, ts = g.cursor()
    cursores = g.cursores()
    if cursores and not (pub / "cursores").exists():
        shutil.copytree(g.cursores_pasta, pub / "cursores")
    zooms = r.get("zooms", [])
    for z in zooms:
        if not (z.get("seguir") or ("x" in z and "y" in z)):
            raise Erro(f"zoom {z}: diga o centro ('x' e 'y', em pontos da tela de {W}x{H}) ou 'seguir': true")
    alvo_s, alvo_x, alvo_y, alvo_b, linhas = [], [], [], [], []
    for t in linha:
        for q in range(t["q0"], t["q1"]):
            congelado = t.get("congelar") is not None
            seg = t["congelar"] if congelado else t["ini"] + (q - t["q0"]) / FPS * t["vel"]
            x, y, cid = posicao(serie, ts, seg) if serie else (W / 2, H / 2, "arrow")
            vis = 1 if serie and 0 <= x <= W and 0 <= y <= H and not congelado else 0
            z = next((z for z in zooms if z["de"] <= seg < z["ate"]), None)
            if z:
                esc = max(1.0, float(z.get("escala", 1.8)))
                zx, zy = (x, y) if z.get("seguir") else (z["x"], z["y"])
                mw, mh = W / (2 * esc), H / (2 * esc)
                alvo_s.append(esc)
                alvo_x.append(min(max(zx, mw), W - mw))
                alvo_y.append(min(max(zy, mh), H - mh))
            else:
                alvo_s.append(1.0)
                alvo_x.append(W / 2)
                alvo_y.append(H / 2)
            alvo_b.append(0.0 if (t["mudo"] and bolha_mudo) else 1.0)
            linhas.append([round(x, 1), round(y, 1), cid if cid in cursores else "arrow", vis, round(seg, 3),
                           round(t["vel"], 1) if t["mudo"] and t["vel"] > 1 else 0])
    esc, zx, zy, bol = mola(alvo_s), mola(alvo_x), mola(alvo_y), mola(alvo_b, k=0.25, amortece=0.5)
    quadros = [[round(max(1.0, esc[q]), 4), round(zx[q], 1), round(zy[q], 1)] + linhas[q][:5] + [linhas[q][5], round(min(1, max(0, bol[q])), 3)]
               for q in range(len(linhas))]
    marcas = []
    for tc, x, y in g.cliques():
        for t in linha:
            fim = t["ini"] + (t["q1"] - t["q0"]) / FPS * t["vel"]
            if t.get("congelar") is None and t["ini"] <= tc < fim:
                marcas.append({"q": round(t["q0"] + (tc - t["ini"]) / t["vel"] * FPS), "x": round(x), "y": round(y)})
    for m in r.get("mascaras", []):
        if not all(len(x) == 4 for x in m.get("retangulos", [])) or "de" not in m or "ate" not in m:
            raise Erro(f"máscara {m}: 'de', 'ate' (segundos da gravação) e 'retangulos' [[x, y, largura, altura], ...] em pontos da tela")
    return {"partes": partes, "quadros": quadros, "cliques": marcas, "mascaras": r.get("mascaras", []), "cursores": cursores,
            "largura": W, "altura": H}


def camada_camera(linha, g, pub, nome="camera"):
    if not g.camera or not g.camera.exists():
        return None
    return midia_partes(linha, g.camera, pub, nome, f"fps={FPS},scale=-2:540,setsar=1,format=yuv420p", "2M")


def copiar_marca(pub):
    tema = dict(K.cfg()["tema"])
    for campo in ("logo", "fundo_imagem"):
        rel = tema.get(campo)
        if rel and (RAIZ / "public" / rel).exists():
            (pub / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RAIZ / "public" / rel, pub / rel)
        else:
            tema[campo] = ""
    return {k: v for k, v in tema.items() if not k.startswith("_")}


def convite(r, padrao_dur):
    c = r.get("convite") or K.convite(K.cfg())
    if not c:
        return None, 0.0
    return {"titulo": c.get("titulo", ""), "texto": c.get("texto", ""), "endereco": c.get("endereco", "")}, float(c.get("dur", padrao_dur))


def no_tempo(linha, itens, campo="em"):
    """chamadas e capítulos marcados em segundos da gravação -> quadro de saída."""
    tf = tempos_fala(linha)
    out = []
    for c in itens:
        perto = min(((s - c[campo], q) for q, s in enumerate(tf) if s is not None and s >= c[campo] - 0.02), default=None)
        if perto is None or perto[0] > 1.0:
            raise Erro(f"{c} cai fora do vídeo (num trecho que saiu ou que não está nesta versão): mude o '{campo}'")
        out.append({**c, "q": perto[1]})
    return out


def avisos_tela_parada(pub, partes, extras, limite):
    """Avisa (não recusa) onde a tela fica sem novidade: nada muda no vídeo e não há cursor andando, zoom, chamada ou
    cena. É o lugar de pôr um zoom, uma chamada ou uma cena, ou de cortar."""
    novidade = set(extras)
    out = []
    for p, arq in enumerate(partes):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pub / arq), "-vf", f"scale=320:-2,freezedetect=n=0.002:d={limite}",
                            "-an", "-f", "null", "-"], capture_output=True, text=True)
        ini = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]
        fim = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", r.stderr)]
        fim += [PARTE / FPS] * (len(ini) - len(fim))
        for a, b in zip(ini, fim):
            q0, q1 = p * PARTE + round(a * FPS), p * PARTE + round(b * FPS)
            corrida = 0
            for q in range(q0, q1 + 1):
                if q in novidade or q == q1:
                    if corrida >= limite * FPS:
                        out.append((q - corrida, q))
                    corrida = 0
                else:
                    corrida += 1
    juntos = []
    for a, b in sorted(out):
        if juntos and a - juntos[-1][1] <= 1:
            juntos[-1] = (juntos[-1][0], max(b, juntos[-1][1]))
        else:
            juntos.append((a, b))
    return juntos


# ── comandos ───────────────────────────────────────────────────────────────

MODELO = {
    "_leia": "Roteiro da edição. Índices de palavra: gravacao.py texto <id>. Tempos em segundos da gravação. Veja a skill gravacao-editada.",
    "titulo": "",
    "projeto": "",
    "idioma": "pt_BR",
    "pausas": dict(PAUSAS),
    "remover": [],
    "remover_tempo": [],
    "acelerar": [],
    "proibidos": [],
    "mascaras": [],
    "zooms": [],
    "chamadas": [],
    "capitulos": [],
    "legenda_trocas": [],
    "emendas_aceitas": [],
}


def cmd_novo(id_, projeto):
    if not re.fullmatch(r"[a-z0-9-]+", id_ or ""):
        raise Erro("id: só letras minúsculas, números e hífen")
    if not projeto:
        raise Erro("diga o projeto do Screen Studio: --projeto \"<pasta .screenstudio>\"")
    g = Gravacao(projeto)
    arq = EDICOES / f"{id_}.json"
    if arq.exists():
        raise Erro(f"edicoes/{id_}.json já existe")
    EDICOES.mkdir(exist_ok=True)
    r = dict(MODELO, titulo=g.p.stem, projeto=str(g.p.resolve()), idioma=K.lin(K.cfg(), "transcricao")[0])
    arq.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  criado edicoes/{id_}.json: {g.duracao / 60:.1f} min de gravação, tela {g.W}x{g.H}, "
          f"{'com' if g.camera else 'sem'} câmera (Screen Studio {g.versao})")
    print(f"  próximo: gravacao.py transcrever {id_}")


def cmd_transcrever(r):
    g = Gravacao(r["projeto"])
    d = pasta(r) / "transcricao"
    d.mkdir(exist_ok=True)
    wav = d / "mic16k.wav"
    wav_mono(g.mic, wav, 16000)
    ws = transcrever([wav], r.get("idioma", "pt_BR"))[0]
    if not ws:
        raise Erro("a transcrição voltou vazia: o microfone gravou a sua voz?")
    gravar(d / "palavras.json", ws)
    gravar(d / "energia.json", energia(wav))
    wav_mono(g.mic, d / "mic48k.wav", 48000)
    print(f"  {len(ws)} palavras em {ws[-1]['e'] / 60:.1f} min. Próximo: gravacao.py texto {r['_id']}, escrever os cortes em "
          f"edicoes/{r['_id']}.json e gravacao.py plano {r['_id']}")


def cmd_texto(r, de, ate):
    ws, _, _ = dados_transcricao(r)
    removidas = {k for i, j in r.get("remover", []) for k in range(i, j + 1)}
    linha = []
    for i, w in enumerate(ws):
        if de <= w["s"] <= ate:
            tok = f"{i}:{w['w']}@{w['s']:.2f}"
            linha.append(f"[{tok}]" if i in removidas else tok)
    for k in range(0, len(linha), 10):
        print("  ".join(linha[k:k + 10]))
    print("  [entre colchetes] = já está em 'remover'")


def descreve_tela(tela):
    t = tela.get("tipo")
    principal = tela.get("titulo") or tela.get("para") or ""
    itens = [x if isinstance(x, str) else x.get("texto", "") for x in tela.get("itens", tela.get("passos", []))]
    return f"{t}: {principal}" + (f" ({'; '.join(itens)})" if itens else "")


def cmd_plano(r):
    ws, en, d = dados_transcricao(r)
    plano = calcular_plano(r, ws, en)
    plano["chave"] = chave_do_plano(r, ws)
    plano["assinatura"] = assinatura(r)
    gravar(d.parent / "plano.json", plano)
    fica = set(plano["fica"])
    gravar(d.parent / "texto-final.txt", " ".join(ws[i]["w"] for i in plano["fica"]) + "\n")
    emendas = emendas_validas(r, ws)
    erros = []
    cfg_ = K.cfg()
    tr = lambda pt, en: K.M.tr(cfg_, pt, en)  # o plano é o que a pessoa lê para dar o ok: sai no idioma dela
    md = [tr("# Plano de edição: ", "# Edit plan: ") + f"{r.get('titulo') or r['_id']}", "",
          tr("- Gravação: ", "- Recording: ") + f"{plano['fim_total'] / 60:.1f} min → " + tr("**vídeo editado: ", "**edited video: ")
          + f"{plano['quadros'] / FPS / 60:.1f} min** ({plano['quadros'] / FPS:.0f} s), {len(plano['fica'])}" + tr(" palavras ficam.", " words stay."),
          tr("- Esperas aceleradas: ", "- Sped-up waits: ") + f"{len(r.get('acelerar', []))}" + tr("; trechos que saem pelo tempo: ", "; stretches cut by time: ")
          + f"{len(r.get('remover_tempo', []))}" + tr("; tela congelada por dado sensível: ", "; screen frozen for sensitive data: ")
          + f"{len(r.get('proibidos', []))}" + tr("; máscaras: ", "; masks: ") + f"{len(r.get('mascaras', []))}; zooms: {len(r.get('zooms', []))}.",
          "", tr("## O que sai da fala", "## What comes out of the narration"), ""]
    for i, j in r.get("remover", []):
        antes = " ".join(ws[k]["w"] for k in range(max(0, i - 4), i) if k in fica)
        depois = " ".join(ws[k]["w"] for k in range(j + 1, min(len(ws), j + 5)) if k in fica)
        e = emendas.get((i, j))
        prova = tr("sem prova ainda", "not proven yet") if not e else (tr("emenda provada", "splice proven") + f" ({e['nota']})" if e["nota"] >= NOTA_EMENDA else tr("emenda a ouvir", "splice to listen to") + f" ({e['nota']})")
        md.append(f"- {mmss(ws[i]['s'])} «{antes} ~~{' '.join(ws[k]['w'] for k in range(i, j + 1))}~~ {depois}» · {prova}")
    sobrou = [(ws[i]["w"], ws[i]["s"]) for i in plano["fica"] if bruta(ws[i]["w"]) in {bruta(m) for m in muletas_de(r)}]
    if sobrou:
        md += ["", tr("**Muletas que ficaram:** ", "**Filler words left in:** ") + ", ".join(f"{w} ({mmss(s)})" for w, s in sobrou)]
    if plano["parciais"]:
        md += ["", tr("**Palavras com um pedaço cortado (ouvir):** ", "**Words with a piece cut off (listen):** ") + ", ".join(f"{ws[i]['w']} ({mmss(ws[i]['s'])})" for i in plano["parciais"])]
    textos = r.get("chamadas", []) + r.get("capitulos", [])
    if textos or r.get("abertura"):
        md += ["", tr("## Texto na tela (versão editada)", "## On-screen text (edited version)"), ""]
        if r.get("abertura"):
            md.append(f"- Abertura: «{r['abertura'].get('titulo', '')}» {r['abertura'].get('sub', '')}")
        md += [tr("- Em ", "- At ") + f"{mmss(c['em'])}: «{c.get('texto', '')}»" for c in sorted(textos, key=lambda x: x["em"])]
    if r.get("hibrido"):
        try:
            linha, fora, total_ss = linha_hibrida(r, plano, en)
            md += ["", tr("## Versão híbrida: a fala na ordem nova", "## Hybrid version: the narration in the new order"), "",
                   f"{linha[-1]['q1'] / FPS / 60:.1f} min. " + tr("A tela sai do Screen Studio (gravacao.py fatias) e as cenas entram por cima da voz.",
                                                                 "The screen comes from Screen Studio (gravacao.py fatias) and the scenes come in over the voice."), ""]
            for b in r["hibrido"]["blocos"]:
                pecas = [t for t in linha if t["bloco"] == (b.get("nome") or f"{b['de']}-{b['ate']}")]
                if not pecas:
                    continue
                texto = " ".join(ws[i]["w"] for t in pecas for i in plano["fica"] if t["ini"] <= plano["ataque"][str(i)] < t["fim"])
                md.append(f"1. **{b.get('nome', '')}** ({(pecas[-1]['q1'] - pecas[0]['q0']) / FPS:.0f} s): «{texto[:180]}{'…' if len(texto) > 180 else ''}»")
            if fora:
                md += ["", tr("**Fica de fora da híbrida**", "**Left out of the hybrid**") + f" ({sum(b - a for a, b in fora):.0f} s" + tr(" de fala):", " of narration):"), ""]
                md += [f"- {mmss(a)}: «{' '.join(ws[i]['w'] for i in plano['fica'] if a <= plano['ataque'][str(i)] < b)}»" for a, b in fora]
            for c in r["hibrido"].get("cenas", []):
                md.append(tr("- Cena de ", "- Scene from ") + f"{mmss(c['de'])}" + tr(" a ", " to ") + f"{mmss(c['ate'])}: {descreve_tela(c.get('tela', {}))}")
            for c in r["hibrido"].get("chamadas", []) + r["hibrido"].get("capitulos", []):
                md.append(tr("- Na tela em ", "- On screen at ") + f"{mmss(c['em'])}: «{c.get('texto', '')}»")
        except Erro as e:
            erros.append(str(e))
    if r.get("reels"):
        vel = r["reels"].get("velocidade", 1.3)
        md += ["", tr("## Cortes em pé (a ", "## Vertical cuts (at ") + f"{vel}x)", ""]
        for c in r["reels"].get("cortes", []):
            try:
                linha = linha_reel(plano, c, vel, en)
                seg = linha[-1]["q1"] / FPS
                texto = " ".join(ws[i]["w"] for t in linha for i in plano["fica"] if t["ini"] <= plano["ataque"][str(i)] < t["fim"])
                md.append(f"- **{c['id']}** ({seg:.0f} s) " + tr("gancho", "hook") + f" «{c.get('gancho', '')}», " + tr("título", "title") + f" «{c.get('titulo', '')}»: «{texto[:220]}…»")
                if seg > r["reels"].get("max_segundos", REEL_MAXIMO):
                    erros.append(f"o corte {c['id']} tem {seg:.0f} s (máximo {r['reels'].get('max_segundos', REEL_MAXIMO)})")
            except Erro as e:
                erros.append(str(e))
    md += ["", tr("## O texto que fica", "## The text that stays"), "", " ".join(ws[i]["w"] for i in plano["fica"]), ""]
    gravar(d.parent / "plano-de-edicao.md", "\n".join(md))
    print(f"  {plano['fim_total']:.0f} s → {plano['quadros'] / FPS:.1f} s; {len(plano['trechos'])} trechos; plano em "
          f"{(d.parent / 'plano-de-edicao.md')}")
    for e in erros:
        print("ERRO:", e)
    return not erros


def cmd_emendas(r, so=None, refazer=False):
    """Prova cada corte da fala: monta 1,6 s antes + 1,6 s depois da emenda, transcreve e confere se as palavras vizinhas
    saíram inteiras e as cortadas sumiram. Não deu certo de primeira: testa os vales de energia perto das bordas."""
    ws, en, d = dados_transcricao(r)
    cfg = {**PAUSAS, **r.get("pausas", {})}
    at = ataques(ws, en, cfg["voz_db"])
    fim_total = min(float(r.get("fim", 1e9)), ws[-1]["e"] + 0.4, len(en) * JANELA)
    removidas = {k for i, j in r.get("remover", []) for k in range(i, j + 1)}
    sr, src = amostras(d / "mic16k.wav")
    feitas = emendas_validas(r, ws)
    teste = d / "emendas-teste"
    teste.mkdir(exist_ok=True)
    pend = [tuple(c) for c in r.get("remover", []) if (so is None or c[0] == so) and (refazer or so is not None or tuple(c) not in feitas)]
    if not pend:
        print("  todos os cortes já têm prova (--refazer para provar de novo)")
    melhor = {}

    def esperado_em(i, j, cs, ce):
        """as palavras que ficam e cabem inteiras no trecho de prova: até 3 antes da emenda e até 3 depois."""
        antes = [k for k in range(max(0, i - 6), i) if k not in removidas and at[k][0] >= cs - CONTEXTO + 0.02][-3:]
        depois = [k for k in range(j + 1, min(len(ws), j + 7)) if k not in removidas and at[k][1] <= ce + CONTEXTO - 0.02][:3]
        esperado = [norm(ws[k]["w"]) for k in antes + depois]
        return esperado, {norm(ws[k]["w"]) for k in range(i, j + 1)} - set(esperado)

    def montar_teste(cs, ce, nome):
        a = src[max(0, int((cs - CONTEXTO) * sr)):int(cs * sr)]
        b = src[int(ce * sr):int((ce + CONTEXTO) * sr)]
        f = int(sr * 0.008)
        for k in range(min(f, len(a), len(b))):
            a[len(a) - 1 - k] = int(a[len(a) - 1 - k] * k / f)
            b[k] = int(b[k] * k / f)
        arq = teste / nome
        with wave.open(str(arq), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes((a + b).tobytes())
        return arq

    for rodada in (1, 2):
        pedidos = []
        for c in pend:
            if rodada == 2 and melhor.get(c, {}).get("nota", 0) >= NOTA_EMENDA:
                continue
            i, j = c
            ini0, fim0 = emenda_padrao(en, at, ws, i, j, fim_total)
            if rodada == 1:
                cands = [(ini0, fim0)]
            else:
                ss = vales(en, at[i][0] - 0.35, at[i][0] + 0.08) + [ini0]
                ee = (vales(en, at[j + 1][0] - 0.35, at[j + 1][0] + 0.08) + [fim0]) if j + 1 < len(ws) else [fim0]
                cands = [(a, b) for a in dict.fromkeys(ss) for b in dict.fromkeys(ee) if (a, b) != (ini0, fim0) and b > a]
            for k, (cs, ce) in enumerate(cands):
                pedidos.append((c, cs, ce, montar_teste(cs, ce, f"c{i}-{j}-r{rodada}-{k}.wav")))
        if not pedidos:
            break
        ouvidos = transcrever([p[3] for p in pedidos], r.get("idioma", "pt_BR"))
        for (c, cs, ce, arq), ouvido in zip(pedidos, ouvidos):
            arq.unlink()
            esperado, cortadas = esperado_em(c[0], c[1], cs, ce)
            ouv = [norm(w["w"]) for w in ouvido]
            sm = SequenceMatcher(None, esperado, ouv, autojunk=False)
            casou = sum(b.size for b in sm.get_matching_blocks()) / len(esperado) if esperado else 1.0
            nota = round(casou - 0.4 * sum(1 for x in ouv if x in cortadas), 3)
            if c not in melhor or nota > melhor[c]["nota"]:
                melhor[c] = {"corte": list(c), "ini": cs, "fim": ce, "nota": nota, "ouvido": " ".join(ouv), "esperado": " ".join(esperado)}
    for c, e in melhor.items():
        feitas[c] = e
        marca = "ok " if e["nota"] >= NOTA_EMENDA else "?? "
        print(f"  {marca}{c[0]}-{c[1]} nota {e['nota']}: {e['ini']:.2f}→{e['fim']:.2f} | esperado «{e['esperado']}» ouvido «{e['ouvido']}»")
    gravar(d / "emendas.json", {"palavras": resumo(ws), "cortes": list(feitas.values())})
    shutil.rmtree(teste, ignore_errors=True)
    ruins = [c for c, e in feitas.items() if e["nota"] < NOTA_EMENDA]
    if ruins:
        print(f"  {len(ruins)} emenda(s) abaixo de {NOTA_EMENDA}: ouça (um subagente, pelo relatório do conferir) e mude o corte, "
              "ou, se estiver limpa, ponha o primeiro índice em 'emendas_aceitas'")
    cmd_plano(r)


def cmd_aprovar(r):
    _, _, d = dados_transcricao(r)
    arq = d.parent / "plano.json"
    if not arq.exists() or ler(arq).get("assinatura") != assinatura(r):
        raise Erro(f"o plano de edição não é o do roteiro atual: gravacao.py plano {r['_id']} e mostre de novo à pessoa")
    plano_atual(r)
    gravar(arq_aprovacao(r), {"assinatura": assinatura(r)})
    print("  plano de edição aprovado")


def cmd_audio(r):
    plano = plano_atual(r)
    d = pasta(r)
    lufs = audio_da_linha(plano["trechos"], d / "transcricao" / "mic48k.wav", d / "audio-editada.wav", -16, passa_alta=True)
    gravar(d / "audio-editada.json", {"plano": plano["chave"]})
    print(f"  fala editada: {plano['quadros'] / FPS:.1f} s; entrada {lufs} LUFS -> -16")


def audio_atual(r, plano):
    d = pasta(r)
    if not (d / "audio-editada.wav").exists() or not (d / "audio-editada.json").exists() or ler(d / "audio-editada.json").get("plano") != plano["chave"]:
        raise Erro(f"a fala editada não é a do plano atual: gravacao.py audio {r['_id']}")
    return d / "audio-editada.wav"


def emendas_pendentes(r, ws):
    feitas = emendas_validas(r, ws)
    aceitas = set(r.get("emendas_aceitas", []))
    sem = [c for c in r.get("remover", []) if tuple(c) not in feitas]
    baixas = [c for c in r.get("remover", []) if tuple(c) in feitas and feitas[tuple(c)]["nota"] < NOTA_EMENDA and c[0] not in aceitas]
    return sem, baixas


def cmd_conferir(r, aprovar_agora=False):
    plano = plano_atual(r)
    audio = audio_atual(r, plano)
    ws, _, dt = dados_transcricao(r)
    d = pasta(r)
    h = resumo_arquivo(audio)
    rel = d / "conferencia.json"
    if aprovar_agora:
        if not rel.exists() or ler(rel).get("audio") != h:
            raise Erro(f"a fala editada mudou depois do relatório (ou ele não existe): gravacao.py conferir {r['_id']} e revise de novo")
        c = ler(rel)
        sem, baixas = emendas_pendentes(r, ws)
        if sem:
            raise Erro(f"corte(s) sem prova: {sem}. Rode gravacao.py emendas {r['_id']}")
        if baixas:
            raise Erro(f"emenda(s) abaixo de {NOTA_EMENDA} sem aceite: {baixas}. Mude o corte, ou, se a revisão ouviu e está limpa, "
                       "ponha o primeiro índice em 'emendas_aceitas'")
        if c["semelhanca"] < SEMELHANCA_MINIMA:
            raise Erro(f"o que se ouve na fala editada bate {c['semelhanca']:.0%} com o texto esperado (mínimo {SEMELHANCA_MINIMA:.0%}): "
                       "alguma emenda comeu palavra; veja as diferenças no relatório")
        gravar(d / "conferencia-aprovada.json", {"audio": h})
        print("  fala editada aprovada")
        return
    esperado = [norm(w) for w in (d / "texto-final.txt").read_text(encoding="utf-8").split() if norm(w)]
    tmp = dt / f"conferir-{h}.wav"
    wav_mono(audio, tmp, 16000, ["-af", "apad=pad_dur=1"])  # sem o segundo de silêncio, a última frase fica de fora
    ouvido = transcrever([tmp], r.get("idioma", "pt_BR"))[0]
    tmp.unlink()
    obtido = [norm(w["w"]) for w in ouvido]
    sm = SequenceMatcher(None, esperado, obtido, autojunk=False)
    difs = []
    for op, a, b, c0, e0 in sm.get_opcodes():
        if op != "equal":
            t = ouvido[min(c0, len(ouvido) - 1)]["s"] if ouvido else 0
            difs.append({"em": round(t, 2), "esperado": " ".join(esperado[a:b]), "ouvido": " ".join(obtido[c0:e0])})
    muletas = {bruta(m) for m in muletas_de(r)}
    sem, baixas = emendas_pendentes(r, ws)
    feitas = emendas_validas(r, ws)
    c = {"audio": h, "semelhanca": round(sm.ratio(), 3), "diferencas": difs,
         "muletas_ouvidas": [{"w": w["w"], "em": w["s"]} for w in ouvido if bruta(w["w"]) in muletas],
         "emendas_sem_prova": sem, "emendas_a_ouvir": [feitas[tuple(x)] for x in baixas],
         "audio_editado": str(audio)}
    gravar(rel, json.dumps(c, ensure_ascii=False, indent=1))
    gravar(d / "legenda.json", {"audio": h, "ouvido": ouvido, "fonte": ancorar(ouvido, plano["trechos"])})
    if (d / "conferencia-aprovada.json").exists():
        (d / "conferencia-aprovada.json").unlink()
    estado = "ok" if sm.ratio() >= SEMELHANCA_REVISAR else ("REVISAR" if sm.ratio() >= SEMELHANCA_MINIMA else "REPROVADA")
    print(f"  semelhança {sm.ratio():.1%} {estado} ({len(esperado)} palavras esperadas, {len(obtido)} ouvidas); "
          f"{len(difs)} diferença(s); muletas ouvidas: {len(c['muletas_ouvidas'])}; emendas a ouvir: {len(baixas)}; sem prova: {len(sem)}")
    raise Portao(f"revisão da fala editada: um subagente lê {rel} (diferenças, muletas, emendas a ouvir; o áudio está em "
                 f"{audio.name}, os instantes são do vídeo editado). Aprovou: gravacao.py conferir {r['_id']} --aprovado. Reprovou: "
                 "mude o corte no roteiro e refaça plano, emendas, audio e conferir.")


def legenda_atual(r):
    d = pasta(r)
    plano = plano_atual(r)
    audio = audio_atual(r, plano)
    if not (d / "legenda.json").exists() or ler(d / "legenda.json").get("audio") != resumo_arquivo(audio):
        raise Erro(f"a legenda sai do que se ouve na fala editada: gravacao.py conferir {r['_id']}")
    return plano, ler(d / "legenda.json")


def cmd_montar(r):
    plano, leg = legenda_atual(r)
    g = Gravacao(r["projeto"])
    d = pasta(r)
    pub = d / "editada" / "publico"
    pub.mkdir(parents=True, exist_ok=True)
    linha = plano["trechos"]
    tema = copiar_marca(pub)
    tela = camada_tela(linha, g, r, pub)
    cam = camada_camera(linha, g, pub)
    palavras = maiusculas(trocar([{"w": w["w"], "q": round(w["s"] * FPS)} for w in leg["ouvido"]], r.get("legenda_trocas", [])))
    frases = frases_de(palavras)
    conv, dur = convite(r, ENCERRAMENTO)
    chamadas = no_tempo(linha, r.get("chamadas", []))
    capitulos = no_tempo(linha, r.get("capitulos", []))
    dados = {"versao": "editada", "quadros": plano["quadros"], "parte": PARTE, "tema": tema, "cabecalho": r.get("titulo", ""),
             "convite": conv, "encerramento": dur, "tela": tela, "telaPronta": None,
             "camera": {"partes": cam, **r.get("camera", {"x": 0.5, "y": 0.4})} if cam else None,
             "legendas": frases, "cenas": [], "chamadas": chamadas, "capitulos": capitulos,
             "abertura": r.get("abertura"), "bolhaSempre": False, "roteiro": roteiro_inteiro(r), "plano": plano["chave"]}
    gravar(pub / "dados.json", dados)
    extras = {q for c in chamadas for q in range(c["q"], c["q"] + int(c.get("dur", 3) * FPS))}
    extras |= {q for c in capitulos for q in range(c["q"], c["q"] + int(3.2 * FPS))}
    extras |= {q for q in range(1, len(tela["quadros"])) if abs(tela["quadros"][q][0] - tela["quadros"][q - 1][0]) > 0.001
               or abs(tela["quadros"][q][3] - tela["quadros"][q - 1][3]) + abs(tela["quadros"][q][4] - tela["quadros"][q - 1][4]) > 1.5}
    limite = K.cfg()["travas"].get("tela_parada_segundos", 2.5)
    paradas = avisos_tela_parada(pub, tela["partes"], extras, limite)
    print(f"  editada: {plano['quadros'] / FPS:.1f} s, {len(tela['partes'])} parte(s), {len(frases)} legendas, "
          f"{len(tela['cliques'])} cliques; próximo: gravacao.py renderizar {r['_id']} --versao editada")
    if paradas:
        print(f"  aviso: tela sem novidade por mais de {limite} s em " + ", ".join(f"{mmss(a / FPS)}-{mmss(b / FPS)}" for a, b in paradas[:8])
              + (f" e mais {len(paradas) - 8}" if len(paradas) > 8 else "") + ": ponha um zoom, uma chamada, uma cena, ou acelere")


def sensiveis(linha, r):
    """o que apareceria na exportação do Screen Studio sem a proteção do estúdio: trecho proibido (a tela congelada é
    nossa, o app mostraria o trecho) e máscara (o estúdio desenha; o app não tem a nossa)."""
    tf_tela = []
    for t in linha:
        for q in range(t["q0"], t["q1"]):
            tf_tela.append(t["ini"] + (q - t["q0"]) / FPS * t["vel"])
    out = [(t["q0"], t["q1"], f"trecho proibido {t['ini']:.2f}-{t['fim']:.2f} s") for t in linha if t.get("congelar") is not None]
    for m in r.get("mascaras", []):
        qs = [q for q, s in enumerate(tf_tela) if m["de"] <= s < m["ate"]]
        if qs:
            out.append((qs[0], qs[-1] + 1, f"máscara {m['de']}-{m['ate']} s"))
    return out


def descobertos(sens, cenas):
    cobre = set()
    for c in cenas:
        cobre.update(range(c["q0"], c["q1"]))
    return [s for s in sens if any(q not in cobre for q in range(s[0], s[1]))]


def novo_id():
    return "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))


def clonar(origem, destino):
    """cópia do projeto: no macOS, clone APFS (instantâneo, sem ocupar o disco de novo); fora dele, cópia comum."""
    if sys.platform == "darwin" and subprocess.run(["cp", "-c", "-R", str(origem), str(destino)], capture_output=True).returncode == 0:
        return "clone"
    shutil.rmtree(destino, ignore_errors=True)
    tamanho = sum(f.stat().st_size for f in Path(origem).rglob("*") if f.is_file())
    if shutil.disk_usage(Path(destino).parent).free < tamanho + 2e9:
        raise Erro(f"sem espaço para copiar o projeto ({tamanho / 1e9:.1f} GB)")
    shutil.copytree(origem, destino)
    return "cópia"


def cmd_fatias(r, nome):
    if not nome or "/" in nome or nome.startswith("."):
        raise Erro("diga o nome da cópia: --nome \"Minha gravação (editada)\"")
    if not aprovado(r):
        raise Portao(f"o plano de edição ainda não tem o ok da pessoa (ou mudou depois): gravacao.py plano {r['_id']}, mostre e, "
                     f"com o ok, gravacao.py aprovar {r['_id']}")
    plano = plano_atual(r)
    g = Gravacao(r["projeto"])
    _, en, _ = dados_transcricao(r)
    if r.get("hibrido"):
        linha, _, total = linha_hibrida(r, plano, en)
        cenas = cenas_na_linha(r["hibrido"].get("cenas", []), linha, [], estrito=False)
        ruins = descobertos(sensiveis(linha, r), cenas)
        fatias = sorted(linha, key=lambda t: t["ini"])
    else:
        linha = plano["trechos"]
        ruins = sensiveis(linha, r)
        fatias = linha
        total = sum((t["fim"] - t["ini"]) / t["vel"] for t in fatias)
    if ruins:
        raise Erro("a exportação do Screen Studio mostraria o que o estúdio esconde: " + "; ".join(s[2] for s in ruins) +
                   ". Cubra com uma cena da versão híbrida ou tire da fala ('remover_tempo')")
    destino = g.p.parent / f"{nome}.screenstudio"
    if destino.exists():
        raise Erro(f"já existe {destino.name}: escolha outro nome (nada foi mexido)")
    if destino.resolve() == g.p.resolve():
        raise Erro("a cópia não pode ser o próprio projeto")
    modo = clonar(g.p, destino)
    pj = ler(destino / "project.json")
    j = pj["json"]
    j["name"], j["id"] = nome, novo_id()
    cena = j["scenes"][0]
    modelo = dict(cena["slices"][0]) if cena.get("slices") else {}
    cena["slices"] = []
    for t in fatias:
        s = {**modelo, "id": novo_id(), "timeScale": 1 / t["vel"], "sourceStartMs": round(t["ini"] * 1000, 1),
             "sourceEndMs": round(t["fim"] * 1000, 1)}
        for v in ("volume", "systemAudioVolume", "externalDeviceAudioVolume"):
            if v in modelo or v == "volume":
                s[v] = 0 if t["mudo"] else modelo.get(v, 1)
        cena["slices"].append(s)
    feito = []
    conf = j.get("config", {})
    tam = float(r.get("bolha", {}).get("tamanho", 0.32))
    for caminho, valor in ((("styles", "cameraBorderRadiusRatio01"), 1), (("defaultLayout", "cameraOverlay", "overlayCameraSizeRatio01"), tam),
                           (("defaultLayout", "cameraOverlay", "overlayZoomedCameraScale"), 1),
                           (("defaultLayout", "cameraOverlay", "overlayCameraAspectRatio"), 1), (("captions", "enableTranscript"), False)):
        alvo = conf
        for k in caminho[:-1]:
            alvo = alvo.get(k) if isinstance(alvo, dict) else None
        if isinstance(alvo, dict) and caminho[-1] in alvo:
            alvo[caminho[-1]] = valor
            feito.append(caminho[-1])
    (destino / "project.json").write_text(json.dumps(pj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    volta = ler(destino / "project.json")["json"]["scenes"][0]["slices"]
    soma = sum((s["sourceEndMs"] - s["sourceStartMs"]) * s["timeScale"] for s in volta) / 1000
    if len(volta) != len(fatias) or abs(soma - total) > 0.5:
        raise Erro(f"a cópia não ficou com as fatias do plano ({len(volta)} de {len(fatias)}; {soma:.1f} de {total:.1f} s)")
    gravar(pasta(r) / "fatias.json", {"projeto": str(destino), "duracao": round(total, 3), "linha": resumo([(t["ini"], t["fim"], t["vel"]) for t in fatias]),
                                     "hibrido": bool(r.get("hibrido"))})
    print(f"  {modo} em {destino}: {len(fatias)} fatias, {total:.1f} s; ajustado: {', '.join(feito) or 'nada além das fatias'}")
    print(f"  Abra \"{nome}\" no Screen Studio, confira e exporte (Export > MP4, 1080p). Depois: "
          f"gravacao.py hibrido {r['_id']} --exportacao <arquivo.mp4>")


def cmd_hibrido(r, exportacao=None):
    h = r.get("hibrido")
    if not h:
        raise Erro("o roteiro não tem 'hibrido' (blocos na ordem nova e cenas)")
    plano, leg = legenda_atual(r)
    g = Gravacao(r["projeto"])
    d = pasta(r)
    _, en, _ = dados_transcricao(r)
    linha, fora, total_ss = linha_hibrida(r, plano, en)
    inicios = sorted({t["q0"] for k, t in enumerate(linha) if k == 0 or t["bloco"] != linha[k - 1]["bloco"]})
    palavras = maiusculas(trocar(palavras_na_linha(leg["fonte"], linha), r.get("legenda_trocas", [])), inicios)
    cenas = cenas_na_linha(h.get("cenas", []), linha, palavras, estrito=True)
    pub = d / "hibrida" / "publico"
    pub.mkdir(parents=True, exist_ok=True)
    tema = copiar_marca(pub)
    copiar_imagens(cenas, pub)
    escala = None
    if exportacao:
        exp = Path(exportacao).expanduser()
        if not exp.exists():
            raise Erro(f"não achei {exp}")
        fat = d / "fatias.json"
        if not fat.exists() or ler(fat).get("linha") != resumo([(t["ini"], t["fim"], t["vel"]) for t in sorted(linha, key=lambda t: t["ini"])]):
            raise Erro(f"a exportação precisa vir das fatias do plano atual: gravacao.py fatias {r['_id']} --nome \"...\", exporte e volte")
        ruins = descobertos(sensiveis(linha, r), cenas)
        if ruins:
            raise Erro("a exportação mostraria o que o estúdio esconde: " + "; ".join(s[2] for s in ruins) + ". Cubra com uma cena")
        dur = duracao(exp)
        if abs(dur - total_ss) > 1.5:
            raise Erro(f"a exportação tem {dur:.1f} s e as fatias somam {total_ss:.1f} s: o projeto mudou depois das fatias? "
                       "Exporte de novo (nada foi montado)")
        escala = (dur / total_ss,)
        tela = None
        pronta = {"partes": midia_partes(linha, exp, pub, "exportacao",
                                         f"fps={FPS},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                                         "setsar=1,format=yuv420p", "10M", exportacao=escala)}
        lufs = audio_da_linha(linha, exp, d / "hibrida" / "audio.wav", -16, exportacao=escala)
    else:
        tela = camada_tela(linha, g, r, pub)
        pronta = None
        lufs = audio_da_linha(linha, d / "transcricao" / "mic48k.wav", d / "hibrida" / "audio.wav", -16, passa_alta=True)
    cam = camada_camera(linha, g, pub)
    conv, dur_conv = convite(r, ENCERRAMENTO)
    dados = {"versao": "hibrida", "quadros": linha[-1]["q1"], "parte": PARTE, "tema": tema, "cabecalho": r.get("titulo", ""),
             "convite": conv, "encerramento": dur_conv, "tela": tela, "telaPronta": pronta,
             "camera": {"partes": cam, **r.get("camera", {"x": 0.5, "y": 0.4})} if cam else None,
             "legendas": frases_de(palavras, inicios), "cenas": cenas, "chamadas": no_tempo(linha, h.get("chamadas", [])),
             "capitulos": no_tempo(linha, h.get("capitulos", [])), "abertura": None, "bolhaSempre": pronta is None,
             "roteiro": roteiro_inteiro(r), "plano": plano["chave"], "exportacao": bool(exportacao)}
    gravar(pub / "dados.json", dados)
    print(f"  híbrida: {linha[-1]['q1'] / FPS:.1f} s em {len(r['hibrido']['blocos'])} blocos, {len(cenas)} cenas, tela "
          f"{'da exportação do Screen Studio' if exportacao else 'desenhada pelo estúdio (sem exportação)'}; voz {lufs} LUFS -> -16")
    if fora:
        print(f"  fica de fora da híbrida: {sum(b - a for a, b in fora):.0f} s de fala ("
              + ", ".join(mmss(a) for a, _ in fora[:12]) + ("…" if len(fora) > 12 else "") + "): diga na entrega o que saiu e por quê")
    if not exportacao:
        print(f"  para o acabamento do Screen Studio: gravacao.py fatias {r['_id']} --nome \"...\", exporte e rode de novo com --exportacao")


def cmd_reels(r):
    cfg = r.get("reels") or {}
    if not cfg.get("cortes"):
        raise Erro("o roteiro não tem 'reels.cortes' (cada corte: id, gancho, titulo e trechos [[de, ate], ...] da gravação)")
    plano, leg = legenda_atual(r)
    g = Gravacao(r["projeto"])
    d = pasta(r)
    _, en, _ = dados_transcricao(r)
    vel = float(cfg.get("velocidade", 1.3))
    maximo = float(cfg.get("max_segundos", REEL_MAXIMO))
    pub = d / "reels" / "publico"
    pub.mkdir(parents=True, exist_ok=True)
    tema = copiar_marca(pub)
    conv = cfg.get("convite") or K.convite(K.cfg())
    conv = {"titulo": conv.get("titulo", ""), "texto": conv.get("texto", ""), "endereco": conv.get("endereco", "")} if conv else None
    ids = set()
    for c in cfg["cortes"]:
        if not re.fullmatch(r"[a-z0-9-]+", c.get("id", "")) or c["id"] in ids:
            raise Erro(f"corte {c.get('id')}: 'id' único, só letras minúsculas, números e hífen")
        ids.add(c["id"])
        if not c.get("gancho"):
            raise Erro(f"o corte {c['id']} não tem gancho (a frase dos 2 primeiros segundos)")
        linha = linha_reel(plano, c, vel, en)
        seg = linha[-1]["q1"] / FPS
        if seg > maximo:
            raise Erro(f"o corte {c['id']} tem {seg:.0f} s a {vel}x (máximo {maximo:.0f}): tire trechos")
        tela = camada_tela(linha, g, r, pub, f"{c['id']}-tela")
        cam = camada_camera(linha, g, pub, f"{c['id']}-camera")
        palavras = trocar(palavras_na_linha(leg["fonte"], linha), r.get("legenda_trocas", []))
        cenas = cenas_na_linha((r.get("hibrido") or {}).get("cenas", []), linha, palavras, estrito=False, minimo=int(1.5 * FPS))
        copiar_imagens(cenas, pub)
        lufs = audio_da_linha(linha, d / "transcricao" / "mic48k.wav", d / "reels" / f"audio-{c['id']}.wav", -14, passa_alta=True)
        dados = {"versao": "reel", "quadros": linha[-1]["q1"], "parte": PARTE, "tema": tema, "cabecalho": r.get("titulo", ""),
                 "convite": conv, "encerramento": float(cfg.get("convite_segundos", CONVITE_REEL)) if conv else 0.0, "tela": tela,
                 "telaPronta": None, "camera": {"partes": cam, **r.get("camera", {"x": 0.5, "y": 0.4})} if cam else None,
                 "legendas": [], "blocos": blocos_reel(palavras), "cenas": cenas, "chamadas": [], "capitulos": [], "abertura": None,
                 "bolhaSempre": True, "gancho": c["gancho"], "titulo": c.get("titulo", ""), "nome": c.get("nome", c["id"]),
                 "roteiro": roteiro_inteiro(r), "plano": plano["chave"]}
        gravar(pub / f"dados-{c['id']}.json", dados)
        print(f"  {c['id']}: {seg:.1f} s a {vel}x + {dados['encerramento']} s de convite; {len(dados['blocos'])} legendas, "
              f"{len(cenas)} cena(s); voz {lufs} LUFS -> -14")
        if seg < 15:
            print(f"  aviso: {c['id']} tem menos de 15 s")


def legendas_arquivos(frases, destino):
    def ts(seg, sep):
        h, r_ = divmod(seg, 3600)
        m, s = divmod(r_, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s % 1) * 1000)) % 1000:03d}"

    vtt, srt = ["WEBVTT", ""], []
    for i, f in enumerate(frases, 1):
        txt = " ".join(p["w"] for p in f["palavras"])
        a, b = f["q0"] / FPS, f["q1"] / FPS
        vtt += [f"{ts(a, '.')} --> {ts(b, '.')}", txt, ""]
        srt += [str(i), f"{ts(a, ',')} --> {ts(b, ',')}", txt, ""]
    destino.with_suffix(".vtt").write_text("\n".join(vtt), encoding="utf-8")
    destino.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")


def cmd_renderizar(r, versao, corte=None, quadros=None, concorrencia=2):
    previa = quadros is not None
    plano = plano_atual(r)
    d = pasta(r)
    if not previa:
        if not aprovado(r):
            raise Portao(f"o plano de edição ainda não tem o ok da pessoa (ou mudou depois): gravacao.py plano {r['_id']}, mostre e, "
                         f"com o ok, gravacao.py aprovar {r['_id']}")
        audio = audio_atual(r, plano)
        ok = d / "conferencia-aprovada.json"
        if not ok.exists() or ler(ok).get("audio") != resumo_arquivo(audio):
            raise Portao(f"a fala editada ainda não passou pela revisão (ou mudou depois): gravacao.py conferir {r['_id']}")
    pastas = {"editada": d / "editada", "hibrida": d / "hibrida", "reels": d / "reels"}
    if versao not in pastas:
        raise Erro("--versao editada, hibrida ou reels")
    base = pastas[versao]
    pub = base / "publico"
    if versao == "reels":
        todos = [c["id"] for c in (r.get("reels") or {}).get("cortes", [])]
        alvos = [(f"dados-{x}.json", "Reel", base / f"audio-{x}.wav", f"{r['_id']}-reel-{x}") for x in todos if not corte or x == corte]
    else:
        alvos = [("dados.json", "Editada" if versao == "editada" else "Hibrida", d / "audio-editada.wav" if versao == "editada" else base / "audio.wav",
                  f"{r['_id']}-{versao}")]
    if not alvos or not all((pub / a[0]).exists() for a in alvos):
        raise Erro(f"a versão {versao} ainda não foi preparada: gravacao.py {PREPARA[versao]} {r['_id']}")
    for arq, _, _, _ in alvos:
        dd = ler(pub / arq)
        if dd.get("roteiro") != roteiro_inteiro(r) or dd.get("plano") != plano["chave"]:
            raise Erro(f"o roteiro mudou depois de preparar {arq}: prepare a versão {versao} de novo")
    tmpdir = tempfile.gettempdir()
    if disco_livre_gb(base, tmpdir) < MINIMO_LIVRE_GB:
        raise Erro(f"só {disco_livre_gb(base, tmpdir):.1f} GB livres (mínimo {MINIMO_LIVRE_GB}): entregue vídeos prontos ou libere espaço")
    npx = shutil.which("npx") or "npx"
    bundle = base / "bundle"
    shutil.rmtree(bundle, ignore_errors=True)
    roda([npx, "remotion", "bundle", "src/edicao/index.ts", f"--public-dir={pub}", f"--out-dir={bundle}", "--log=error"], cwd=RAIZ)
    final = d / "final"
    final.mkdir(exist_ok=True)
    for arq, comp, audio, nome in alvos:
        dd = ler(pub / arq)
        total = dd["quadros"] + round(dd["encerramento"] * FPS)
        a0, a1 = (0, total - 1)
        if previa:
            a0, a1 = (int(x) for x in quadros.split("-"))
            a1 = min(a1, total - 1)
        partes_dir = base / "partes"
        partes_dir.mkdir(exist_ok=True)
        marca = resumo([dd, arq])[:8]
        partes = []
        for a in range(a0, a1 + 1, PARTE):
            b = min(a1, a + PARTE - 1)
            parte = partes_dir / f"{Path(arq).stem}-{marca}-{a:06d}-{b:06d}.mp4"
            partes.append(parte)
            if parte.exists():
                continue
            if disco_livre_gb(base, tmpdir) < LIVRE_POR_PARTE_GB:
                raise Erro(f"PAROU antes da parte {a}-{b}: só {disco_livre_gb(base, tmpdir):.1f} GB livres (as partes prontas ficam; rode de novo)")
            r_ = subprocess.run([npx, "remotion", "render", str(bundle), comp, str(parte.with_suffix(".tmp.mp4")), f"--props={json.dumps({'arquivo': arq})}",
                                 f"--frames={a}-{b}", "--codec=h264", "--crf=20", "--pixel-format=yuv420p", "--muted", "--image-format=jpeg",
                                 "--jpeg-quality=92", f"--concurrency={concorrencia}", "--timeout=120000", "--log=error"], cwd=RAIZ)
            if r_.returncode:
                raise Erro("o render falhou (veja a mensagem acima)")
            parte.with_suffix(".tmp.mp4").rename(parte)
            print(f"  {nome}: quadros {a}-{b} prontos", flush=True)
        lista = partes_dir / f"lista-{marca}.txt"
        lista.write_text("".join("file '" + str(p).replace("'", "'\\''") + "'\n" for p in partes), encoding="utf-8")
        saida = final / (nome + (f" (prévia {a0}-{a1})" if previa else "") + ".mp4")
        roda(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-ss", f"{a0 / FPS:.3f}", "-i", audio,
              "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", "apad", "-shortest",
              "-movflags", "+faststart", saida])
        lista.unlink()
        if not previa:
            roda(["ffmpeg", "-v", "error", "-y", "-ss", "1.2", "-i", saida, "-frames:v", "1", "-q:v", "2", saida.with_suffix(".jpg")])
            if dd.get("legendas"):
                legendas_arquivos(dd["legendas"], saida)
            for p in partes:
                p.unlink()
        print(f"  {saida}")
    if not previa:
        shutil.rmtree(bundle, ignore_errors=True)


def cmd_entregar(r, destino):
    d = pasta(r)
    finais = sorted(p for p in (d / "final").glob("*") if p.suffix in (".mp4", ".jpg", ".srt", ".vtt") and "prévia" not in p.name) \
        if (d / "final").exists() else []
    if not any(p.suffix == ".mp4" for p in finais):
        raise Erro(f"não há vídeo pronto em {d / 'final'}: rode até o renderizar")
    alvo = Path(destino).expanduser().resolve()
    alvo.mkdir(parents=True, exist_ok=True)
    for p in finais:
        shutil.copy2(p, alvo / p.name)
        if (alvo / p.name).stat().st_size != p.stat().st_size:
            raise Erro(f"a cópia de {p.name} não bateu de tamanho: nada foi apagado")
    shutil.rmtree(d, ignore_errors=True)
    print(f"  entregue em {alvo}: {', '.join(p.name for p in finais)}; a montagem foi apagada (o projeto do Screen Studio e "
          "a cópia das fatias ficam onde estão)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["novo", "transcrever", "texto", "plano", "emendas", "aprovar", "audio", "conferir", "montar",
                                        "fatias", "hibrido", "reels", "renderizar", "entregar"])
    ap.add_argument("id")
    ap.add_argument("--projeto", help="novo: a pasta .screenstudio da gravação")
    ap.add_argument("--de", type=float, default=0, help="texto: a partir deste segundo")
    ap.add_argument("--ate", type=float, default=1e9, help="texto: até este segundo")
    ap.add_argument("--corte", help="emendas: só o corte que começa nesta palavra; renderizar: só este corte em pé")
    ap.add_argument("--refazer", action="store_true", help="emendas: prova de novo os cortes que já têm prova")
    ap.add_argument("--aprovado", action="store_true", help="conferir: a revisão da sessão aprovou a fala editada")
    ap.add_argument("--nome", help="fatias: o nome da cópia do projeto")
    ap.add_argument("--exportacao", help="hibrido: o MP4 exportado pelo Screen Studio a partir da cópia das fatias")
    ap.add_argument("--versao", help="renderizar: editada, hibrida ou reels")
    ap.add_argument("--quadros", help="renderizar: só estes quadros (prévia, sem os portões), ex.: 0-299")
    ap.add_argument("--concorrencia", type=int, default=2, help="renderizar: quadros ao mesmo tempo (menos = mais leve)")
    ap.add_argument("--destino", help="entregar: a pasta onde os vídeos ficam")
    a = ap.parse_args()
    K.carregar_env()
    try:
        if a.comando == "novo":
            cmd_novo(a.id, a.projeto)
            return
        r = roteiro(a.id)
        if a.comando == "transcrever":
            cmd_transcrever(r)
        elif a.comando == "texto":
            cmd_texto(r, a.de, a.ate)
        elif a.comando == "plano":
            sys.exit(0 if cmd_plano(r) else 1)
        elif a.comando == "emendas":
            cmd_emendas(r, int(a.corte) if a.corte else None, a.refazer)
        elif a.comando == "aprovar":
            cmd_aprovar(r)
        elif a.comando == "audio":
            cmd_audio(r)
        elif a.comando == "conferir":
            cmd_conferir(r, a.aprovado)
        elif a.comando == "montar":
            cmd_montar(r)
        elif a.comando == "fatias":
            cmd_fatias(r, a.nome)
        elif a.comando == "hibrido":
            cmd_hibrido(r, a.exportacao)
        elif a.comando == "reels":
            cmd_reels(r)
        elif a.comando == "renderizar":
            cmd_renderizar(r, a.versao, a.corte, a.quadros, a.concorrencia)
        elif a.comando == "entregar":
            if not a.destino:
                ap.error("entregar: diga a pasta com --destino")
            cmd_entregar(r, a.destino)
    except Portao as e:
        print(f"\nAGUARDANDO: {e}", file=sys.stderr)
        sys.exit(2)
    except Erro as e:
        print(f"\nPAROU: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
