import React from "react";
import { AbsoluteFill, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Cena } from "../cenas/Cenas";
import { pilha } from "../fontes";
import type { Formato } from "../layout";
import { Ctx, useAmbiente } from "../pecas/contexto";
import { Fundo, Janela, Rotulo } from "../pecas/Moldura";
import { Kicker, Titulo } from "../pecas/Titulo";
import { entra, FPS } from "../tempo";
import type { CamadaTela, CenaGravada, Convite, Frase } from "./tipos";

// Peças das três versões da gravação editada (scripts/gravacao.py). As cores e as fontes são as da marca (tema).

export type Caixa = { x: number; y: number; w: number; h: number };
export const LIMITE = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const CURSOR = 1.5;

// Onde a tela gravada fica no deitado: o maior retângulo que cabe acima da legenda, centrado.
export const caixaDaTela = (W: number, H: number): Caixa => {
  const k = Math.min(1640 / W, 900 / H);
  return { x: (1920 - W * k) / 2, y: 34, w: W * k, h: H * k };
};

// Texto com o trecho entre *asteriscos* na cor de destaque.
export const comDestaque = (txt: string, cor: string) =>
  txt.split(/(\*[^*]+\*)/).map((p, i) => (p.startsWith("*") ? <span key={i} style={{ color: cor }}>{p.slice(1, -1)}</span> : <span key={i}>{p}</span>));

// A tela gravada, desenhada pelo estúdio: o vídeo (o Screen Studio 4 grava sem o cursor), o cursor do macOS, os cliques,
// o zoom com mola e as máscaras. No cartão (corte em pé) o zoom é mais fechado e segue o cursor quando não há zoom.
export const TelaGravada: React.FC<{ tela: CamadaTela; parte: number; caixa: Caixa; cartao?: boolean }> = ({ tela, parte, caixa, cartao }) => {
  const q = useCurrentFrame();
  const { tema } = useAmbiente();
  const ult = tela.quadros.length - 1;
  const [esc, zx, zy, cx, cy, cid, vis, seg, vel] = tela.quadros[Math.max(0, Math.min(q, ult))];
  const W = tela.largura;
  const H = tela.altura;
  let transform = `scale(${caixa.w / W}) translate(${W / 2 - zx * esc}px, ${H / 2 - zy * esc}px) scale(${esc})`;
  if (cartao) {
    const Z = Math.max(1, caixa.w / W, caixa.h / H) * Math.max(1, esc * 0.78);
    let sx = 0;
    let sy = 0;
    let n = 0;
    for (let j = Math.max(0, q - 20); j <= Math.min(ult, q + 20); j++) {
      const l = tela.quadros[j];
      if (l[6]) {
        sx += l[3];
        sy += l[4];
        n++;
      }
    }
    const peso = Math.min(1, Math.max(0, (esc - 1) / 0.3));
    const mw = caixa.w / (2 * Z);
    const mh = caixa.h / (2 * Z);
    const fx = Math.min(Math.max(peso * zx + (1 - peso) * (n ? sx / n : W / 2), mw), W - mw);
    const fy = Math.min(Math.max(peso * zy + (1 - peso) * (n ? sy / n : H / 2), mh), H - mh);
    transform = `translate(${caixa.w / 2 - fx * Z}px, ${caixa.h / 2 - fy * Z}px) scale(${Z})`;
  }
  const cursor = tela.cursores[cid];
  return (
    <div
      style={{
        position: "absolute",
        left: caixa.x,
        top: caixa.y,
        width: caixa.w,
        height: caixa.h,
        borderRadius: cartao ? 0 : 18,
        overflow: "hidden",
        background: "#000",
        boxShadow: cartao ? "none" : `0 30px 80px #0009, 0 0 0 1px ${tema.texto}14`,
      }}
    >
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transformOrigin: "0 0", transform }}>
        {tela.partes.map((arq, p) => (
          <Sequence key={p} from={p * parte} durationInFrames={parte} layout="none">
            <OffthreadVideo src={staticFile(arq)} muted style={{ position: "absolute", width: W, height: H }} />
          </Sequence>
        ))}
        {tela.mascaras
          .filter((m) => seg >= m.de && seg < m.ate)
          .flatMap((m, i) =>
            m.retangulos.map(([x, y, w, h], j) => (
              <div key={`${i}-${j}`} style={{ position: "absolute", left: x, top: y, width: w, height: h, background: m.cor ?? "#ffffff", borderRadius: 4 }} />
            )),
          )}
        {tela.cliques
          .filter((c) => q >= c.q && q < c.q + 14)
          .map((c, i) => {
            const p = (q - c.q) / 14;
            const raio = 12 + 46 * p;
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: c.x - raio,
                  top: c.y - raio,
                  width: raio * 2,
                  height: raio * 2,
                  borderRadius: "50%",
                  border: `5px solid ${tema.destaque}`,
                  opacity: 1 - p,
                }}
              />
            );
          })}
        {vis && cursor ? (
          <Img
            src={staticFile(`cursores/${cid}.png`)}
            style={{
              position: "absolute",
              left: cx - cursor.hx * CURSOR,
              top: cy - cursor.hy * CURSOR,
              width: cursor.w * CURSOR,
              height: cursor.h * CURSOR,
              filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.35))",
            }}
          />
        ) : null}
      </div>
      {vel > 0 ? (
        <div
          style={{
            position: "absolute",
            right: 22,
            top: 20,
            padding: "8px 18px",
            borderRadius: 999,
            background: `${tema.fundo}d9`,
            color: tema.destaque,
            fontFamily: pilha(tema.fonte_texto),
            fontSize: 30,
            fontWeight: 700,
          }}
        >
          ▶▶ {vel}x
        </div>
      ) : null}
    </div>
  );
};

// A exportação do Screen Studio (acabamento do app: fundo, zoom, cursor e a bolinha da câmera), em partes.
export const TelaPronta: React.FC<{ partes: string[]; parte: number }> = ({ partes, parte }) => (
  <>
    {partes.map((arq, p) => (
      <Sequence key={p} from={p * parte} durationInFrames={parte} layout="none">
        <OffthreadVideo src={staticFile(arq)} muted style={{ position: "absolute", width: 1920, height: 1080 }} />
      </Sequence>
    ))}
  </>
);

// A câmera da pessoa numa bolinha: o rosto nunca em tela cheia.
export const Bolinha: React.FC<{ partes: string[]; px: number; py: number; parte: number; x: number; y: number; l: number; opacidade: number }> = ({
  partes,
  px,
  py,
  parte,
  x,
  y,
  l,
  opacidade,
}) => {
  const { tema } = useAmbiente();
  if (opacidade <= 0.001) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: l,
        height: l,
        borderRadius: "50%",
        overflow: "hidden",
        opacity: opacidade,
        border: `5px solid ${tema.destaque}`,
        boxShadow: "0 18px 46px rgba(0,0,0,.45)",
        background: tema.fundo,
      }}
    >
      {partes.map((arq, p) => (
        <Sequence key={p} from={p * parte} durationInFrames={parte} layout="none">
          <OffthreadVideo src={staticFile(arq)} muted style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: `${px * 100}% ${py * 100}%` }} />
        </Sequence>
      ))}
    </div>
  );
};

// Legenda do que se ouve na fala editada, numa faixa; a palavra dita fica na cor de destaque.
export const LegendaFaixa: React.FC<{ frases: Frase[]; y: number; tamanho?: number; largura?: number }> = ({ frases, y, tamanho = 44, largura = 1240 }) => {
  const q = useCurrentFrame();
  const { tema } = useAmbiente();
  const f = frases.find((x) => q >= x.q0 && q < x.q1);
  if (!f) return null;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: y, display: "flex", justifyContent: "center" }}>
      <div
        style={{
          maxWidth: largura,
          padding: "12px 26px",
          borderRadius: 16,
          background: `${tema.fundo}d9`,
          color: tema.texto,
          fontFamily: pilha(tema.fonte_texto),
          fontSize: tamanho,
          fontWeight: 700,
          lineHeight: 1.18,
          textAlign: "center",
        }}
      >
        {f.palavras.map((p, i) => {
          const prox = f.palavras[i + 1];
          const atual = q >= p.q && (!prox || q < prox.q);
          return (
            <span key={i} style={{ color: atual ? tema.destaque : tema.texto }}>
              {p.w}
              {i < f.palavras.length - 1 ? " " : ""}
            </span>
          );
        })}
      </div>
    </div>
  );
};

const Pilula: React.FC<{ marca: string; texto: string; q: number; dur: number; centro?: boolean }> = ({ marca, texto, q, dur, centro }) => {
  const { fps } = useVideoConfig();
  const { tema } = useAmbiente();
  const ent = spring({ frame: q, fps, config: { damping: 15, stiffness: 150 } });
  const op = Math.min(interpolate(q, [dur - 10, dur], [1, 0], LIMITE), interpolate(q, [0, 6], [0, 1], LIMITE));
  const caixa = (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 18,
        padding: "14px 30px 14px 14px",
        background: `${tema.fundo}f0`,
        border: `1.5px solid ${tema.destaque}66`,
        borderRadius: 999,
        boxShadow: "0 18px 46px rgba(0,0,0,.35)",
        opacity: op,
        transform: centro ? `translateY(${(1 - ent) * -40}px)` : `translateX(${(1 - ent) * -80}px)`,
      }}
    >
      <div
        style={{
          width: 58,
          height: 58,
          borderRadius: "50%",
          background: tema.destaque,
          color: tema.fundo,
          display: "grid",
          placeItems: "center",
          fontFamily: pilha(tema.fonte_texto),
          fontWeight: 700,
          fontSize: 30,
        }}
      >
        {marca}
      </div>
      <div style={{ fontFamily: pilha(tema.fonte_texto), fontWeight: 700, fontSize: 38, color: tema.texto }}>{texto}</div>
    </div>
  );
  return centro ? (
    <div style={{ position: "absolute", left: 0, right: 0, top: 56, display: "flex", justifyContent: "center" }}>{caixa}</div>
  ) : (
    <div style={{ position: "absolute", left: 56, top: 50 }}>{caixa}</div>
  );
};

// Capítulo (no canto) e chamada (no alto, no centro), no molde das aulas.
export const Marcadores: React.FC<{ capitulos: { q: number; texto: string; n?: string }[]; chamadas: { q: number; dur?: number; texto: string }[] }> = ({
  capitulos,
  chamadas,
}) => {
  const q = useCurrentFrame();
  const cap = capitulos.find((c) => q >= c.q && q < c.q + 3.2 * FPS);
  const cham = chamadas.find((c) => q >= c.q && q < c.q + (c.dur ?? 3) * FPS);
  return (
    <>
      {cap ? <Pilula marca={cap.n || "✦"} texto={cap.texto} q={q - cap.q} dur={3.2 * FPS} /> : null}
      {cham ? <Pilula marca="!" texto={cham.texto} q={q - cham.q} dur={(cham.dur ?? 3) * FPS} centro /> : null}
    </>
  );
};

// Título por cima da tela nos primeiros segundos, com um painel que escurece o lado esquerdo.
export const Abertura: React.FC<{ a: { kicker?: string; titulo: string; sub?: string; ate: number } }> = ({ a }) => {
  const q = useCurrentFrame();
  const { tema } = useAmbiente();
  const fim = Math.round(a.ate * FPS);
  if (q >= fim) return null;
  const vis = Math.min(entra(q, 0, FPS, true), interpolate(q, [fim - 9, fim], [1, 0], LIMITE));
  return (
    <Sequence durationInFrames={fim} layout="none">
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 1150,
          height: 1080,
          background: `linear-gradient(90deg, ${tema.fundo}e6 0%, ${tema.fundo}99 55%, ${tema.fundo}00 100%)`,
          opacity: vis,
        }}
      />
      <div style={{ position: "absolute", left: 96, bottom: 180, width: 960, opacity: vis, display: "flex", flexDirection: "column" }}>
        <Kicker texto={a.kicker} />
        <Titulo texto={a.titulo} tamanho={112} />
        {a.sub ? <div style={{ marginTop: 18, fontFamily: pilha(tema.fonte_texto), fontSize: 46, color: tema.suave }}>{a.sub}</div> : null}
      </div>
    </Sequence>
  );
};

// O convite do fim, no visual do encerramento das aulas.
export const Encerramento: React.FC<{ convite: Convite }> = ({ convite }) => {
  const frame = useCurrentFrame();
  const { tema } = useAmbiente();
  const p = (t: number) => entra(frame, t, FPS);
  const linha = (t: number, filhos: React.ReactNode, estilo: React.CSSProperties) => (
    <div style={{ opacity: Math.min(1, p(t) * 1.4), transform: `translateY(${(1 - p(t)) * 24}px)`, ...estilo }}>{filhos}</div>
  );
  return (
    <AbsoluteFill style={{ opacity: interpolate(frame, [0, 8], [0, 1], LIMITE) }}>
      <Fundo />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", textAlign: "center", gap: 22, padding: 60 }}>
        {tema.logo ? linha(0, <Img src={staticFile(tema.logo)} style={{ height: 120, objectFit: "contain" }} />, {}) : null}
        {convite.titulo ? linha(0.1, convite.titulo, { fontFamily: pilha(tema.fonte_titulo), fontSize: 96, color: tema.texto, lineHeight: 1.05 }) : null}
        {convite.texto ? linha(0.5, convite.texto, { fontFamily: pilha(tema.fonte_texto), fontSize: 40, color: tema.suave }) : null}
        {convite.endereco
          ? linha(0.9, convite.endereco, {
              fontFamily: pilha(tema.fonte_texto),
              fontSize: 54,
              fontWeight: 700,
              color: tema.fundo,
              background: tema.destaque,
              padding: "12px 34px",
              borderRadius: 999,
            })
          : null}
        {linha(1.3, tema.marca, { fontFamily: pilha(tema.fonte_texto), fontSize: 26, color: tema.suave, marginTop: 30, letterSpacing: "0.12em", textTransform: "uppercase" })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Cena das aulas (capa, lista, colunas, fluxo, frase, número, imagem) por cima da voz da pessoa. Os itens entram nas
// palavras ditas, como nas aulas. Deitada, numa janela; no cartão do corte em pé, direto no fundo.
export const CenaDaGravacao: React.FC<{ cena: CenaGravada; formato: Formato; esc: number; janela?: Caixa; cabecalho: string; area: { w: number; h: number } }> = ({
  cena,
  formato,
  esc,
  janela,
  cabecalho,
  area,
}) => {
  const { tema } = useAmbiente();
  const duracao = (cena.q1 - cena.q0) / FPS;
  const ambiente = { tema, formato, esc, areaW: janela ? janela.w : area.w, areaH: janela ? janela.h : area.h };
  return (
    <Sequence from={cena.q0} durationInFrames={cena.q1 - cena.q0} layout="none">
      <Ctx.Provider value={ambiente}>
        {janela ? (
          <>
            {cena.rotulo ? <Rotulo texto={cena.rotulo} y={Math.max(20, janela.y - 64)} /> : null}
            <Janela {...janela} cabecalho={cabecalho}>
              <Cena tela={cena.tela} palavras={cena.palavras} duracao={duracao} />
            </Janela>
          </>
        ) : (
          <div style={{ position: "absolute", inset: 0 }}>
            <Cena tela={cena.tela} palavras={cena.palavras} duracao={duracao} />
          </div>
        )}
      </Ctx.Provider>
    </Sequence>
  );
};

// Opacidade da camada de cenas: aparece e some em 8 quadros só na troca com a tela (cenas vizinhas emendam sem piscar).
export const opacidadeDasCenas = (q: number, cenas: CenaGravada[], total: number) => {
  const c = cenas.find((x) => q >= x.q0 && q < x.q1);
  if (!c) return 0;
  const antes = cenas.some((o) => o.q1 === c.q0) || c.q0 === 0;
  const depois = cenas.some((o) => o.q0 === c.q1) || c.q1 >= total;
  const ent = antes ? 1 : interpolate(q - c.q0, [0, 8], [0, 1], LIMITE);
  const sai = depois ? 1 : interpolate(c.q1 - q, [0, 8], [0, 1], LIMITE);
  return Math.min(ent, sai);
};
