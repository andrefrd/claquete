// O que o scripts/gravacao.py escreve em dados.json (ou dados-<corte>.json) para cada versão da gravação editada.
import type { Tela, Tema } from "../tipos";

// por quadro: [escala, centroX, centroY, cursorX, cursorY, cursor, cursorVisível, segundoDaTela, aceleração, bolinha]
export type Quadro = [number, number, number, number, number, string, number, number, number, number];

export type CamadaTela = {
  partes: string[]; // um vídeo por parte do render, já na ordem e na velocidade da linha do tempo
  quadros: Quadro[];
  cliques: { q: number; x: number; y: number }[];
  mascaras: { de: number; ate: number; cor?: string; retangulos: [number, number, number, number][] }[];
  cursores: Record<string, { hx: number; hy: number; w: number; h: number }>;
  largura: number;
  altura: number;
};

export type PalavraDita = { w: string; q: number };
export type Frase = { q0: number; q1: number; palavras: PalavraDita[] };
export type CenaGravada = { q0: number; q1: number; tela: Tela; rotulo?: string; palavras: { p: string; ini: number; fim: number }[] };
export type Convite = { titulo: string; texto: string; endereco: string };

export type Dados = {
  versao: "editada" | "hibrida" | "reel";
  quadros: number;
  parte: number;
  tema: Tema;
  cabecalho: string;
  convite: Convite | null;
  encerramento: number; // segundos depois da fala
  tela: CamadaTela | null; // a tela desenhada pelo estúdio (editada, híbrida sem exportação, corte em pé)
  telaPronta: { partes: string[] } | null; // a exportação do Screen Studio (híbrida)
  camera: { partes: string[]; x: number; y: number } | null;
  legendas: Frase[];
  blocos?: Frase[]; // corte em pé: legenda de até 3 palavras
  cenas: CenaGravada[];
  chamadas: { q: number; dur?: number; texto: string }[];
  capitulos: { q: number; texto: string; n?: string }[];
  abertura: { kicker?: string; titulo: string; sub?: string; ate: number } | null;
  bolhaSempre: boolean;
  gancho?: string;
  titulo?: string;
};
