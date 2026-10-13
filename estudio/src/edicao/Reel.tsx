import React from "react";
import { AbsoluteFill, Img, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { pilha } from "../fontes";
import { Ctx } from "../pecas/contexto";
import { Fundo } from "../pecas/Moldura";
import { FPS } from "../tempo";
import { Bolinha, CenaDaGravacao, comDestaque, Encerramento, LIMITE, TelaGravada } from "./pecas";
import type { Dados } from "./tipos";

// Corte em pé (Reels, TikTok, Shorts): o gancho nos 2 primeiros segundos, depois o título; a tela no cartão do meio, com
// zoom mais fechado, ou a cena em pé; legenda palavra a palavra na borda do cartão; a bolinha no alto; o convite no fim.
const W = 1080;
const CARTAO = { x: 0, y: 400, w: 1080, h: 1040 };
const BOLHA = { x: 800, y: 96, l: 240 };
const GANCHO = 2.6 * FPS;
const ESC_CARTAO = 1.15; // texto das cenas maior no cartão: o corte em pé se vê no celular

export const Reel: React.FC<{ dados: Dados | null; arquivo: string }> = ({ dados }) => {
  const r = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!dados) return null;
  const d = dados;
  const { tema } = d;
  const total = d.quadros + Math.round(d.encerramento * FPS);
  const noConvite = r >= d.quadros;
  const cena = d.cenas.find((c) => r >= c.q0 && r < c.q1);
  const bloco = (d.blocos ?? []).find((b) => r >= b.q0 && r < b.q1);
  const linha = d.tela ? d.tela.quadros[Math.min(r, d.tela.quadros.length - 1)] : null;
  // o gancho sai antes de o título entrar: no mesmo lugar, os dois juntos embaralham
  const gancho = interpolate(r, [0, GANCHO - 8, GANCHO - 2], [1, 1, 0], LIMITE);
  const ganchoEntra = spring({ frame: r, fps, config: { damping: 14, stiffness: 160 } });
  const depois = interpolate(r, [GANCHO, GANCHO + 8], [0, 1], LIMITE);
  const limpa = (w: string) => w.replace(/[.,:;!?]+$/, "");
  return (
    <Ctx.Provider value={{ tema, formato: "v", esc: ESC_CARTAO, areaW: CARTAO.w, areaH: CARTAO.h }}>
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, ${tema.destaque}33 0%, ${tema.fundo}00 55%), ${tema.fundo}` }}>
        <div style={{ position: "absolute", left: CARTAO.x, top: CARTAO.y, width: CARTAO.w, height: CARTAO.h, overflow: "hidden", background: tema.fundo2 }}>
          {d.tela && !noConvite ? <TelaGravada tela={d.tela} parte={d.parte} caixa={{ x: 0, y: 0, w: CARTAO.w, h: CARTAO.h }} cartao /> : null}
          {cena && !noConvite ? (
            <AbsoluteFill>
              <Fundo />
              <CenaDaGravacao cena={cena} formato="v" esc={ESC_CARTAO} cabecalho="" area={{ w: CARTAO.w, h: CARTAO.h }} />
            </AbsoluteFill>
          ) : null}
          <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 6, background: tema.destaque }} />
          <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 6, background: tema.destaque }} />
        </div>

        {d.camera && !noConvite ? (
          <Bolinha partes={d.camera.partes} px={d.camera.x} py={d.camera.y} parte={d.parte} {...BOLHA} opacidade={linha ? Math.max(0.0, linha[9]) : 1} />
        ) : null}

        {gancho > 0 ? (
          <div style={{ position: "absolute", left: 50, width: 720, top: 110, opacity: gancho, transform: `scale(${0.92 + 0.08 * ganchoEntra})`, transformOrigin: "0 0" }}>
            <div style={{ fontFamily: pilha(tema.fonte_titulo), fontWeight: 700, fontSize: 76, lineHeight: 1.04, color: tema.texto }}>{comDestaque(d.gancho ?? "", tema.destaque)}</div>
          </div>
        ) : null}
        {d.titulo && !noConvite ? (
          <div style={{ position: "absolute", left: 50, width: 720, top: 200, opacity: depois }}>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 14,
                padding: "14px 26px",
                borderRadius: 999,
                background: `${tema.fundo}d9`,
                border: `2px solid ${tema.destaque}`,
              }}
            >
              {tema.logo ? <Img src={staticFile(tema.logo)} style={{ height: 40 }} /> : null}
              <div style={{ fontFamily: pilha(tema.fonte_texto), fontWeight: 700, fontSize: 38, color: tema.texto }}>{d.titulo}</div>
            </div>
          </div>
        ) : null}

        {bloco && !noConvite ? (
          <div style={{ position: "absolute", left: 50, right: 50, top: CARTAO.y + CARTAO.h, transform: "translateY(-50%)", textAlign: "center" }}>
            <div
              style={{
                display: "inline-flex",
                flexWrap: "wrap",
                justifyContent: "center",
                columnGap: 6,
                rowGap: 6,
                fontFamily: pilha(tema.fonte_texto),
                fontWeight: 700,
                fontSize: 84,
                lineHeight: 1.05,
                textTransform: "uppercase",
                transform: `scale(${interpolate(r, [bloco.q0, bloco.q0 + 4], [0.84, 1], LIMITE)})`,
              }}
            >
              {bloco.palavras.map((p, k) => {
                const ativa = r >= p.q && r < (bloco.palavras[k + 1]?.q ?? bloco.q1);
                return (
                  <span
                    key={k}
                    style={{
                      display: "inline-block",
                      padding: "2px 14px 0",
                      borderRadius: 16,
                      backgroundColor: ativa ? tema.destaque : "transparent",
                      color: ativa ? tema.fundo : tema.texto,
                      WebkitTextStroke: ativa ? "0px transparent" : `12px ${tema.fundo}`,
                      paintOrder: "stroke fill",
                      textShadow: ativa ? "none" : "0 6px 18px rgba(0,0,0,0.55)",
                    }}
                  >
                    {limpa(p.w)}
                  </span>
                );
              })}
            </div>
          </div>
        ) : null}

        {!noConvite ? (
          <div style={{ position: "absolute", left: 0, top: 1600, width: W, display: "flex", alignItems: "center", justifyContent: "center", gap: 16 }}>
            {tema.logo ? <Img src={staticFile(tema.logo)} style={{ height: 46 }} /> : null}
            <div style={{ fontFamily: pilha(tema.fonte_texto), fontWeight: 700, fontSize: 40, color: tema.texto }}>{tema.marca}</div>
          </div>
        ) : null}

        {d.convite ? (
          <Sequence from={d.quadros}>
            <Encerramento convite={d.convite} />
          </Sequence>
        ) : null}

        <div style={{ position: "absolute", left: 0, top: 0, height: 10, width: `${(r / total) * 100}%`, background: tema.destaque }} />
      </AbsoluteFill>
    </Ctx.Provider>
  );
};
