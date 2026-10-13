import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Ctx } from "../pecas/contexto";
import { Fundo } from "../pecas/Moldura";
import { Abertura, Bolinha, caixaDaTela, Encerramento, LegendaFaixa, Marcadores, TelaGravada } from "./pecas";
import type { Dados } from "./tipos";

// Versão editada: a gravação na ordem em que foi feita, sem as muletas, as repetições e as esperas, com a tela desenhada
// pelo estúdio sobre o fundo da marca, a câmera na bolinha e a legenda do que se ouve.
export const BOLHA_H = { x: 1620, y: 770, l: 260 };

export const Editada: React.FC<{ dados: Dados | null; arquivo: string }> = ({ dados }) => {
  const q = useCurrentFrame();
  if (!dados || !dados.tela) return null;
  const d = dados;
  const tela = dados.tela;
  const fim = q >= d.quadros;
  const linha = tela.quadros[Math.min(q, tela.quadros.length - 1)];
  return (
    <Ctx.Provider value={{ tema: d.tema, formato: "h", esc: 1, areaW: 1920, areaH: 1080 }}>
      <AbsoluteFill style={{ backgroundColor: d.tema.fundo }}>
        <Fundo />
        {!fim ? <TelaGravada tela={tela} parte={d.parte} caixa={caixaDaTela(tela.largura, tela.altura)} /> : null}
        {d.camera && !fim ? <Bolinha partes={d.camera.partes} px={d.camera.x} py={d.camera.y} parte={d.parte} {...BOLHA_H} opacidade={linha[9]} /> : null}
        {d.abertura ? <Abertura a={d.abertura} /> : null}
        {!fim ? <Marcadores capitulos={d.capitulos} chamadas={d.chamadas} /> : null}
        {!fim ? <LegendaFaixa frases={d.legendas} y={952} /> : null}
        {d.convite ? (
          <Sequence from={d.quadros}>
            <Encerramento convite={d.convite} />
          </Sequence>
        ) : null}
      </AbsoluteFill>
    </Ctx.Provider>
  );
};
