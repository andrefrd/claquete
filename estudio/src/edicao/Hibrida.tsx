import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Ctx } from "../pecas/contexto";
import { Fundo } from "../pecas/Moldura";
import { BOLHA_H } from "./Editada";
import { Bolinha, caixaDaTela, CenaDaGravacao, Encerramento, LegendaFaixa, Marcadores, opacidadeDasCenas, TelaGravada, TelaPronta } from "./pecas";
import type { Dados } from "./tipos";

// Versão híbrida: a fala da pessoa remontada numa ordem de raciocínio, a tela com o acabamento do Screen Studio (a
// exportação das fatias) ou, sem ela, desenhada pelo estúdio, e cenas das aulas por cima da voz, marcadas pelas palavras.
const JANELA = { x: 140, y: 120, w: 1440, h: 790 };

export const Hibrida: React.FC<{ dados: Dados | null; arquivo: string }> = ({ dados }) => {
  const q = useCurrentFrame();
  if (!dados) return null;
  const d = dados;
  const fim = q >= d.quadros;
  const opCena = fim ? 1 : opacidadeDasCenas(q, d.cenas, d.quadros);
  const cena = d.cenas.find((c) => q >= c.q0 && q < c.q1);
  const bolhaTela = d.tela ? d.tela.quadros[Math.min(q, d.tela.quadros.length - 1)][9] : 0;
  const bolha = d.bolhaSempre ? Math.max(bolhaTela, opCena) : opCena;
  return (
    <Ctx.Provider value={{ tema: d.tema, formato: "h", esc: 1, areaW: 1920, areaH: 1080 }}>
      <AbsoluteFill style={{ backgroundColor: d.tema.fundo }}>
        {opCena < 1 && d.telaPronta ? <TelaPronta partes={d.telaPronta.partes} parte={d.parte} /> : null}
        {opCena < 1 && d.tela ? (
          <>
            <Fundo />
            <TelaGravada tela={d.tela} parte={d.parte} caixa={caixaDaTela(d.tela.largura, d.tela.altura)} />
          </>
        ) : null}
        {opCena > 0 && !fim ? (
          <AbsoluteFill style={{ opacity: opCena }}>
            <Fundo />
            {d.cenas.map((c, i) => (
              <CenaDaGravacao key={i} cena={c} formato="h" esc={1} janela={JANELA} cabecalho={d.cabecalho} area={{ w: 1920, h: 1080 }} />
            ))}
          </AbsoluteFill>
        ) : null}
        {d.camera && !fim ? <Bolinha partes={d.camera.partes} px={d.camera.x} py={d.camera.y} parte={d.parte} {...BOLHA_H} opacidade={bolha} /> : null}
        {!cena && !fim ? <Marcadores capitulos={d.capitulos} chamadas={d.chamadas} /> : null}
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
