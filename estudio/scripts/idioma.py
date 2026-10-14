#!/usr/bin/env python3
"""O idioma do estúdio: o que muda de um idioma para o outro, num lugar só.

    import idioma as M
    M.lin(cfg, "ritmo")        # parâmetro de língua do idioma ativo
    M.t(cfg, "portao1")        # mensagem que a pessoa lê, no idioma dela

Por que este módulo existe, e por que os números ficam no CÓDIGO e não no `kit.config.json`:

- O `kit.config.json` é da pessoa. O `--atualizar` do instalador usa uma mesclagem que só acrescenta
  chave ausente e nunca sobrescreve o que já está lá: é o que protege a marca e as cores dela. Se os
  parâmetros de língua morassem ali, um palpite errado nosso (`ritmo` em inglês, o tamanho do bloco
  de legenda) ficaria congelado na máquina de todo mundo para sempre.
- Aqui, ao contrário, este arquivo é copiado inteiro pelo `--atualizar`. Um número que a prática
  mostrar errado se conserta numa linha, e chega a todas as instalações.

O pt-BR é o idioma padrão e o que está escrito no `kit.config.json` no topo; o en-US vive em
`linguas.en-US`, e chave ausente lá cai no valor do pt-BR.
"""
import re

# ── mensagens ──────────────────────────────────────────────────────────────
# As chaves são iguais nos dois idiomas (há teste que confere). O pt-BR é o texto de hoje, byte a byte:
# é ele que as asserções do teste.py casam por substring, e é a rede de regressão da tradução.
TEXTO = {
    "pt-BR": {
        # portões: é a mensagem que a pessoa lê quando o programa para de propósito (código 2)
        "portao_roteiro": "o roteiro ainda não foi aprovado (ou mudou depois do ok). Rode: kit.py plano {id}, mostre e, com o ok, kit.py aprovar {id}",
        "portao_fala": "revisão da fala: um subagente da sessão lê {rel} e confere cada parte (fala exata, pronúncia, siglas, palavras que soam iguais{local}). Aprovou: kit.py conferir {id} --aprovado. Reprovou: reescreva a frase e narre a parte de novo.",
        "portao_fala_sem_local": "; sem transcrição local, a pessoa ouve os áudios",
        "portao_fala_cena": "a fala ainda não foi aprovada na revisão, e a cena anda no tempo das palavras: kit.py conferir {id}",
        # transcrição local
        "transcricao_local": "  transcrição local ({modelo}), {n} partes...",
        "transcricao_falhou": "  (transcrição local falhou: {erro})",
        # montagem
        "montar_plano": "  plano: {n} partes, {total:.1f} s, ritmo ok",
    },
    "en-US": {
        "portao_roteiro": "the script has not been approved yet (or it changed after the go-ahead). Run: kit.py plano {id}, show it, and with the go-ahead: kit.py aprovar {id}",
        "portao_fala": "narration review: a subagent of the session reads {rel} and checks every part (exact wording, pronunciation, acronyms, words that sound alike{local}). Approved: kit.py conferir {id} --aprovado. Rejected: rewrite the sentence and narrate that part again.",
        "portao_fala_sem_local": "; with no local transcription, the person listens to the audio files",
        "portao_fala_cena": "the narration has not been approved in the review yet, and the scene runs on the timing of the words: kit.py conferir {id}",
        "transcricao_local": "  local transcription ({modelo}), {n} parts...",
        "transcricao_falhou": "  (local transcription failed: {erro})",
        "montar_plano": "  plan: {n} parts, {total:.1f} s, pacing ok",
    },
}

# ── parâmetros de língua ───────────────────────────────────────────────────
PAUSAS_PT = {"limiar_db": -42, "voz_db": -43, "minima": 0.40, "sobra": 0.13}

# A transcrição escreve número em algarismo ("2 minutos") onde o roteiro tem "dois minutos": na
# comparação, os dois viram algarismo. "um" e "uma" ficam de fora (quase sempre são artigo).
NUMEROS_PT = {"zero": "0", "dois": "2", "duas": "2", "tres": "3", "quatro": "4", "cinco": "5", "seis": "6", "sete": "7",
              "oito": "8", "nove": "9", "dez": "10", "onze": "11", "doze": "12", "treze": "13", "catorze": "14", "quatorze": "14",
              "quinze": "15", "dezesseis": "16", "dezessete": "17", "dezoito": "18", "dezenove": "19", "vinte": "20",
              "trinta": "30", "quarenta": "40", "cinquenta": "50", "sessenta": "60", "setenta": "70", "oitenta": "80",
              "noventa": "90", "cem": "100"}

# O que a voz diz igual e o transcritor não distingue: o relatório da conferência aponta para o subagente.
HOMOFONOS_PT = [(r"\bpor qu[eê]\b|\bporqu[eê]\b", "por que / por quê / porque soam iguais: troque a construção ('os motivos')"),
                (r"\bma[lu]\b", "mal / mau soam iguais"), (r"\bcon[cs]erto\b", "conserto / concerto soam iguais"),
                (r"\b(sess|se[cç]|cess)[aã]o\b", "sessão / seção / cessão soam iguais")]

LING = {
    "pt-BR": {
        "ritmo": 2.5,                     # palavras por segundo, antes da velocidade da voz
        "numeros": NUMEROS_PT,
        "homofonos": HOMOFONOS_PT,
        "muletas": ["né", "ó", "certo", "enfim", "tipo", "hum"],
        "sigla": r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}\b",
        "transcricao": ("pt_BR", "pt"),    # (locale do Screen Studio, ISO do faster-whisper)
        "vtt": 42,                         # letras por bloco de legenda da aula
        "tela": {"h": 44, "v": 26},        # letras por bloco de legenda desenhada na tela
        "frases": 40,                      # letras por bloco, na gravação editada
        "reel": (3, 14),                   # (palavras, letras) por bloco, no corte em pé
        "voz_teste": "Olá! Esta é a voz do seu estúdio. Tudo pronto para a primeira aula.",
    },
    "en-US": {
        # Igual ao pt-BR de propósito: é uma estimativa usada só no aviso de duração do `validar` (o
        # `montar` mede a duração real dos mp3). Um palpite infundado é pior que nenhuma mudança.
        # Para medir: narre uma parte em inglês e compare `duracao_audio(mp3)` com `len(fala.split()) / x`.
        "ritmo": 2.5,
        # Vazios de propósito. `numeros` e `homofonos` existem para casar o que o transcritor devolve
        # diferente do roteiro; em inglês, mapear palavra funcional (`to` -> 2, `for` -> 4) injeta
        # falso-igual e falso-diferente na comparação do `conferir`. Sem um transcritor en-US rodado
        # de verdade, qualquer lista seria chute — e chute aqui polui o relatório da revisão.
        "numeros": {},
        "homofonos": [],
        # Muleta em inglês é UMA palavra: o `bruta()` do gravacao.py compara a muleta com um token da
        # transcrição, então "you know" (que viraria "youknow") e "I mean" ficariam inertes, sem erro.
        "muletas": ["like", "right", "well", "so", "actually", "basically"],
        "sigla": r"\b[A-Z]{2,}\b",
        "transcricao": ("en_US", "en"),
        "vtt": 42,
        "tela": {"h": 44, "v": 26},
        "frases": 40,
        "reel": (3, 14),
        "voz_teste": "Hi! This is the voice of your studio. Everything is ready for your first lesson.",
    },
}

PADRAO = "pt-BR"


def tag(c=None):
    """O idioma do estúdio (a chave `idioma` do kit.config.json), com o pt-BR de reserva."""
    if not isinstance(c, dict):
        return PADRAO
    return c.get("idioma") or PADRAO


def conhecido(t):
    return t in LING


def lin(c, campo):
    """Parâmetro de língua do idioma ativo. Campo que o idioma não define cai no valor do pt-BR."""
    t = tag(c)
    if t in LING and campo in LING[t]:
        return LING[t][campo]
    return LING[PADRAO][campo]


def t(c, chave, **kw):
    """A mensagem no idioma ativo. Chave que o idioma não tem cai no pt-BR (nunca devolve a chave crua)."""
    t_ = tag(c)
    texto = TEXTO.get(t_, {}).get(chave) or TEXTO[PADRAO].get(chave)
    if texto is None:
        raise KeyError(f"mensagem sem tradução: {chave}")
    return texto.format(**kw) if kw else texto


def tr(c, pt, en):
    """O texto do idioma ativo, escrito no lugar em que é usado (para títulos de relatório, em que o par
    lado a lado se lê melhor que uma chave no catálogo). Idioma sem tradução cai no pt-BR."""
    return en if tag(c) == "en-US" else pt


def chaves_diferentes():
    """Chaves que existem num idioma e faltam no outro. O teste usa isto; vazio é o esperado."""
    base = set(TEXTO[PADRAO])
    return {t_: sorted(base ^ set(v)) for t_, v in TEXTO.items() if set(v) != base}


def normalizar(valor):
    """`pt`, `pt_BR`, `pt-BR`, `en`, `en_US`, `en-US` -> a tag do estúdio. O resto: None."""
    v = re.sub(r"[^a-z]", "", str(valor or "").lower())
    if v.startswith("pt"):
        return "pt-BR"
    if v.startswith("en"):
        return "en-US"
    return None
