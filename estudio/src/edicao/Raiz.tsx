import React from "react";
import { Composition, staticFile } from "remotion";
import "../fontes";
import { Editada } from "./Editada";
import { Hibrida } from "./Hibrida";
import { Reel } from "./Reel";
import type { Dados } from "./tipos";

// Entrada própria das gravações editadas (scripts/gravacao.py). Os dados e a mídia ficam na pasta pública da versão,
// passada no bundle com --public-dir; cada composição lê o arquivo de dados que vier em "arquivo".
const carregar = async (arquivo: string): Promise<Dados> => (await fetch(staticFile(arquivo))).json();
const duracao = (d: Dados) => d.quadros + Math.round(d.encerramento * 30);
const padrao = { dados: null as Dados | null, arquivo: "dados.json" };

export const Raiz: React.FC = () => (
  <>
    <Composition
      id="Editada"
      component={Editada}
      fps={30}
      width={1920}
      height={1080}
      durationInFrames={30}
      defaultProps={padrao}
      calculateMetadata={async ({ props }) => {
        const dados = await carregar(props.arquivo);
        return { durationInFrames: duracao(dados), props: { ...props, dados } };
      }}
    />
    <Composition
      id="Hibrida"
      component={Hibrida}
      fps={30}
      width={1920}
      height={1080}
      durationInFrames={30}
      defaultProps={padrao}
      calculateMetadata={async ({ props }) => {
        const dados = await carregar(props.arquivo);
        return { durationInFrames: duracao(dados), props: { ...props, dados } };
      }}
    />
    <Composition
      id="Reel"
      component={Reel}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={30}
      defaultProps={padrao}
      calculateMetadata={async ({ props }) => {
        const dados = await carregar(props.arquivo);
        return { durationInFrames: duracao(dados), props: { ...props, dados } };
      }}
    />
  </>
);
