#!/usr/bin/env python3
"""Testes dos portões e das travas do estúdio, sem gastar nada (a voz é um tom gerado pelo ffmpeg).

  python3 scripts/teste.py
  python3 scripts/teste.py --licenca <arquivos...>   só a trava do React Bits (o pre-commit do repositório usa)

Cada caso aqui é uma promessa do README: roteiro sem ok não narra, fala sem revisão não monta, a duração escolhida vale,
o roteiro mudado pede ok novo e a entrega só apaga a montagem depois de conferir a cópia."""
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ESTUDIO = Path(__file__).resolve().parent.parent
falhas = []

# Componentes do React Bits: a licença (MIT + Commons Clause) não deixa redistribuí-los, então nenhum pode estar versionado
# no repositório da Claquete. O instalador baixa cada um na máquina de quem instala (src/components/react-bits/ das cenas).
RB_NOMES = {"SplitText", "BlurText", "ShinyText", "GradientText", "RotatingText", "TextType", "CountUp", "AnimatedList", "Orb", "Aurora",
            "Beams", "Particles", "staggered-text", "agentic-ball", "speeding-text", "animated-list", "magic-transform", "globe"}


def licenca_react_bits(arquivos):
    """Dos caminhos dados, os que são componente do React Bits (pasta react-bits ou arquivo com o nome de um deles)."""
    ruins = []
    for f in arquivos:
        q = Path(f)
        if "react-bits" in q.parts or (q.stem in RB_NOMES and q.suffix in (".tsx", ".jsx")) or q.name == "globe.gl.min.js":
            ruins.append(str(f))
    return ruins


def confere(nome, cond):
    print(("ok      " if cond else "FALHOU  ") + nome)
    cond or falhas.append(nome)


def kit(raiz, *args):
    r = subprocess.run([sys.executable, "scripts/kit.py", *args], cwd=raiz, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})
    return r.returncode, r.stdout + r.stderr


def narracao_falsa(raiz, id_):
    """Escreve partes 'narradas' com um tom do tamanho da fala (2,6 palavras por segundo) e os tempos de palavra
    espalhados, como o narrar deixaria."""
    a = json.loads((raiz / "aulas" / f"{id_}.json").read_text(encoding="utf-8"))
    d = raiz / "public" / "aulas" / id_
    d.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(a["partes"], 1):
        segundos = round(max(3.0, len(p["fala"].split()) / 2.6), 2)
        mp3 = d / f"parte-{i:02d}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=220:duration={segundos}", str(mp3)], check=True)
        toks = p["fala"].split()
        passo = segundos / max(1, len(toks))
        palavras = [{"p": t, "ini": round(k * passo, 3), "fim": round(k * passo + passo * 0.9, 3)} for k, t in enumerate(toks)]
        (d / f"parte-{i:02d}.json").write_text(json.dumps({"assinatura": f"falsa-{i}", "fala": p["fala"], "palavras": palavras}, ensure_ascii=False))


def carregar_kit(raiz):
    spec = importlib.util.spec_from_file_location("kit_teste", raiz / "scripts" / "kit.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def testes_licenca():
    confere("a trava do React Bits pega componente na pasta react-bits e pelo nome",
            licenca_react_bits(["estudio/cenas/src/components/react-bits/Orb.tsx", "outra/pasta/SplitText.tsx", "x/agentic-ball.tsx"]) ==
            ["estudio/cenas/src/components/react-bits/Orb.tsx", "outra/pasta/SplitText.tsx", "x/agentic-ball.tsx"])
    confere("a trava do React Bits deixa passar o código da Claquete",
            licenca_react_bits(["estudio/cenas/src/rb.js", "estudio/cenas/src/ilustra.jsx", "estudio/cenas/src/aulas/animada-exemplo.jsx"]) == [])
    repo = ESTUDIO.parent
    if (repo / ".git").exists() and shutil.which("git"):
        versionados = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True).stdout.split()
        confere("nenhum componente do React Bits versionado no repositório", licenca_react_bits(versionados) == [])
        ign = (repo / ".gitignore").read_text(encoding="utf-8")
        confere("o .gitignore deixa de fora os componentes baixados", "estudio/cenas/src/components/react-bits/" in ign)
    else:
        print("pulado  React Bits versionado (fora do repositório da Claquete)")


# ── gravação editada (2.2): uma gravação do Screen Studio 4 de mentira, com tons no lugar das palavras ─────────────

VOCAB = {"um": 300, "dois": 380, "tres": 460, "quatro": 540, "cinco": 620, "seis": 700, "sete": 780, "oito": 860, "nove": 940,
         "dez": 1020, "onze": 1100, "doze": 1180, "né": 1500}
# palavras de 0,30 s com 0,12 s entre elas: "né" é muleta (3), "sete" se repete (7 e 8), há uma pausa longa e uma espera
FALA = ["um", "dois", "tres", "né", "quatro", "cinco", 1.5, "seis", "sete", "sete", "oito", 3.0, "nove", "dez", "onze", "doze"]

# O transcritor de mentira fala o formato do transcritor do Screen Studio (uma linha JSON por palavra) e reconhece cada
# palavra pela frequência do tom. Como o da Apple, começa cada palavra onde a anterior acabou (a pausa entra nela).
TRANSCRITOR_FALSO = r"""
import array, json, math, os, sys, wave
VOCAB = %s
arq = sys.argv[1]
if os.environ.get("FALSO_LOG"):
    open(os.environ["FALSO_LOG"], "a").write(os.path.basename(arq) + "\n")
with wave.open(arq) as w:
    sr = w.getframerate(); a = array.array("h", w.readframes(w.getnframes()))
n = int(sr * 0.01)
en = []
for i in range(0, len(a) - n + 1, n):
    r = math.sqrt(sum(v * v for v in a[i:i + n]) / n) / 32768
    en.append(20 * math.log10(r) if r > 1e-7 else -140)
reg, ini = [], None
for i, e in enumerate(en + [-140]):
    if e > -30 and ini is None:
        ini = i
    elif e <= -30 and ini is not None:
        if i - ini >= 8:
            reg.append((ini, i))
        ini = None
print("Transcribe audio starting...")
fim = 0.0
for a0, a1 in reg:
    seg = a[a0 * n:a1 * n]
    f = sum(1 for k in range(1, len(seg)) if (seg[k - 1] < 0) != (seg[k] < 0)) / (2 * len(seg) / sr)
    w = min(VOCAB, key=lambda k: abs(VOCAB[k] - f))
    print(json.dumps({"type": "word", "word": w, "start": round(fim, 3), "end": round(a1 * 0.01, 3), "confidence": 0.9}))
    fim = a1 * 0.01
""" % json.dumps(VOCAB, ensure_ascii=False)


def gravacao_falsa(p):
    """Um projeto .screenstudio do 4.x: tela, microfone, câmera, cursor e cliques, como o app grava."""
    import array as _array
    import math
    import wave
    rec = p / "recording"
    (rec / "cursors").mkdir(parents=True)
    sr, amostras, t = 48000, _array.array("h"), 0.0
    for item in FALA:
        if isinstance(item, float):
            amostras.extend([0] * int(item * sr))
            t += item
            continue
        for k in range(int(0.30 * sr)):
            env = min(1, k / (0.01 * sr), (0.30 * sr - k) / (0.01 * sr))
            amostras.append(int(0.4 * 32767 * env * math.sin(2 * math.pi * VOCAB[item] * k / sr)))
        amostras.extend([0] * int(0.12 * sr))
        t += 0.42
    amostras.extend([0] * int(0.5 * sr))
    t += 0.5
    with wave.open(str(rec / "fala.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(amostras.tobytes())

    def ff(*a):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, a)], check=True)
    ff("-i", rec / "fala.wav", "-c:a", "aac", rec / "channel-2-microphone-0.m4a")
    (rec / "fala.wav").unlink()
    ff("-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=30:duration={t:.2f}", "-pix_fmt", "yuv420p", rec / "channel-1-display-0.mp4")
    ff("-f", "lavfi", "-i", f"testsrc=size=320x240:rate=30:duration={t:.2f}", "-pix_fmt", "yuv420p", rec / "channel-3-webcam-0.mp4")
    ff("-f", "lavfi", "-i", "color=c=black:s=17x23", "-frames:v", "1", rec / "cursors" / "arrow.png")
    t0 = 1000.0

    def sessao(**k):
        return {"durationMs": t * 1000, "processTimeStartMs": t0, **k}
    meta = {"recorders": [
        {"id": "channel-0-cursor", "type": "cursor", "cursorImagesFolder": "cursors", "cursorsInfoFile": "cursors.json"},
        {"id": "channel-0-input", "type": "input", "sessions": [sessao(mouseMovesFilename="mousemoves-0.json", mouseClicksFilename="mouseclicks-0.json")]},
        {"id": "channel-1-display", "type": "display", "sessions": [sessao(outputFilename="channel-1-display-0.mp4",
                                                                            bounds={"x": 100, "y": -360, "width": 640, "height": 360})]},
        {"id": "channel-2-microphone", "type": "microphone", "sessions": [sessao(outputFilename="channel-2-microphone-0.m4a")]},
        {"id": "channel-3-webcam", "type": "webcam", "sessions": [sessao(outputFilename="channel-3-webcam-0.mp4")]}]}
    (rec / "metadata.json").write_text(json.dumps(meta))
    (rec / "mousemoves-0.json").write_text(json.dumps([{"processTimeMs": t0 + k * 250, "x": 100 + (20 * k) % 640, "y": -360 + (12 * k) % 360,
                                                        "cursorId": "arrow", "type": "mouseMoved"} for k in range(int(t * 4))]))
    (rec / "mouseclicks-0.json").write_text(json.dumps([{"processTimeMs": t0 + 2000, "x": 300, "y": -200, "type": "mouseDown"}]))
    (rec / "cursors.json").write_text(json.dumps([{"id": "arrow", "hotSpot": {"x": 4, "y": 4}, "standardSize": {"width": 17, "height": 23}}]))
    (p / "meta.json").write_text(json.dumps({"json": {"version": "4.0.4-teste"}, "meta": {"v": 1}}))
    (p / "project.json").write_text(json.dumps({"json": {"name": "Gravação de teste", "id": "AbCdEfGhIj", "config": {
        "styles": {"cameraBorderRadiusRatio01": 0.15}, "captions": {"enableTranscript": True},
        "defaultLayout": {"cameraOverlay": {"overlayCameraSizeRatio01": 0.5, "overlayZoomedCameraScale": 0.8, "overlayCameraAspectRatio": 1}}},
        "scenes": [{"zooms": [], "slices": [{"id": "x0", "timeScale": 1, "sourceStartMs": 0, "sourceEndMs": t * 1000, "volume": 1,
                                             "systemAudioVolume": 1, "externalDeviceAudioVolume": 1}]}]}, "meta": {"values": {}, "v": 1}}))


def testes_gravacao(raiz, tmp):
    import hashlib
    import shlex
    falso, log = tmp / "transcritor_falso.py", tmp / "falso.log"
    falso.write_text(TRANSCRITOR_FALSO, encoding="utf-8")
    proj = tmp / "projetos" / "Gravação de teste.screenstudio"
    gravacao_falsa(proj)
    ambiente = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "CLAQUETE_TRANSCRITOR": f"{shlex.quote(sys.executable)} {shlex.quote(str(falso))}",
                "FALSO_LOG": str(log)}

    def grav(*args):
        r = subprocess.run([sys.executable, "scripts/gravacao.py", *map(str, args)], cwd=raiz, capture_output=True, text=True, env=ambiente)
        return r.returncode, r.stdout + r.stderr

    arq = raiz / "edicoes" / "g.json"
    trab = raiz / "saida" / "edicoes" / "g"

    def roteiro(**mudar):
        r = json.loads(arq.read_text(encoding="utf-8"))
        r.update(mudar)
        arq.write_text(json.dumps(r, ensure_ascii=False))

    rc, out = grav("novo", "g", "--projeto", tmp)
    confere("gravação: novo recusa pasta que não é projeto do Screen Studio", rc == 1 and "Screen Studio" in out)
    rc, out = grav("novo", "g", "--projeto", proj)
    rc2, out2 = grav("transcrever", "g")
    ws = json.loads((trab / "transcricao" / "palavras.json").read_text()) if rc2 == 0 else []
    confere("gravação: transcreve a fala palavra a palavra, no computador", rc == 0 and [w["w"] for w in ws] == [x for x in FALA if isinstance(x, str)])
    if len(ws) != 14:
        print(out, out2)
        return
    roteiro(remover=[[3, 3], [7, 7]], acelerar=[{"de": 5.7, "ate": 8.6, "vel": 4}], proibidos=[{"de": 9.1, "ate": 9.45, "antes": 9.0, "depois": 9.5}],
            zooms=[{"de": 1.5, "ate": 2.5, "escala": 1.6, "x": 320, "y": 180}], mascaras=[{"de": 0, "ate": 3, "retangulos": [[10, 10, 100, 30]]}])
    rc, out = grav("plano", "g")
    plano = json.loads((trab / "plano.json").read_text()) if rc == 0 else {"trechos": [], "fica": []}
    tr = plano["trechos"]
    confere("gravação: o plano tira a muleta e a repetição e deixa as outras palavras", plano["fica"] == [0, 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13])
    confere("gravação: a pausa longa encolhe (do silêncio de 1,5 s só ficam as bordas)",
            bool(tr) and not any(t["ini"] < 3.85 and t["fim"] > 2.6 for t in tr if not t["mudo"]))
    confere("gravação: a espera acelerada vira trecho mudo, e o proibido congela a tela com a fala por cima",
            any(t["mudo"] and t["vel"] == 4 for t in tr) and any(t.get("congelar") == 9.5 and not t["mudo"] for t in tr))
    roteiro(proibidos=[{"de": 6.0, "ate": 7.0}])
    rc, out = grav("plano", "g")
    confere("gravação: espera acelerada que cruza um trecho proibido é recusada", rc == 1 and "cruza o proibido" in out)
    roteiro(proibidos=[{"de": 9.1, "ate": 9.45, "antes": 9.0, "depois": 9.5}])
    grav("plano", "g")

    rc, out = grav("renderizar", "g", "--versao", "editada")
    confere("gravação: renderizar sem o ok ao plano para no portão 1", rc == 2 and "ok da pessoa" in out)
    rc, _ = grav("aprovar", "g")
    roteiro(zooms=[{"de": 1.5, "ate": 2.6, "escala": 1.5, "x": 300, "y": 180}])
    k = carregar_gravacao(raiz)
    r = k.roteiro("g")
    confere("gravação: ajustar um zoom não pede ok novo", rc == 0 and k.aprovado(r))
    roteiro(remover=[[3, 3], [7, 7], [12, 12]])
    confere("gravação: mudar o que sai da fala pede ok novo", not k.aprovado(k.roteiro("g")))
    roteiro(remover=[[3, 3], [7, 7]])
    pausas = json.loads(arq.read_text(encoding="utf-8"))["pausas"]
    roteiro(pausas={**pausas, "minima": 0.6})
    rc, out = grav("audio", "g")
    confere("gravação: o audio recusa plano velho (o roteiro mudou depois do plano)", rc == 1 and "depois do plano" in out)
    roteiro(pausas=pausas)
    grav("plano", "g")
    grav("audio", "g")
    grav("conferir", "g")
    rc, out = grav("conferir", "g", "--aprovado")
    confere("gravação: conferir --aprovado recusa corte sem prova", rc == 1 and "sem prova" in out)
    rc, out = grav("emendas", "g")
    em = json.loads((trab / "transcricao" / "emendas.json").read_text()) if rc == 0 else {"cortes": []}
    confere("gravação: as duas emendas saem provadas (transcrição de 1,6 s antes e depois)",
            len(em["cortes"]) == 2 and all(c["nota"] >= 0.99 for c in em["cortes"]))
    rc, out = grav("conferir", "g")
    confere("gravação: depois das emendas a fala editada velha é recusada (o plano mudou)", rc == 1 and "fala editada não é a do plano" in out)
    grav("audio", "g")
    p = json.loads((trab / "plano.json").read_text())
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(trab / "audio-editada.wav")],
                               capture_output=True, text=True).stdout or 0)
    confere("gravação: a fala editada tem o tamanho exato do vídeo", abs(dur - p["quadros"] / 30) < 0.03)
    rc, out = grav("conferir", "g")
    c = json.loads((trab / "conferencia.json").read_text()) if (trab / "conferencia.json").exists() else {}
    confere("gravação: conferir transcreve a fala editada e para no portão 2", rc == 2 and c.get("semelhanca") == 1.0)
    rc, out = grav("conferir", "g", "--aprovado")
    confere("gravação: conferir --aprovado libera", rc == 0)
    (trab / "conferencia-aprovada.json").unlink(missing_ok=True)
    rc, out = grav("renderizar", "g", "--versao", "editada")
    confere("gravação: renderizar sem a revisão da fala editada para no portão 2", rc == 2 and "revisão" in out)
    c["semelhanca"] = 0.5
    (trab / "conferencia.json").write_text(json.dumps(c, ensure_ascii=False))
    rc, out = grav("conferir", "g", "--aprovado")
    confere("gravação: fala editada que não bate com o texto esperado não se aprova", rc == 1 and "bate" in out)
    grav("conferir", "g")
    grav("conferir", "g", "--aprovado")

    rc, out = grav("montar", "g")
    pub = trab / "editada" / "publico"
    dados = json.loads((pub / "dados.json").read_text()) if rc == 0 else {"quadros": -1, "tela": {"partes": []}}
    partes_ok = all(int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets",
                                        "-of", "csv=p=0", str(pub / a)], capture_output=True, text=True).stdout.strip().split(",")[0]) == min(900, dados["quadros"])
                    for a in dados["tela"]["partes"])
    confere("gravação: montar faz a tela e a câmera do tamanho exato do plano, com cursor e clique",
            rc == 0 and dados["quadros"] == p["quadros"] and partes_ok and dados["tela"]["cliques"] and (pub / "cursores" / "arrow.png").exists())

    original = hashlib.sha256((proj / "project.json").read_bytes()).hexdigest()
    rc, out = grav("fatias", "g", "--nome", "Copia")
    confere("gravação: as fatias recusam mostrar no Screen Studio o trecho proibido e a máscara",
            rc == 1 and "proibido" in out and "máscara" in out and not (proj.parent / "Copia.screenstudio").exists())

    roteiro(hibrido={"blocos": [{"nome": "fim", "de": 8.6, "ate": 11}, {"nome": "fim de novo", "de": 9.4, "ate": 11}]})
    grav("plano", "g")
    grav("aprovar", "g")
    rc, out = grav("hibrido", "g")
    confere("gravação: a mesma fala em dois blocos é recusada", rc == 1 and "dois blocos" in out)
    cena = {"de": 8.6, "ate": 10.4, "tela": {"tipo": "lista", "titulo": "Os *números*", "itens": [{"texto": "Nove", "quando": "nove"}, {"texto": "Vinte", "quando": "vinte"}]}}
    roteiro(hibrido={"blocos": [{"nome": "fim", "de": 8.6, "ate": 11}, {"nome": "começo", "de": 0, "ate": 5.7}], "cenas": [cena]},
            mascaras=[{"de": 9.0, "ate": 10.0, "retangulos": [[10, 10, 100, 30]]}])
    grav("plano", "g")
    grav("aprovar", "g")
    rc, out = grav("hibrido", "g")
    confere("gravação: cena que entra numa palavra que a fala não tem é recusada", rc == 1 and "vinte" in out)
    cena["tela"]["itens"][1] = {"texto": "Doze", "quando": "doze"}
    roteiro(hibrido={"blocos": [{"nome": "fim", "de": 8.6, "ate": 11}, {"nome": "começo", "de": 0, "ate": 5.7}], "cenas": [cena]})
    grav("plano", "g")
    grav("aprovar", "g")
    rc, out = grav("hibrido", "g")
    h = json.loads((trab / "hibrida" / "publico" / "dados.json").read_text()) if rc == 0 else {"legendas": [{"palavras": [{"w": "?"}]}], "cenas": []}
    confere("gravação: a híbrida remonta a fala na ordem nova, com a cena por cima",
            rc == 0 and h["legendas"][0]["palavras"][0]["w"] == "Nove" and len(h["cenas"]) == 1 and h["cenas"][0]["q0"] == 0)

    rc, out = grav("fatias", "g", "--nome", "Copia")
    copia = proj.parent / "Copia.screenstudio"
    j = json.loads((copia / "project.json").read_text())["json"] if rc == 0 else {"config": {}}
    sl = j.get("scenes", [{}])[0].get("slices", [])
    soma = sum((x["sourceEndMs"] - x["sourceStartMs"]) * x["timeScale"] for x in sl) / 1000
    fat = json.loads((trab / "fatias.json").read_text()) if rc == 0 else {"duracao": -1}
    confere("gravação: as fatias vão para uma CÓPIA do projeto, em ordem, com a câmera em bolinha e sem a legenda do app",
            rc == 0 and len(sl) > 1 and abs(soma - fat["duracao"]) < 0.05 and [x["sourceStartMs"] for x in sl] == sorted(x["sourceStartMs"] for x in sl)
            and j["config"].get("styles", {}).get("cameraBorderRadiusRatio01") == 1 and j["config"].get("captions", {}).get("enableTranscript") is False
            and j["config"].get("defaultLayout", {}).get("cameraOverlay", {}).get("overlayCameraSizeRatio01") == 0.32)
    confere("gravação: o projeto original fica intacto", hashlib.sha256((proj / "project.json").read_bytes()).hexdigest() == original)
    rc, out = grav("fatias", "g", "--nome", "Copia")
    confere("gravação: as fatias não sobrescrevem uma cópia que já existe", rc == 1 and "já existe" in out)

    def exportacao(nome, segundos):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=30:duration={segundos:.3f}", "-f", "lavfi",
                        "-i", f"sine=frequency=500:duration={segundos:.3f}", "-shortest", "-pix_fmt", "yuv420p", str(tmp / nome)], check=True)
        return tmp / nome
    rc, out = grav("hibrido", "g", "--exportacao", exportacao("errada.mp4", fat["duracao"] + 4))
    confere("gravação: exportação que não bate com as fatias é recusada", rc == 1 and "exportação tem" in out)
    rc, out = grav("hibrido", "g", "--exportacao", exportacao("certa.mp4", fat["duracao"]))
    h = json.loads((trab / "hibrida" / "publico" / "dados.json").read_text()) if rc == 0 else {}
    confere("gravação: com a exportação, a tela da híbrida é a do Screen Studio", rc == 0 and h.get("telaPronta") and h.get("tela") is None)

    roteiro(reels={"max_segundos": 2, "cortes": [{"id": "r1", "gancho": "Um *gancho*", "titulo": "T", "trechos": [[8.6, 11], [0, 2.6]]}]})
    grav("plano", "g")
    grav("aprovar", "g")
    rc, out = grav("reels", "g")
    confere("gravação: corte em pé acima do máximo é recusado", rc == 1 and "máximo" in out)
    roteiro(reels={"cortes": [{"id": "r1", "gancho": "Um *gancho*", "titulo": "T", "trechos": [[8.6, 11], [0, 2.6]]}]})
    grav("plano", "g")
    grav("aprovar", "g")
    rc, out = grav("reels", "g")
    rl = json.loads((trab / "reels" / "publico" / "dados-r1.json").read_text()) if rc == 0 else {"quadros": 0, "blocos": []}
    fonte = sum(t["fim"] - t["ini"] for t in json.loads((trab / "plano.json").read_text())["trechos"]
                if (8.6 <= t["ini"] < 11 or 0 <= t["ini"] < 2.6))
    confere("gravação: o corte em pé sai a 1,3x, com legenda de até 3 palavras",
            rc == 0 and abs(rl["quadros"] / 30 - fonte / 1.3) < 0.2 and all(len(b["palavras"]) <= 3 for b in rl["blocos"]) and rl["blocos"])

    grav("montar", "g")
    k = carregar_gravacao(raiz)
    k.MINIMO_LIVRE_GB = 10 ** 9
    try:
        k.cmd_renderizar(k.roteiro("g"), "editada")
        confere("gravação: render recusa com o disco quase cheio", False)
    except k.Erro as e:
        confere("gravação: render recusa com o disco quase cheio", "livres" in str(e))
        "livres" in str(e) or print(e)
    rc, out = grav("entregar", "g", "--destino", tmp / "entregue")
    confere("gravação: entregar sem vídeo pronto não apaga nada", rc == 1 and (trab / "plano.json").exists())
    # o transcritor do Screen Studio devolve o resultado guardado quando o caminho se repete: a mesma fala editada
    # conferida duas vezes (e cada prova de emenda) tem de ir com um nome novo
    grav("conferir", "g")
    nomes = log.read_text().split()
    confere("gravação: cada transcrição vai ao transcritor com um nome de arquivo novo", len(nomes) >= 5 and len(set(nomes)) == len(nomes))


def carregar_gravacao(raiz):
    sys.path.insert(0, str(raiz / "scripts"))
    for m in ("gravacao", "kit"):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location("gravacao", raiz / "scripts" / "gravacao.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.path.pop(0)
    return m


# ── o idioma (2.3): o pt-BR é o padrão e não se move; o en-US vive em linguas.en-US ─────────────────────────

def testes_idioma(raiz, tmp):
    repo = ESTUDIO.parent
    k = carregar_kit(raiz)
    arq = raiz / "kit.config.json"

    # As skills existem nos dois idiomas e com os MESMOS nomes de pasta: é por eles que o instalador
    # instala, o --desinstalar remove e a skill de entrada chama as outras.
    # (Só no repositório da Claquete: no estúdio de quem instalou não existem skills/ nem skills-en/.)
    if (repo / "skills").is_dir():
        pt = {d.name for d in (repo / "skills").iterdir() if (d / "SKILL.md").exists()}
        en = {d.name for d in (repo / "skills-en").iterdir() if (d / "SKILL.md").exists()} if (repo / "skills-en").exists() else set()
        confere("skills-en/ traz as mesmas skills de skills/, com os mesmos nomes",
                en == pt and len(pt) > 0)
        faltando = sorted(pt - en)
        faltando and print("           faltam em skills-en/:", ", ".join(faltando))

        # Toda SKILL.md em inglês precisa do `metadata.resumo`, que o instalador imprime no terminal.
        sem_resumo = [d.name for d in (repo / "skills-en").iterdir()
                      if (d / "SKILL.md").exists() and not re.search(r"^\s+resumo:\s*\S", (d / "SKILL.md").read_text(encoding="utf-8"), re.M)] if (repo / "skills-en").exists() else []
        confere("toda skill em inglês tem o resumo que o instalador mostra", sem_resumo == [])
    else:
        print("pulado  skills-en/ (fora do repositório da Claquete)")

    # O pt-BR de hoje continua sendo o padrão, e o encanamento não pode ter mexido nisso.
    c = json.loads(arq.read_text(encoding="utf-8"))
    no_repo = (repo / "skills").is_dir()  # fora dele, a pessoa pode ter trocado voz, pronúncia e convite
    confere("o estúdio do teste roda em pt-BR", c.get("idioma") == "pt-BR")
    confere("o conteúdo pt-BR continua no topo (voz, pronúncia, convite)",
            all(k in c for k in ("voz", "pronuncia", "convite")) and (not no_repo or (c["voz"]["elevenlabs"]["nome"] == "Raquel" and "IA" in c["pronuncia"])))

    # A assinatura da narração NÃO pode mudar em pt-BR: mudar invalidaria toda narração já paga e a
    # pessoa pagaria de novo pelo mesmo áudio. Este é o teste que protege o bolso dela.
    fala = "Primeiro, diga quem você é e para quem é o texto."
    original = hashlib.sha256(json.dumps([fala, c["voz"],
                                          {kk: vv for kk, vv in c["pronuncia"].items()
                                           if not kk.startswith("_") and re.search(rf"(?<!\w){re.escape(kk)}(?!\w)", fala)}],
                                         sort_keys=True).encode()).hexdigest()[:16]
    confere("a assinatura da narração em pt-BR continua a mesma (ninguém paga áudio de novo)",
            k.assinatura_parte(fala, c) == original)

    # Os catálogos de mensagem: as duas metades têm de ter as mesmas chaves, senão uma cai no português
    # no meio de uma execução em inglês.
    import idioma as M
    confere("os catálogos de mensagem têm as mesmas chaves nos dois idiomas", M.chaves_diferentes() == {})
    confere("o pt-BR de hoje continua no catálogo (o teste é a rede de regressão)",
            M.t(c, "montar_plano", n=3, total=12.5).startswith("  plano:") and "portao_roteiro" in M.TEXTO["pt-BR"])
    confere("o en-US tem texto próprio, não uma cópia do português",
            M.TEXTO["en-US"]["portao_roteiro"] != M.TEXTO["pt-BR"]["portao_roteiro"]
            and "aprovado" not in M.TEXTO["en-US"]["portao_roteiro"])

    # Trocar para en-US muda voz, convite, pronúncia e o locale da transcrição — e SÓ isso: as
    # constantes de língua mudam o valor, não a forma, para o hash voltar a bater ao voltar o idioma.
    en = dict(c, idioma="en-US")
    confere("em en-US a voz é outra, com voice_id próprio",
            k.voz(en)["elevenlabs"]["voice_id"] != c["voz"]["elevenlabs"]["voice_id"]
            and (not no_repo or (k.voz(en)["elevenlabs"]["nome"] == "Lauren" and k.voz(en)["elevenlabs"].get("dono_publico"))))
    if no_repo:
        confere("em en-US o convite é o inglês", k.convite(en)["titulo"] != k.convite(c)["titulo"])
    confere("em en-US a transcrição sai em inglês", k.lin(en, "transcricao")[1] == "en")
    confere("em en-US as muletas são as inglesas", "like" in k.lin(en, "muletas") and "né" not in k.lin(en, "muletas"))
    confere("em en-US a busca de sigla não usa a classe acentuada do português",
            k.lin(en, "sigla") != k.lin(c, "sigla") and re.fullmatch(k.lin(en, "sigla"), "IA") is not None)
    confere("a voz de testar a voz muda com o idioma", k.lin(en, "voz_teste") != k.lin(c, "voz_teste"))
    confere("trocar de idioma muda a assinatura da narração (a parte é narrada de novo, na voz nova)",
            k.assinatura_parte(fala, en) != k.assinatura_parte(fala, c))

    # Um roteiro de edição criado agora já nasce com o locale do estúdio (era pt_BR fixo: inglês sairia
    # transcrito como português, sem erro nenhum).
    import importlib.util as iu
    spec = iu.spec_from_file_location("gravacao_idioma", raiz / "scripts" / "gravacao.py")
    g = iu.module_from_spec(spec)
    spec.loader.exec_module(g)
    confere("o roteiro de edição nasce no idioma do estúdio", g.MODELO["idioma"] == "pt_BR" and "idioma" in g.MODELO)
    confere("com o estúdio em inglês, o roteiro de edição nasce em inglês",
            g.K.lin(en, "transcricao")[0] == "en_US")


def main():
    if "--licenca" in sys.argv:
        ruins = licenca_react_bits(sys.argv[sys.argv.index("--licenca") + 1:])
        for f in ruins:
            print(f"RECUSADO: {f} é componente do React Bits (a licença não deixa redistribuir; ele é baixado na máquina de quem instala)")
        sys.exit(1 if ruins else 0)
    testes_licenca()
    tmp = Path(tempfile.mkdtemp())
    raiz = tmp / "estudio"
    shutil.copytree(ESTUDIO, raiz, ignore=shutil.ignore_patterns("node_modules", ".venv", "saida", "aulas", "edicoes", "public", "dist", "react-bits"))
    # As travas não dependem de idioma, mas as conferências abaixo casam as mensagens em português: num estúdio
    # instalado em inglês, a CÓPIA do teste roda em pt-BR (o estúdio da pessoa não é tocado).
    cfg_copia = json.loads((raiz / "kit.config.json").read_text(encoding="utf-8"))
    if cfg_copia.get("idioma", "pt-BR") != "pt-BR":
        cfg_copia["idioma"] = "pt-BR"
        (raiz / "kit.config.json").write_text(json.dumps(cfg_copia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (raiz / "cenas" / "src" / "aulas").mkdir(parents=True, exist_ok=True)
    shutil.copy(ESTUDIO / "cenas" / "src" / "aulas" / "animada-exemplo.jsx", raiz / "cenas" / "src" / "aulas" / "animada-exemplo.jsx")
    (raiz / "aulas").mkdir()
    (raiz / "public").mkdir()
    for f in ("fundos",):
        if (ESTUDIO / "public" / f).exists():
            shutil.copytree(ESTUDIO / "public" / f, raiz / "public" / f)
    shutil.copy(ESTUDIO / "aulas" / "exemplo.json", raiz / "aulas" / "exemplo.json")
    shutil.copy(ESTUDIO / "aulas" / "tutorial-exemplo.json", raiz / "aulas" / "tutorial-exemplo.json")
    shutil.copy(ESTUDIO / "aulas" / "animada-exemplo.json", raiz / "aulas" / "animada-exemplo.json")

    rc, out = kit(raiz, "novo", "x", "--tipo", "aula")
    confere("aula sem --minutos é recusada (a pessoa escolhe a duração)", rc == 1 and "minutos" in out)
    rc, out = kit(raiz, "novo", "x", "--tipo", "aula", "--minutos", "3")
    confere("novo cria a aula com tipo e minutos", rc == 0 and json.loads((raiz / "aulas" / "x.json").read_text())["minutos"] == 3)

    rc, out = kit(raiz, "narrar", "exemplo")
    confere("narrar recusa roteiro sem ok (portão 1)", rc == 1 and "aprovado" in out)
    rc, out = kit(raiz, "fazer", "exemplo")
    confere("fazer para no portão 1 com código 2 e gera o plano", rc == 2 and (raiz / "saida" / "exemplo" / "roteiro-e-plano.md").exists())
    rc, _ = kit(raiz, "aprovar", "exemplo")
    confere("aprovar registra o ok", rc == 0 and (raiz / "aulas" / "exemplo.aprovado.json").exists())

    a = json.loads((raiz / "aulas" / "exemplo.json").read_text(encoding="utf-8"))
    a["partes"][0]["fala"] += " Mudou."
    (raiz / "aulas" / "exemplo.json").write_text(json.dumps(a, ensure_ascii=False))
    rc, out = kit(raiz, "narrar", "exemplo")
    confere("roteiro mudado depois do ok pede ok novo", rc == 1 and "aprovado" in out)
    shutil.copy(ESTUDIO / "aulas" / "exemplo.json", raiz / "aulas" / "exemplo.json")
    shutil.copy(ESTUDIO / "aulas" / "tutorial-exemplo.json", raiz / "aulas" / "tutorial-exemplo.json")

    narracao_falsa(raiz, "exemplo")
    rc, out = kit(raiz, "montar", "exemplo")
    confere("montar recusa fala sem revisão (portão 2)", rc == 2 and "revisão" in out)
    rc, out = kit(raiz, "conferir", "exemplo", "--aprovado")
    confere("--aprovado sem relatório é recusado", rc == 1)
    rc, out = kit(raiz, "conferir", "exemplo")
    confere("conferir gera o relatório e para com código 2", rc == 2 and (raiz / "public" / "aulas" / "exemplo" / "conferencia.json").exists())
    rc, _ = kit(raiz, "conferir", "exemplo", "--aprovado")
    confere("conferir --aprovado libera", rc == 0 and (raiz / "public" / "aulas" / "exemplo" / "conferencia-aprovada.json").exists())
    rc, out = kit(raiz, "montar", "exemplo")
    confere("depois dos dois portões o montar segue (para só no ritmo ou na duração, nunca no portão)", rc != 2 and "revisão" not in out)

    p = raiz / "public" / "aulas" / "exemplo" / "parte-02.json"
    m = json.loads(p.read_text())
    m["assinatura"] = "narrada-de-novo"
    p.write_text(json.dumps(m))
    rc, out = kit(raiz, "montar", "exemplo")
    confere("parte narrada de novo depois da revisão volta ao portão 2", rc == 2)

    a = json.loads((raiz / "aulas" / "exemplo.json").read_text(encoding="utf-8"))
    a["tipo"], a["minutos"] = "aula", 2
    (raiz / "aulas" / "exemplo.json").write_text(json.dumps(a, ensure_ascii=False))
    kit(raiz, "aprovar", "exemplo")
    kit(raiz, "conferir", "exemplo")
    kit(raiz, "conferir", "exemplo", "--aprovado")
    rc, out = kit(raiz, "montar", "exemplo")
    confere("aula de 2 min com menos de 1 min de vídeo é recusada pela duração", rc == 1 and "aceita de" in out)

    rc, out = kit(raiz, "entregar", "exemplo", "--destino", str(tmp / "entregue"))
    confere("entregar sem vídeo pronto não apaga nada", rc == 1 and (raiz / "public" / "aulas" / "exemplo").exists())

    # demonstração: o roteiro se aprova ANTES de gravar
    rc, out = kit(raiz, "plano", "tutorial-exemplo")
    md = (raiz / "saida" / "tutorial-exemplo" / "roteiro-e-plano.md")
    confere("plano sai sem a gravação feita (ela vem depois do ok)", rc == 0 and md.exists() and "A gravar depois do ok" in md.read_text()
            and "não existe em public" not in md.read_text())
    confere("plano mostra o caminho na ferramenta", md.exists() and "Caminho na ferramenta" in md.read_text() and "Clicar em Gerar" in md.read_text())
    rc, _ = kit(raiz, "aprovar", "tutorial-exemplo")
    k = carregar_kit(raiz)
    t = json.loads((raiz / "aulas" / "tutorial-exemplo.json").read_text(encoding="utf-8"))
    t["partes"][1]["tela"]["de"] = 9.9
    (raiz / "aulas" / "tutorial-exemplo.json").write_text(json.dumps(t, ensure_ascii=False))
    confere("acertar o 'de' depois de gravar não pede ok novo", rc == 0 and k.aprovado("tutorial-exemplo"))
    t["caminho"].append("Passo novo")
    (raiz / "aulas" / "tutorial-exemplo.json").write_text(json.dumps(t, ensure_ascii=False))
    confere("mudar o caminho pede ok novo", not k.aprovado("tutorial-exemplo"))
    rc, out = kit(raiz, "montar", "tutorial-exemplo")
    confere("montar recusa sem a gravação", rc == 1 and "não existe" in out)

    # a narração de uma parte só se paga de novo se algo DELA mudou
    c = k.cfg()
    a1 = k.assinatura_parte("A IA ajuda.", c)
    c["pronuncia"]["PJe"] = "outra coisa"
    a2 = k.assinatura_parte("A IA ajuda.", c)
    c["pronuncia"]["IA"] = "ia"
    a3 = k.assinatura_parte("A IA ajuda.", c)
    confere("pronúncia de outra palavra não muda a assinatura; a desta fala muda", a1 == a2 and a2 != a3)

    # finalizar de novo (para a versão de página) sem o render bruto
    shutil.copy(ESTUDIO / "aulas" / "exemplo.json", raiz / "aulas" / "exemplo.json")
    cfg = json.loads((raiz / "kit.config.json").read_text())
    cfg["travas"]["tela_parada_segundos"] = 30  # a voz falsa espalha as palavras por igual: aqui o ritmo não é o que se testa
    (raiz / "kit.config.json").write_text(json.dumps(cfg, ensure_ascii=False))
    kit(raiz, "aprovar", "exemplo")
    narracao_falsa(raiz, "exemplo")
    kit(raiz, "conferir", "exemplo")
    kit(raiz, "conferir", "exemplo", "--aprovado")
    rc, out = kit(raiz, "montar", "exemplo")
    if rc:
        print(out)
    if (raiz / "public" / "aulas" / "exemplo" / "plano.json").exists():
        plano = json.loads((raiz / "public" / "aulas" / "exemplo" / "plano.json").read_text())
        confere("o plano sempre traz os dois formatos", plano["formatos"] == ["h", "v"])
        (raiz / "saida" / "exemplo").mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=30:duration={plano['total']:.2f}",
                        "-f", "lavfi", "-i", f"sine=duration={plano['total']:.2f}", "-shortest", "-pix_fmt", "yuv420p",
                        str(raiz / "saida" / "exemplo" / "exemplo-h.mp4")], check=True)
        rc, out = kit(raiz, "finalizar", "exemplo")
        confere("finalizar roda de novo sobre o vídeo já finalizado", rc == 0)
        rc, out = kit(raiz, "finalizar", "exemplo", "--formatos", "v")
        confere("finalizar sem render nenhum avisa o que falta", rc == 1 and "não há render" in out)
    else:
        confere("montar do exemplo gerou o plano (pré-requisito dos testes do finalizar)", False)

    # marca: fundo claro leva o resto da paleta junto, e a fonte vira import
    (raiz / "marca").mkdir(exist_ok=True)
    (raiz / "marca" / "marca.json").write_text(json.dumps({"nome": "Marca Clara", "cores": {"principal": "#1a4fd6", "fundo": "#f7f5ef"},
                                                            "fontes": {"titulos": "Playfair Display", "texto": "Montserrat"}}))
    rc, out = kit(raiz, "marca")
    tema = json.loads((raiz / "kit.config.json").read_text())["tema"]
    gen = (raiz / "src" / "fontes.gen.ts").read_text()
    confere("fundo claro deixa o texto escuro e os painéis claros", rc == 0 and tema["texto"] == "#14171a" and k.escuro(tema["texto"])
            and not k.escuro(tema["fundo2"]) and not k.escuro(tema["janela"]) and tema["fundo_imagem"] == "")
    confere("as fontes da marca entram no fontes.gen.ts (com a Inter de reserva)",
            all(f"@remotion/google-fonts/{m}" in gen for m in ("PlayfairDisplay", "Montserrat", "Inter")))
    if (ESTUDIO / "node_modules").exists():
        (raiz / "node_modules").symlink_to(ESTUDIO / "node_modules")
        (raiz / "marca" / "marca.json").write_text(json.dumps({"nome": "X", "fontes": {"titulos": "Fonte Que Nao Existe"}}))
        rc, out = kit(raiz, "marca")
        confere("fonte fora do Google Fonts é recusada", rc == 1 and "Google Fonts" in out)

    # telas animadas (2.1): a cena é escrita depois do ok, fotografada no tempo da voz, e o montar recusa sem a foto
    an = json.loads((raiz / "aulas" / "animada-exemplo.json").read_text(encoding="utf-8"))
    sem = json.loads(json.dumps(an))
    del sem["partes"][0]["tela"]["descricao"]
    (raiz / "aulas" / "animada-sem.json").write_text(json.dumps(sem, ensure_ascii=False))
    rc, out = kit(raiz, "validar", "animada-sem")
    confere("tela animada sem descrição é recusada (a pessoa aprova o que a cena mostra)", rc == 1 and "descricao" in out)
    falta = json.loads(json.dumps(an))
    falta["partes"][1]["tela"]["cena"] = "CenaQueNaoExiste"
    (raiz / "aulas" / "animada-falta.json").write_text(json.dumps(falta, ensure_ascii=False))
    rc, out = kit(raiz, "plano", "animada-falta")
    md = (raiz / "saida" / "animada-falta" / "roteiro-e-plano.md").read_text()
    confere("cena ainda não escrita é só aviso no plano, na lista do que escrever depois do ok",
            rc == 0 and "Cenas animadas a escrever depois do ok" in md and "CenaQueNaoExiste" in md and "**Cena animada** (Cena1)" in md)
    kit(raiz, "aprovar", "animada-exemplo")
    narracao_falsa(raiz, "animada-exemplo")
    rc, out = kit(raiz, "cenas", "animada-exemplo")
    confere("cenas antes da revisão da fala para no portão 2", rc == 2)
    kit(raiz, "conferir", "animada-exemplo")
    kit(raiz, "conferir", "animada-exemplo", "--aprovado")
    rc, out = kit(raiz, "cenas", "animada-exemplo")
    confere("cenas sem o app instalado diz o que fazer", rc == 1 and "npm install" in out)
    rc, out = kit(raiz, "montar", "animada-exemplo")
    confere("montar recusa tela animada sem a foto da cena", rc == 1 and "kit.py cenas animada-exemplo" in out)
    k2 = carregar_kit(raiz)
    d = raiz / "public" / "aulas" / "animada-exemplo"
    feitas = {}
    for i, p in enumerate(an["partes"], 1):
        meta = json.loads((d / f"parte-{i:02d}.json").read_text())
        dur = k2.duracao_audio(d / f"parte-{i:02d}.mp3") + (0.35 if i < len(an["partes"]) else k2.FOLGA_FINAL)
        feitas[str(i)] = k2.assinatura_cena("animada-exemplo", i, p, meta, k2.cfg(), dur)
        for f in ("h", "v"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=1", "-pix_fmt", "yuv420p",
                            str(d / f"cena-{i:02d}-{f}.mp4")], check=True)
    (d / "cenas.json").write_text(json.dumps(feitas))
    rc, out = kit(raiz, "montar", "animada-exemplo")
    plano = json.loads((d / "plano.json").read_text()) if (d / "plano.json").exists() else {}
    confere("com as cenas fotografadas o montar segue e o plano aponta os clipes dos dois formatos",
            rc == 0 and plano.get("partes", [{}])[0].get("tela", {}).get("clipes", {}).get("v") == "aulas/animada-exemplo/cena-01-v.mp4")
    arq = raiz / "cenas" / "src" / "aulas" / "animada-exemplo.jsx"
    arq.write_text(arq.read_text() + "\n// mudou\n")
    rc, out = kit(raiz, "montar", "animada-exemplo")
    confere("mudou o código da cena: o montar pede a foto de novo", rc == 1 and "kit.py cenas" in out)

    # disco quase cheio: o render nem começa
    k.MINIMO_LIVRE_GB = 10 ** 9
    try:
        k.renderizar("exemplo", ["h"])
        confere("render recusa com o disco quase cheio", False)
    except k.Erro as e:
        confere("render recusa com o disco quase cheio", "livres" in str(e))

    testes_gravacao(raiz, tmp)

    testes_idioma(raiz, tmp)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'TUDO CERTO' if not falhas else str(len(falhas)) + ' FALHA(S)'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
