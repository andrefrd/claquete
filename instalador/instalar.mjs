#!/usr/bin/env node
// Instalador da Claquete.ai. Deixa tudo pronto para o Claude fazer vídeos com a sua marca:
//   1. as skills (as da Claquete e as de motion design da iart.ai, MIT)
//   2. o estúdio (projeto Remotion), novo ou atualizado sem perder o que é seu
//   3. as ferramentas da máquina: ffmpeg, Python 3, os navegadores do Remotion e do Playwright, o app das telas
//      animadas (cenas/) com os componentes do React Bits baixados do site oficial para a sua máquina e, se quiser, a
//      transcrição local e gratuita para a revisão da fala e a edição de gravações (faster-whisper)
//   4. a chave da ElevenLabs num .env só seu, e a voz pronta na sua conta (e, se tiver, a licença do React Bits Pro)
//   5. a sua marca: um questionário (nome, público, cores, fontes, logo, tom, chamada, voz) e o material que você
//      tiver (pasta, HTML, .md ou link), para o Claude ler depois
//   6. um teste final
//
//   npx github:dantaspaulo/claquete                 interativo
//   npx github:dantaspaulo/claquete --tudo          tudo, sem perguntas (usa a chave do ambiente, se houver; --sim é igual)
//   ... --idioma pt-BR | en-US                      o idioma dos vídeos e das mensagens (--lang é igual; padrão: pt-BR)
//   ... --atualizar                                 atualiza skills e estúdio, mantendo marca, aulas, .env e configuração
//   ... --projeto | --global                        skills em ./.claude/skills ou em ~/.claude/skills
//   ... --skills claquete,aula-animada              só estas
//   ... --estudio ./meu-estudio                     o estúdio nessa pasta
//   ... --sem-ferramentas | --sem-motion | --sem-marca | --sem-cenas | --sem-reactbits | --transcricao-local
//   ... --desinstalar                               remove as skills (o estúdio fica)
//   ... --versao | --ajuda
//en 1. Claquete and motion design skills (iart.ai, MIT)
//en 2. The studio (Remotion project), new or updated without losing your work
//en 3. Machine tools: ffmpeg, Python 3, Remotion and Playwright browsers, animated screens
//en    (cenas/) with React Bits components downloaded from the official site and optional
//en    free local transcription for narration review and recording edits (faster-whisper)
//en 4. Your ElevenLabs key in a private .env and a voice ready in your account (optional React Bits Pro license)
//en 5. Your brand: a questionnaire (name, audience, colors, fonts, logo, tone, call to action, voice)
//en    and your materials (folder, HTML, .md or link) for Claude to read later
//en 6. A final test
//en npx github:dantaspaulo/claquete                 interactive
//en npx github:dantaspaulo/claquete --tudo          everything, no questions (uses the environment key if set; --sim works too)
//en ... --idioma pt-BR | en-US                      video and message language (--lang works too; default: pt-BR)
//en ... --atualizar                                 update skills and studio while keeping brand, lessons, .env and configuration
//en ... --projeto | --global                        skills in ./.claude/skills or ~/.claude/skills
//en ... --skills claquete,aula-animada              only these
//en ... --estudio ./meu-estudio                     studio in this folder
//en ... --sem-ferramentas | --sem-motion | --sem-marca | --sem-cenas | --sem-reactbits | --transcricao-local
//en ... --desinstalar                               remove skills (the studio stays)
//en ... --versao | --ajuda
//
// As flags em inglês valem como alias das portuguesas: --all, --yes, --update, --project, --studio, --no-tools,
// --no-motion, --no-brand, --no-scenes, --no-reactbits, --local-transcription, --uninstall, --version.
//
// Com --atualizar, junte --idioma para trocar o idioma de um estúdio que já existe (sem isso, a escolha da
// pessoa fica como está).
//
// Só Node 18+. Instalar não apaga nada: skill que já existe vira cópia de segurança.
import { chmodSync, copyFileSync, cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from "node:fs";
import { homedir, platform, tmpdir } from "node:os";
import { basename, dirname, extname, join, resolve, sep } from "node:path";
import { createInterface } from "node:readline/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const VERSAO = JSON.parse(readFileSync(join(RAIZ, "package.json"), "utf8")).version;
// As skills existem em português (padrão) e em inglês. Os NOMES das pastas são iguais nos dois: é por
// eles que o --desinstalar remove e que a skill de entrada chama as outras.
const pastaSkills = (idioma) => join(RAIZ, idioma === "en-US" ? "skills-en" : "skills");
const PASTA_ESTUDIO = join(RAIZ, "estudio");
const MOTION = { repo: "iart-ai/motion-design-skills", tar: "https://codeload.github.com/iart-ai/motion-design-skills/tar.gz/refs/heads/main" };
const HAIRLINE = { repo: "lucasmarkes/hairline", skill: "hairline-create" };
const SO = platform(); // darwin | linux | win32
const args = process.argv.slice(2);
const valor = (f) => {
  const i = args.indexOf(f);
  return i >= 0 ? args[i + 1] : undefined;
};

// As flags em inglês são aliases das portuguesas, que continuam funcionando: renomear quebraria todo
// comando já escrito por aí (README, skills e o que a pessoa decorou). `--idioma` é a única nova.
const SINONIMOS = {
  "--all": "--tudo", "--yes": "--sim", "--update": "--atualizar", "--project": "--projeto", "--studio": "--estudio",
  "--no-tools": "--sem-ferramentas", "--no-motion": "--sem-motion", "--no-brand": "--sem-marca", "--no-scenes": "--sem-cenas",
  "--no-reactbits": "--sem-reactbits", "--local-transcription": "--transcricao-local", "--uninstall": "--desinstalar",
  "--version": "--versao", "--lang": "--idioma",
};
for (let i = 0; i < args.length; i++) args[i] = SINONIMOS[args[i]] || args[i];
const tem = (f) => args.includes(f);

// Flag desconhecida (ou --help) mostra o uso e para: sem isso, "--help" rodava a instalação inteira.
const FLAGS = ["--tudo", "--sim", "--atualizar", "--projeto", "--global", "--skills", "--estudio", "--idioma", "--sem-ferramentas", "--sem-motion",
  "--sem-marca", "--sem-cenas", "--sem-reactbits", "--transcricao-local", "--desinstalar", "--versao", "--ajuda", "--help", "-h"];
const COM_VALOR = ["--skills", "--estudio", "--idioma"];
const ajudaEn = valor("--idioma") ? /^en(?:-|_|$)/i.test(valor("--idioma")) : /^en/i.test(process.env.LC_ALL || "") || /^en/i.test(process.env.LANG || "");
const uso = () => readFileSync(fileURLToPath(import.meta.url), "utf8").split("\n").filter((l) => l.startsWith(ajudaEn ? "//en " : "//   ")).map((l) => l.slice(5)).join("\n");
for (let i = 0; i < args.length; i++) {
  if (COM_VALOR.includes(args[i])) {
    if (!args[i + 1] || args[i + 1].startsWith("--")) {
      console.error(`${args[i]} ${ajudaEn ? "requires a value" : "pede um valor"}.\n\n${uso()}`);
      process.exit(1);
    }
    i++;
  } else if (!FLAGS.includes(args[i])) {
    console.error(`${ajudaEn ? "Unknown option" : "Opção desconhecida"}: ${args[i]}\n\n${uso()}`);
    process.exit(1);
  }
}
if (tem("--ajuda") || tem("--help") || tem("-h")) {
  console.log(`Claquete.ai ${VERSAO}\n\n${uso()}`);
  process.exit(0);
}

const cor = (c, t) => (process.stdout.isTTY ? `\x1b[${c}m${t}\x1b[0m` : t);
const verde = (t) => cor("32", t);
const fraco = (t) => cor("2", t);
const negrito = (t) => cor("1", t);
const ok = (t) => console.log(`  ${verde("✓")} ${t}`);
const nao = (t) => console.log(`  · ${t}`);
const titulo = (t) => console.log(`\n${negrito(t)}`);
// As mensagens nos dois idiomas. O pt-BR é o texto de sempre; o idioma vem da primeira pergunta.
let IDIOMA = "pt-BR";
const T = (pt, en) => (IDIOMA === "en-US" ? en : pt);

function roda(cmd, cwd, mostrar = true) {
  const r = spawnSync(cmd, { cwd, shell: true, stdio: mostrar ? "inherit" : "pipe" });
  return r.status === 0;
}
const existe = (cmd) => spawnSync(SO === "win32" ? `where ${cmd}` : `command -v ${cmd}`, { shell: true, stdio: "pipe" }).status === 0;

function lerSkills(pasta) {
  return readdirSync(pasta, { withFileTypes: true })
    .filter((d) => d.isDirectory() && existsSync(join(pasta, d.name, "SKILL.md")))
    .map((d) => {
      const md = readFileSync(join(pasta, d.name, "SKILL.md"), "utf8");
      const resumo = (md.match(/^\s+resumo:\s*(.+)$/m) || [, ""])[1];
      return { nome: d.name, resumo };
    });
}

function copiarPasta(origem, alvo) {
  if (existsSync(alvo)) {
    const copia = `${alvo}.bak-${new Date().toISOString().replace(/[:.]/g, "-")}`;
    renameSync(alvo, copia);
    console.log(fraco(T(`    já existia: a anterior ficou em ${copia}`, `    already existed: the previous copy is at ${copia}`)));
  }
  cpSync(origem, alvo, { recursive: true });
}

// As skills de motion design da iart.ai (MIT): baixa o repositório e copia cada skill, com a licença junto.
function instalarMotion(destino) {
  if (!existe("curl") || !existe("tar")) {
    nao(T(`motion design: preciso de curl e tar para baixar ${MOTION.repo}; instale à mão: npx skills add ${MOTION.repo}`, `motion design: curl and tar are needed to download ${MOTION.repo}; install manually: npx skills add ${MOTION.repo}`));
    return [];
  }
  const tmp = mkdtempSync(join(tmpdir(), "claquete-motion-"));
  if (!roda(`curl -sL ${MOTION.tar} | tar xz -C "${tmp}"`, undefined, false)) {
    nao(T(`motion design: não consegui baixar ${MOTION.repo} (sem internet?). Depois: npx github:dantaspaulo/claquete --atualizar`, `motion design: could not download ${MOTION.repo} (offline?). Later: npx github:dantaspaulo/claquete --atualizar`));
    return [];
  }
  const raiz = join(tmp, readdirSync(tmp)[0]);
  const licenca = join(raiz, "LICENSE");
  const nomes = readdirSync(join(raiz, "skills"), { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name);
  for (const n of nomes) {
    copiarPasta(join(raiz, "skills", n), join(destino, n));
    if (existsSync(licenca)) copyFileSync(licenca, join(destino, n, "LICENSE-iart.txt"));
  }
  rmSync(tmp, { recursive: true, force: true });
  return nomes;
}

// A skill de figuras isométricas do @lucasmarkes/hairline (MIT): uma skill só, então vem pelo "npx skills",
// que também põe o symlink do Claude Code. Sem o npx, a mensagem diz o comando.
function instalarHairline(destino) {
  if (!existe("npx")) {
    nao(T(`hairline: preciso do npx; instale à mão: npx skills add ${HAIRLINE.repo} --skill ${HAIRLINE.skill}`, `hairline: npx is needed; install manually: npx skills add ${HAIRLINE.repo} --skill ${HAIRLINE.skill}`));
    return [];
  }
  const escopo = destino === global ? "--global" : "";
  if (!roda(`npx -y skills add ${HAIRLINE.repo} --skill ${HAIRLINE.skill} -y ${escopo}`.trim(), undefined, false)) {
    nao(T(`hairline: não consegui instalar ${HAIRLINE.repo} (sem internet?). Depois: npx skills add ${HAIRLINE.repo} --skill ${HAIRLINE.skill}`, `hairline: could not install ${HAIRLINE.repo} (offline?). Later: npx skills add ${HAIRLINE.repo} --skill ${HAIRLINE.skill}`));
    return [];
  }
  return [HAIRLINE.skill];
}

// ── React Bits nas telas animadas ───────────────────────────────────────────
// A licença do React Bits (MIT + Commons Clause) não deixa redistribuir os componentes: eles NÃO estão neste
// repositório. O instalador baixa cada um do registro oficial direto para a máquina de quem instala, como o
// "npx shadcn add" faria, e instala as dependências deles. O teste do estúdio recusa componente do React Bits versionado.
const RB_GRATIS = ["SplitText", "BlurText", "ShinyText", "GradientText", "RotatingText", "TextType", "CountUp", "AnimatedList", "Orb", "Aurora", "Beams", "Particles"];
const RB_PRO = ["staggered-text", "agentic-ball", "speeding-text", "animated-list", "magic-transform", "globe"];
const GLOBE_GL = "https://cdn.jsdelivr.net/npm/globe.gl@2.46.2/dist/globe.gl.min.js";

// Ajuste para vídeo, só na cópia da pessoa: o canvas do React Three Fiber mede pelo tamanho de layout, não pelo retângulo
// transformado (a câmera da cena dá zoom e as peças entram com escala; sem isto o desenho nasce do tamanho errado).
const ajustarParaVideo = (codigo) => codigo.replace(/<Canvas\b(?![^>]*resize=)/g, "<Canvas resize={{ offsetSize: true }}");

async function baixarReactBits(cenas, chavePro) {
  const destino = join(cenas, "src", "components", "react-bits");
  mkdirSync(destino, { recursive: true });
  const itens = [
    ...RB_GRATIS.map((n) => ({ nome: n, url: `https://reactbits.dev/r/${n}-TS-TW.json` })),
    ...(chavePro ? RB_PRO.map((n) => ({ nome: n, url: `https://pro.reactbits.dev/api/r/starter/${n}-tw.json`, pro: true })) : []),
  ];
  const deps = new Set(), baixados = [], falhas = [];
  for (const it of itens) {
    try {
      const r = await fetch(it.url, { headers: it.pro ? { Authorization: `Bearer ${chavePro}` } : {} });
      if (!r.ok) {
        falhas.push(`${it.nome} (${r.status === 401 || r.status === 403 ? T("licença recusada", "license rejected") : r.status})`);
        continue;
      }
      const item = await r.json();
      for (const f of item.files || []) writeFileSync(join(destino, basename(f.path)), ajustarParaVideo(f.content));
      for (const d of item.dependencies || []) deps.add(d);
      baixados.push(it.nome);
    } catch (e) {
      falhas.push(`${it.nome} (${e.message})`);
    }
  }
  if (baixados.includes("globe")) {
    try {
      const r = await fetch(GLOBE_GL);
      if (r.ok) {
        mkdirSync(join(cenas, "public", "vendor"), { recursive: true });
        writeFileSync(join(cenas, "public", "vendor", "globe.gl.min.js"), Buffer.from(await r.arrayBuffer()));
      } else falhas.push(`globe.gl (${r.status})`);
    } catch (e) {
      falhas.push(`globe.gl (${e.message})`);
    }
  }
  const instalou = !deps.size || roda(`npm install --no-audit --no-fund ${[...deps].map((d) => `"${d}"`).join(" ")}`, cenas, false);
  return { baixados, falhas, instalou };
}

function perguntarSegredo(q) {
  if (!process.stdin.isTTY) return Promise.resolve("");
  process.stdout.write(q);
  return new Promise((res) => {
    let v = "";
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.setEncoding("utf8");
    const fim = () => {
      process.stdin.setRawMode(false);
      process.stdin.pause();
      process.stdin.off("data", ao);
      process.stdout.write("\n");
      res(v.trim());
    };
    const ao = (bloco) => {
      for (const ch of bloco) {
        if (ch === "\r" || ch === "\n" || ch === "\u0004") return fim();
        if (ch === "\u0003") process.exit(130);
        if (ch === "\u007f" || ch === "\b") v = v.slice(0, -1);
        else {
          v += ch;
          process.stdout.write("•");
        }
      }
    };
    process.stdin.on("data", ao);
  });
}

function comandoPython() {
  for (const c of ["python3", "python", "py -3"]) {
    const r = spawnSync(`${c} --version`, { shell: true, stdio: "pipe" });
    if (r.status === 0 && /Python 3/.test(`${r.stdout}${r.stderr}`)) return c;
  }
  return null;
}

function instaladorDoSistema(pacote) {
  const nomes = {
    ffmpeg: { brew: "ffmpeg", apt: "ffmpeg", dnf: "ffmpeg", winget: "Gyan.FFmpeg" },
    python: { brew: "python", apt: "python3", dnf: "python3", winget: "Python.Python.3.12" },
  }[pacote];
  if (SO === "darwin" && existe("brew")) return `brew install ${nomes.brew}`;
  if (SO === "linux" && existe("apt-get")) return `sudo apt-get update && sudo apt-get install -y ${nomes.apt}`;
  if (SO === "linux" && existe("dnf")) return `sudo dnf install -y ${nomes.dnf}`;
  if (SO === "win32" && existe("winget")) return `winget install -e --id ${nomes.winget}`;
  return null;
}

// Atualiza o estúdio sem tocar no que é da pessoa: roteiros, gravações, marca, saída, chaves e a configuração dela
// (que só ganha as chaves novas que não tinha).
const DA_PESSOA = ["aulas", "edicoes", join("public", "aulas"), join("public", "gravacoes"), join("public", "marca"), "marca", "saida", ".env", "kit.config.json", "node_modules",
  join("cenas", "node_modules"), join("cenas", "dist"), join("cenas", "src", "aulas"), join("cenas", "src", "components", "react-bits"), join("cenas", "public", "vendor")];
// nunca saem do repositório para o estúdio de ninguém (são da máquina de quem desenvolve ou baixados na hora)
const NAO_COPIAR = ["node_modules", "saida", ".venv", join("public", "aulas"), join("public", "gravacoes"), join("cenas", "node_modules"), join("cenas", "dist"),
  join("cenas", "src", "components", "react-bits"), join("cenas", "public", "vendor")];
function atualizarEstudio(estudio) {
  const pula = [...new Set([...DA_PESSOA, ...NAO_COPIAR])].map((x) => join(PASTA_ESTUDIO, x));
  cpSync(PASTA_ESTUDIO, estudio, { recursive: true, filter: (f) => !pula.some((x) => f === x || f.startsWith(x + sep)) });
  for (const ex of ["exemplo.json", "tutorial-exemplo.json", "animada-exemplo.json"]) {
    if (!existsSync(join(estudio, "aulas", ex))) cpSync(join(PASTA_ESTUDIO, "aulas", ex), join(estudio, "aulas", ex));
  }
  const cenaExemplo = join("cenas", "src", "aulas", "animada-exemplo.jsx");
  if (!existsSync(join(estudio, cenaExemplo))) {
    mkdirSync(dirname(join(estudio, cenaExemplo)), { recursive: true });
    cpSync(join(PASTA_ESTUDIO, cenaExemplo), join(estudio, cenaExemplo));
  }
  const arq = join(estudio, "kit.config.json");
  const novo = JSON.parse(readFileSync(join(PASTA_ESTUDIO, "kit.config.json"), "utf8"));
  const atual = existsSync(arq) ? JSON.parse(readFileSync(arq, "utf8")) : {};
  const mesclar = (base, meu) => {
    const out = { ...meu };
    for (const [k, v] of Object.entries(base)) {
      if (!(k in out)) out[k] = v;
      else if (v && typeof v === "object" && !Array.isArray(v) && out[k] && typeof out[k] === "object") out[k] = mesclar(v, out[k]);
    }
    return out;
  };
  const mesclado = mesclar(novo, atual);
  if (mesclado.voz) delete mesclado.voz.openai; // a 2.0 tirou a OpenAI do estúdio
  writeFileSync(arq, JSON.stringify(mesclado, null, 2) + "\n");
}

// ── o questionário da marca ─────────────────────────────────────────────────
async function questionarioMarca(perguntar, estudio) {
  const escolha = async (q, opcoes, padrao = 1, rotulos) => {
    opcoes.forEach((o, i) => console.log(`    ${i + 1}) ${IDIOMA === "en-US" ? (rotulos?.[i] ?? o) : o}`));
    const r = Number(await perguntar(`  ${q}`, String(padrao)));
    return opcoes[(r >= 1 && r <= opcoes.length ? r : padrao) - 1];
  };
  const lista = (t) => t.split(",").map((x) => x.trim()).filter(Boolean);
  const hex = (t, padrao) => (/^#?[0-9a-f]{6}$/i.test(t) ? (t.startsWith("#") ? t : `#${t}`) : padrao);
  console.log(fraco(T("  Enter aceita o que está entre colchetes. Tudo pode mudar depois: peça ao Claude \"refaz a minha marca\".", "  Press Enter to accept the value in brackets. You can change it later: ask Claude \"redo my brand\".")));
  const m = { versao_questionario: 1 };
  m.nome = await perguntar(T("  Nome da marca", "  Brand name"), T("Minha marca", "My brand"));
  m.o_que_faz = await perguntar(T("  O que ela faz, em uma linha", "  What it does, in one line"), "");
  m.publico = await perguntar(T("  Para quem são os vídeos (público)", "  Who the videos are for (audience)"), "");
  m.site = await perguntar(T("  Site", "  Website"), "");
  m.instagram = await perguntar(T("  Instagram (@)", "  Instagram (@)"), "");
  m.tiktok = await perguntar(T("  TikTok (@)", "  TikTok (@)"), "");

  titulo(T("  Material da marca", "  Brand material"));
  console.log(fraco(T("  Uma pasta (logos, fontes, manual, posts de exemplo), um arquivo HTML ou .md com o padrão da marca, ou um link.", "  A folder (logos, fonts, guidelines, example posts), an HTML or .md brand guide, or a link.")));
  console.log(fraco(T("  O Claude lê tudo depois e monta a marca com mais precisão. Pode dar vários, separados por vírgula.", "  Claude will read it later to build your brand more accurately. Separate multiple items with commas.")));
  const material = lista(await perguntar(T("  Caminho(s) ou link(s)", "  Path(s) or link(s)"), ""));
  const destMaterial = join(estudio, "marca", "material");
  m.material = [];
  for (const item of material) {
    if (/^https?:\/\//i.test(item)) {
      m.material.push({ link: item });
      ok(T(`link guardado: ${item}`, `link saved: ${item}`));
      continue;
    }
    const caminho = resolve(item.replace(/^~(?=$|\/)/, homedir()));
    if (!existsSync(caminho)) {
      nao(T(`não achei ${caminho}: ficou de fora`, `not found: ${caminho}; skipped`));
      continue;
    }
    mkdirSync(destMaterial, { recursive: true });
    const alvo = join(destMaterial, basename(caminho));
    cpSync(caminho, alvo, { recursive: true });
    m.material.push({ arquivo: join("marca", "material", basename(caminho)) });
    ok(T(`copiado para marca/material/${basename(caminho)}`, `copied to marca/material/${basename(caminho)}`));
  }
  m.design_system = await perguntar(T("  Design system (caminho ou link; enter se não tiver)", "  Design system (path or link; press Enter if none)"), "");

  titulo(T("  Visual", "  Visual style"));
  m.fundo = (await escolha(T("Fundo dos vídeos", "Video background"), ["escuro", "claro"], 1, ["dark", "light"]));
  m.cores = {
    principal: hex(await perguntar(T("  Cor principal (hex)", "  Primary color (hex)"), "#2EE59D"), "#2EE59D"),
    fundo: hex(await perguntar(T("  Cor de fundo (hex)", "  Background color (hex)"), m.fundo === "claro" ? "#F6F7F5" : "#0F1114"), m.fundo === "claro" ? "#F6F7F5" : "#0F1114"),
    texto: hex(await perguntar(T("  Cor do texto (hex)", "  Text color (hex)"), m.fundo === "claro" ? "#111814" : "#F1F4F2"), m.fundo === "claro" ? "#111814" : "#F1F4F2"),
  };
  m.fontes = {
    titulos: await perguntar(T("  Fonte dos títulos (do Google Fonts)", "  Heading font (from Google Fonts)"), "Instrument Serif"),
    texto: await perguntar(T("  Fonte do texto (do Google Fonts)", "  Body font (from Google Fonts)"), "Inter"),
  };
  const logo = await perguntar(T("  Logo (caminho de um SVG ou PNG; enter se não tiver)", "  Logo (path to SVG or PNG; press Enter if none)"), "");
  if (logo) {
    const caminho = resolve(logo.replace(/^~(?=$|\/)/, homedir()));
    if (existsSync(caminho) && statSync(caminho).isFile()) {
      mkdirSync(join(estudio, "public", "marca"), { recursive: true });
      const nome = `logo${extname(caminho).toLowerCase()}`;
      copyFileSync(caminho, join(estudio, "public", "marca", nome));
      m.logo = `marca/${nome}`;
      ok(T(`logo em public/marca/${nome}`, `logo at public/marca/${nome}`));
    } else nao(T(`não achei ${caminho}: o logo ficou de fora`, `not found: ${caminho}; logo skipped`));
  }
  m.movimento = await escolha(T("Estilo de movimento", "Motion style"), ["sóbrio (entradas suaves, pouco zoom)", "dinâmico (mais cortes e zooms)", "editorial (tipografia em destaque)"], 2, ["restrained (soft entrances, little zoom)", "dynamic (more cuts and zooms)", "editorial (emphasis on typography)"]);

  titulo(T("  Voz e tom", "  Voice and tone"));
  m.tom = await escolha(T("Tom", "Tone"), ["próximo e didático", "formal", "descontraído", "técnico"], 1, ["warm and educational", "formal", "casual", "technical"]);
  m.palavras_proibidas = lista(await perguntar(T("  Palavras que nunca podem aparecer (vírgula)", "  Words to avoid (comma-separated)"), ""));
  m.glossario = lista(await perguntar(T("  Termos da sua área que não podem virar sinônimo (vírgula)", "  Industry terms that must not be replaced with synonyms (comma-separated)"), ""));
  const voz = await perguntar(T("  Voz da ElevenLabs: enter para a Raquel, ou o voice_id de outra", "  ElevenLabs voice: press Enter for Lauren, or enter another voice_id"), T("Raquel", "Lauren"));
  m.voz = voz === T("Raquel", "Lauren") ? { nome: voz } : { nome: T("Voz da marca", "Brand voice"), voice_id: voz };

  titulo(T("  Chamada do fim dos vídeos", "  End-of-video call to action"));
  m.chamada = {
    texto: await perguntar(T("  Texto", "  Text"), T(`Conheça ${m.nome}`, `Discover ${m.nome}`)),
    endereco: await perguntar(T("  Endereço", "  Address"), m.site || ""),
    linha: await perguntar(T("  Linha de apoio", "  Supporting line"), ""),
  };

  titulo(T("  Vídeos para redes (versão 2.3)", "  Social videos (version 2.3)"));
  m.avatar = { provedor: (await escolha(T("Provedor do avatar apresentador", "Presenter avatar provider"), ["Higgsfield (principal)", "HeyGen (alternativa)", "não vou usar avatar"], 1, ["Higgsfield (primary)", "HeyGen (alternative)", "no avatar"])).split(" ")[0].toLowerCase() };

  mkdirSync(join(estudio, "marca"), { recursive: true });
  writeFileSync(join(estudio, "marca", "marca.json"), JSON.stringify(m, null, 2) + "\n");
  ok(T("marca/marca.json salvo", "marca/marca.json saved"));
  return m;
}

async function main() {
  if (tem("--versao")) {
    console.log(VERSAO);
    return;
  }
  const global = join(homedir(), ".claude", "skills");
  const projeto = join(process.cwd(), ".claude", "skills");

  // ── 0. o idioma, antes de tudo ─────────────────────────────────────
  // Vem primeiro porque decide DUAS coisas ao mesmo tempo: qual pasta de skills copiar (passo 1) e o
  // que vai para o kit.config.json (passo 2). Perguntar depois instalaria prompts em português num
  // estúdio em inglês. Sem TTY (--tudo, CI), o padrão é pt-BR, do projeto.
  const normaliza = (v) => {
    const t = String(v || "").trim().toLowerCase().replace(/_/g, "-");
    if (!t || /^pt(-br)?$/.test(t) || /^portug/.test(t)) return "pt-BR";
    if (/^en(-us)?$/.test(t) || /^english/.test(t)) return "en-US";
    return null;
  };
  let idioma = valor("--idioma") ? normaliza(valor("--idioma")) : null;
  if (valor("--idioma") && !idioma) {
    console.error(ajudaEn ? `--idioma accepts pt-BR or en-US (received "${valor("--idioma")}")` : `--idioma aceita pt-BR ou en-US (recebi "${valor("--idioma")}")`);
    process.exit(1);
  }
  if (!idioma && !process.env.CLAQUETE_IGNORA_CFG) {
    // Um estúdio que já existe manda: o idioma dele é o que vale, sem perguntar. Perguntar faria a
    // pessoa trocar a voz e as skills sem querer, e o --atualizar existe para não mexer no que é dela.
    const cfgAtual = [
      valor("--estudio") && join(resolve(valor("--estudio")), "kit.config.json"),
      join(process.cwd(), "estudio-video", "kit.config.json"),
      join(RAIZ, "estudio", "kit.config.json"),
    ].filter(Boolean).find((f) => existsSync(f));
    if (cfgAtual) {
      try {
        idioma = normaliza(JSON.parse(readFileSync(cfgAtual, "utf8")).idioma) || null;
      } catch {}
    }
  }
  // A detecção do idioma do sistema só vale quando a pessoa não disse nada e vai responder a pergunta:
  // ela vem pré-marcada, e o Enter aceita. Um LANG da máquina não deve decidir sozinho por ninguém.
  const doSistema = () => {
    const v = `${process.env.LC_ALL || ""} ${process.env.LC_MESSAGES || ""} ${process.env.LANG || ""} ${process.env.LANGUAGE || ""}`;
    if (/\bpt/i.test(v)) return "pt-BR";
    if (/\ben/i.test(v)) return "en-US";
    return null;
  };
  if (!idioma) {
    if (!process.stdin.isTTY || tem("--tudo") || tem("--sim")) idioma = "pt-BR";
    else {
      // O `rl` de verdade só nasce depois dos passos 1 e 2; aqui a pergunta é sozinha, e é fechada logo.
      const padrao = doSistema() || "pt-BR";
      const rl0 = createInterface({ input: process.stdin, output: process.stdout });
      console.log(`\n${verde("◆ Claquete.ai")} ${fraco(`v${VERSAO}`)}`);
      titulo("Language · Idioma");
      console.log(`  1) Português (Brasil)   ${fraco("os vídeos, as mensagens e as skills em português")}`);
      console.log(`  2) English (US)        ${fraco("the videos, the messages and the skills in English")}`);
      console.log(`  ${fraco(padrao === "en-US" ? "System language detected: English. Press Enter to accept." : "Enter aceita português.")}`);
      const r = (await rl0.question(`  ${fraco(`[${padrao === "en-US" ? 2 : 1}]`)} `)).trim();
      idioma = r === "" ? padrao : (/^2|^en/i.test(r) ? "en-US" : "pt-BR");
      rl0.close();
    }
  }
  IDIOMA = idioma;
  console.log(`\n${verde("◆ Claquete.ai")} ${fraco(`v${VERSAO}`)}  ${fraco(T("o estúdio de vídeo que o Claude opera", "the video studio Claude operates"))}`);
  // --desinstalar remove as skills dos DOIS idiomas: quem instalou em inglês e depois em português (ou o
  // contrário) ficaria com as skills do outro idioma no disco para sempre. Os nomes são os mesmos.
  const skills = lerSkills(pastaSkills(idioma));
  const nomesSkills = [...new Set([...skills.map((s) => s.nome), ...lerSkills(pastaSkills(idioma === "en-US" ? "pt-BR" : "en-US")).map((s) => s.nome)])];

  if (tem("--desinstalar")) {
    const destinos = tem("--projeto") ? [projeto] : tem("--global") ? [global] : [global, projeto];
    for (const destino of destinos) {
      for (const nome of nomesSkills) {
        const alvo = join(destino, nome);
        if (existsSync(alvo)) {
          rmSync(alvo, { recursive: true });
          console.log(T(`  removida: ${nome} ${fraco(`(${destino})`)}`, `  removed: ${nome} ${fraco(`(${destino})`)}`));
        }
      }
    }
    console.log(T("\nPronto. O estúdio e as skills de motion design ficam onde estão.\n", "\nDone. The studio and motion design skills stay where they are.\n"));
    return;
  }

  const atualizar = tem("--atualizar");
  const idiomaTrocado = atualizar && Boolean(valor("--idioma"));
  const semPerguntas = tem("--tudo") || tem("--sim") || !process.stdin.isTTY;
  let rl = semPerguntas ? null : createInterface({ input: process.stdin, output: process.stdout });
  const perguntar = async (q, padrao) => {
    if (!rl) return padrao;
    const r = (await rl.question(`${q} ${fraco(`[${padrao}]`)} `)).trim();
    return r || padrao;
  };
  const sim = async (q, padrao = "s") => {
    const resposta = await perguntar(`${q} ${T("(s/n)", "(y/n)")}`, IDIOMA === "en-US" && padrao === "s" ? "y" : padrao);
    return (IDIOMA === "en-US" ? /^(s|y)/i : /^s/i).test(resposta);
  };

  // ── 1. skills ──────────────────────────────────────────────────────
  let destino = tem("--projeto") ? projeto : global;
  if (!tem("--projeto") && !tem("--global") && rl) {
    titulo(T("Onde instalar as skills?", "Where should the skills be installed?"));
    console.log(T(`  1) para você, em todos os projetos  ${fraco(global)}`, `  1) for you, in all projects          ${fraco(global)}`));
    console.log(T(`  2) só neste projeto                 ${fraco(projeto)}`, `  2) only in this project             ${fraco(projeto)}`));
    destino = (await perguntar(T("Escolha", "Choose"), "1")) === "2" ? projeto : global;
  }
  let escolhidas = skills.map((s) => s.nome);
  if (valor("--skills")) escolhidas = valor("--skills").split(",").map((s) => s.trim()).filter(Boolean);
  const desconhecidas = escolhidas.filter((n) => !skills.some((s) => s.nome === n));
  if (desconhecidas.length) {
    console.error(T(`skill desconhecida: ${desconhecidas.join(", ")}`, `unknown skill: ${desconhecidas.join(", ")}`));
    process.exit(2);
  }
  titulo(T(`1/6 Skills em ${destino}`, `1/6 Skills in ${destino}`));
  mkdirSync(destino, { recursive: true });
  for (const nome of escolhidas) {
    copiarPasta(join(pastaSkills(idioma), nome), join(destino, nome));
    ok(`${nome} ${fraco(skills.find((s) => s.nome === nome).resumo)}`);
  }
  if (!tem("--sem-motion")) {
    const motion = instalarMotion(destino);
    if (motion.length) ok(`motion design (iart.ai, MIT): ${motion.join(", ")}`);
    const hairline = instalarHairline(destino);
    if (hairline.length) ok(T(`figuras isométricas (hairline, MIT): ${hairline.join(", ")}`, `isometric figures (hairline, MIT): ${hairline.join(", ")}`));
  }

  // ── 2. estúdio ─────────────────────────────────────────────────────
  let pastaEstudio = valor("--estudio") || (semPerguntas || atualizar ? "./estudio-video" : null);
  if (!pastaEstudio) {
    titulo(T("Criar o estúdio? (o projeto que monta os vídeos; as skills precisam dele)", "Create the studio? (the project that assembles videos; the skills need it)"));
    const r = await perguntar(T("Pasta, ou 'nao' para pular", "Folder, or 'no' to skip"), "./estudio-video");
    if (!/^n(ao|ão|o)?$/i.test(r)) pastaEstudio = r;
  }
  const estudio = pastaEstudio ? resolve(pastaEstudio) : null;
  if (estudio) {
    titulo(T(`2/6 Estúdio em ${estudio}`, `2/6 Studio in ${estudio}`));
    if (existsSync(join(estudio, "kit.config.json"))) {
      const antes = existsSync(join(estudio, "VERSAO")) ? readFileSync(join(estudio, "VERSAO"), "utf8").trim() : "1.x";
      atualizarEstudio(estudio);
      ok(T(`estúdio atualizado de ${antes} para ${VERSAO}: roteiros, gravações, marca, saída, chaves e a sua configuração ficaram como estavam`, `studio updated from ${antes} to ${VERSAO}: scripts, recordings, brand, output, keys and your settings were preserved`));
    } else if (existsSync(estudio) && readdirSync(estudio).length) {
      console.log(T(`  ${estudio} já existe e não está vazia. Escolha outra pasta com --estudio.`, `  ${estudio} already exists and is not empty. Choose another folder with --estudio.`));
      process.exit(2);
    } else {
      const fora = NAO_COPIAR.map((x) => join(PASTA_ESTUDIO, x));
      cpSync(PASTA_ESTUDIO, estudio, { recursive: true, filter: (f) => !fora.some((x) => f === x || f.startsWith(x + sep)) });
      ok(T("arquivos copiados", "files copied"));
    }
    writeFileSync(join(estudio, "VERSAO"), `${VERSAO}\n`);
    // O kit.config.json do repositório é pt-BR (é o padrão e o que mantém a assinatura da narração de
    // quem já narrou em português). O `cpSync` copia ele verbatim e a mesclagem do --atualizar nunca
    // sobrescreve a escolha da pessoa: por isso a escolha DESTA instalação é escrita à mão, aqui.
    const arqCfg = join(estudio, "kit.config.json");
    if (existsSync(arqCfg)) {
      if (idioma === "en-US") {
        const c = JSON.parse(readFileSync(arqCfg, "utf8"));
        c.idioma = "en-US";
        writeFileSync(arqCfg, JSON.stringify(c, null, 2) + "\n");
        ok(T("idioma do estúdio: en-US (a voz da Lauren entra no passo 4)", "studio language: en-US (Lauren voice is set up in step 4)"));
      } else if (valor("--idioma")) {
        const c = JSON.parse(readFileSync(arqCfg, "utf8"));
        c.idioma = "pt-BR";
        writeFileSync(arqCfg, JSON.stringify(c, null, 2) + "\n");
      }
    }
  }

  // ── 3. ferramentas da máquina ──────────────────────────────────────
  titulo(T("3/6 Ferramentas da máquina", "3/6 Machine tools"));
  const nodeOk = Number(process.versions.node.split(".")[0]) >= 18;
  nodeOk ? ok(`Node ${process.versions.node}`) : nao(T(`Node 18+ necessário (tem ${process.versions.node}): https://nodejs.org`, `Node 18+ required (found ${process.versions.node}): https://nodejs.org`));
  for (const [pacote, presente] of [
    ["ffmpeg", () => existe("ffmpeg") && existe("ffprobe")],
    ["python", () => Boolean(comandoPython())],
  ]) {
    const nome = pacote === "python" ? "Python 3" : "ffmpeg";
    if (presente()) {
      ok(nome);
      continue;
    }
    const cmd = instaladorDoSistema(pacote);
    if (!cmd) {
      nao(T(`${nome} não encontrado e não sei instalar sozinho aqui. ${SO === "darwin" ? "Instale o Homebrew (https://brew.sh) e rode de novo." : "Instale pelo gerenciador de pacotes do sistema."}`, `${nome} not found and cannot be installed automatically here. ${SO === "darwin" ? "Install Homebrew (https://brew.sh) and try again." : "Install it with your system package manager."}`));
      continue;
    }
    if (tem("--sem-ferramentas")) {
      nao(T(`${nome} não encontrado. Para instalar: ${cmd}`, `${nome} not found. To install: ${cmd}`));
      continue;
    }
    if (semPerguntas || (await sim(T(`  ${nome} não encontrado. Instalar agora com "${cmd}"?`, `  ${nome} not found. Install now with "${cmd}"?`)))) {
      console.log(fraco(`  $ ${cmd}`));
      roda(cmd) && presente() ? ok(T(`${nome} instalado`, `${nome} installed`)) : nao(T(`${nome}: a instalação não terminou; rode à mão: ${cmd}`, `${nome}: installation did not finish; run manually: ${cmd}`));
    } else nao(T(`${nome} ficou de fora. Depois: ${cmd}`, `${nome} skipped. Later: ${cmd}`));
  }
  if (estudio) {
    console.log(fraco(T("  instalando as dependências do estúdio (Remotion, React, Playwright)...", "  installing studio dependencies (Remotion, React, Playwright)...")));
    roda("npm install --no-audit --no-fund", estudio) ? ok(T("dependências do estúdio (npm)", "studio dependencies (npm)")) : nao(T("npm install falhou: rode dentro do estúdio", "npm install failed: run it inside the studio"));
    console.log(fraco(T("  baixando o navegador que o Remotion usa para renderizar...", "  downloading the browser Remotion uses to render...")));
    roda("npx remotion browser ensure", estudio) ? ok(T("navegador do Remotion", "Remotion browser")) : nao(T("navegador do Remotion: rode 'npx remotion browser ensure' no estúdio", "Remotion browser: run 'npx remotion browser ensure' in the studio"));
    const cmdPw = SO === "linux" ? "npx playwright install --with-deps chromium" : "npx playwright install chromium";
    if (tem("--sem-ferramentas")) nao(T(`navegador do Playwright: rode '${cmdPw}' no estúdio quando for gravar a tela ou fotografar as telas animadas`, `Playwright browser: run '${cmdPw}' in the studio when recording the screen or capturing animated screens`));
    else if (semPerguntas || (await sim(T("  Instalar o navegador do Playwright (a IA usa para operar sistemas, gravar a tela e fotografar as telas animadas)?", "  Install the Playwright browser (Claude uses it to operate apps, record the screen and capture animated screens)?")))) {
      roda(cmdPw, estudio) ? ok(T("navegador do Playwright", "Playwright browser")) : nao(T(`navegador do Playwright: rode '${cmdPw}' no estúdio`, `Playwright browser: run '${cmdPw}' in the studio`));
    }
    // Telas animadas: o app de cenas (Vite + React + motion) e os componentes do React Bits, baixados do site oficial.
    const cenas = join(estudio, "cenas");
    if (existsSync(cenas) && !tem("--sem-cenas")) {
      console.log(fraco(T("  instalando o app das telas animadas (Vite, React, motion)...", "  installing the animated screens app (Vite, React, motion)...")));
      if (roda("npm install --no-audit --no-fund", cenas, false)) {
        ok(T("telas animadas (cenas/)", "animated screens (cenas/)"));
        if (tem("--sem-reactbits")) nao(T("sem React Bits: as telas animadas usam só as peças próprias, feitas com motion", "without React Bits: animated screens use only built-in pieces made with motion"));
        else if (semPerguntas || (await sim(T("  Baixar do reactbits.dev os 12 componentes animados grátis (textos, contador, esfera, aurora, partículas) para as telas animadas?", "  Download the 12 free animated components from reactbits.dev (text, counter, orb, aurora, particles) for animated screens?")))) {
          console.log(fraco(T("  baixando do registro oficial do React Bits para a sua máquina (licença MIT + Commons Clause: use à vontade, só não revenda os componentes)...", "  downloading from the official React Bits registry to your machine (MIT + Commons Clause: use freely, but do not resell the components)...")));
          const r = await baixarReactBits(cenas, "");
          if (r.baixados.length) ok(`React Bits: ${r.baixados.join(", ")}${r.instalou ? "" : fraco(T(" (as dependências não instalaram: rode 'npm install' em cenas/)", " (dependencies were not installed: run 'npm install' in cenas/)"))}`);
          if (r.falhas.length) nao(T(`React Bits, não baixou: ${r.falhas.join(", ")}`, `React Bits, download failed: ${r.falhas.join(", ")}`));
        } else nao(T("sem React Bits: as telas animadas usam só as peças próprias. Depois: npx github:dantaspaulo/claquete --atualizar", "without React Bits: animated screens use only built-in pieces. Later: npx github:dantaspaulo/claquete --atualizar"));
      } else nao(T("o app das telas animadas não instalou: rode 'npm install' em cenas/ (as outras telas funcionam sem ele)", "animated screens app was not installed: run 'npm install' in cenas/ (other screens still work)"));
    }
    // Transcrição local num ambiente Python só do estúdio (.venv): não mexe no Python do sistema.
    const py = comandoPython();
    const venvPy = join(estudio, ".venv", SO === "win32" ? "Scripts\\python.exe" : "bin/python");
    if (py && !tem("--sem-ferramentas")) {
      const temWhisper = existsSync(venvPy) && spawnSync(`"${venvPy}" -c "import faster_whisper"`, { shell: true, stdio: "pipe" }).status === 0;
      if (temWhisper) ok(T("transcrição local (faster-whisper, em .venv)", "local transcription (faster-whisper, in .venv)"));
      else if (tem("--transcricao-local") || (!semPerguntas && (await sim(T("  Transcrição local e gratuita para a revisão da fala e a edição de gravações (faster-whisper; uns 500 MB com o modelo, baixado no primeiro uso)?", "  Free local transcription for narration review and editing recordings (faster-whisper; about 500 MB with the model, downloaded on first use)?"))))) {
        const cmd = `${py} -m venv .venv && "${venvPy}" -m pip install --quiet faster-whisper`;
        roda(cmd, estudio) ? ok(T("transcrição local (faster-whisper, em .venv)", "local transcription (faster-whisper, in .venv)")) : nao(T(`faster-whisper: rode no estúdio: ${cmd}`, `faster-whisper: run in the studio: ${cmd}`));
      } else nao(T("sem transcrição local: a revisão da fala é feita pela sessão do Claude e por você, ouvindo", "without local transcription: Claude and you review the narration by listening"));
    }
  }

  // ── 4. chave e voz ─────────────────────────────────────────────────
  // A chave é lida sem eco: fecha o readline antes (ele ecoaria o que se digita) e abre de novo para a marca.
  rl?.close();
  rl = null;
  if (estudio) {
    titulo(T("4/6 Chave e voz", "4/6 Key and voice"));
    const arqEnv = join(estudio, ".env");
    const atual = existsSync(arqEnv) ? readFileSync(arqEnv, "utf8") : "";
    const temNoEnv = (k) => new RegExp(`^${k}=.+`, "m").test(atual);
    const linhas = [];
    const k = "ELEVENLABS_API_KEY";
    if (temNoEnv(k)) ok(T(`${k} já está no .env`, `${k} is already in .env`));
    else {
      let v = process.env[k] || "";
      if (!v && !semPerguntas) v = await perguntarSegredo(`  ${k} ${fraco(T("(elevenlabs.io → Configurações → API Keys; enter para pular)", "(elevenlabs.io → Settings → API Keys; press Enter to skip)"))}: `);
      if (v) {
        linhas.push(`${k}=${v}`);
        ok(T(`${k} guardada em ${arqEnv}`, `${k} saved in ${arqEnv}`));
      } else nao(T(`${k} ficou de fora: ponha no ${arqEnv} depois`, `${k} skipped: add it to ${arqEnv} later`));
    }
    // React Bits Pro: opcional. Com a licença, as telas animadas ganham os componentes que as aulas do ChatADV usam.
    const cenasPro = join(estudio, "cenas");
    if (existsSync(join(cenasPro, "node_modules")) && !tem("--sem-cenas") && !tem("--sem-reactbits")) {
      const kp = "REACTBITS_LICENSE_KEY";
      let chave = (atual.match(new RegExp(`^${kp}=(.+)$`, "m")) || [])[1]?.trim().replace(/^["']|["']$/g, "") || process.env[kp] || "";
      const nova = !temNoEnv(kp) && !chave && !semPerguntas;
      if (nova) chave = await perguntarSegredo(`  ${T("Licença do React Bits Pro", "React Bits Pro license")} ${fraco(T("(se tiver; os componentes que as aulas do ChatADV usam; enter para pular)", "(if you have one; components used in ChatADV lessons; press Enter to skip)"))}: `);
      if (chave) {
        const r = await baixarReactBits(cenasPro, chave);
        const pro = r.baixados.filter((n) => RB_PRO.includes(n));
        if (pro.length) {
          ok(`React Bits Pro: ${pro.join(", ")}`);
          // guarda no .env só a licença que a pessoa digitou agora (a do ambiente fica onde ela pôs)
          if (nova) linhas.push(`${kp}=${chave}`);
        }
        if (r.falhas.length) nao(T(`React Bits, não baixou: ${r.falhas.join(", ")}`, `React Bits, download failed: ${r.falhas.join(", ")}`));
      } else nao(T("sem React Bits Pro (opcional): as telas animadas usam os componentes grátis e as peças próprias", "without React Bits Pro (optional): animated screens use the free components and built-in pieces"));
    }
    if (/^OPENAI_API_KEY=/m.test(atual)) nao(T("o .env ainda tem OPENAI_API_KEY: a Claquete 2.0 não usa mais; pode apagar a linha", "the .env still has OPENAI_API_KEY: Claquete 2.0 no longer uses it; you can remove that line"));
    if (linhas.length) {
      writeFileSync(arqEnv, (atual ? atual.replace(/\n?$/, "\n") : T("# Chaves do estúdio. Este arquivo é só seu: nunca vai para repositório.\n", "# Studio keys. This file is yours alone: never commit it.\n")) + linhas.join("\n") + "\n");
      try {
        chmodSync(arqEnv, 0o600);
      } catch {}
    }
    const py = comandoPython();
    // `--atualizar --idioma en-US` precisa passar por aqui: é a hora em que a voz nova entra na
    // conta da pessoa. Sem a flag, o --atualizar continua não mexendo em nada.
    if (py && (temNoEnv(k) || linhas.some((l) => l.startsWith(`${k}=`))) && (!atualizar || idiomaTrocado)) {
      console.log(fraco(T("  preparando a voz na sua conta da ElevenLabs e gerando um áudio de teste...", "  setting up the voice in your ElevenLabs account and generating a test audio file...")));
      roda(`${py} scripts/kit.py voz`, estudio) ? ok(T("voz pronta (ouça saida/teste-voz.mp3)", "voice ready (listen to saida/teste-voz.mp3)")) : nao(T(`a voz não ficou pronta: rode '${py} scripts/kit.py voz' no estúdio`, `voice setup failed: run '${py} scripts/kit.py voz' in the studio`));
    }
  }

  // ── 5. a sua marca ─────────────────────────────────────────────────
  if (!semPerguntas) rl = createInterface({ input: process.stdin, output: process.stdout });
  if (estudio) {
    titulo(T("5/6 A sua marca", "5/6 Your brand"));
    const temMarca = existsSync(join(estudio, "marca", "marca.json"));
    if (tem("--sem-marca") || !rl) nao(temMarca ? T("marca mantida", "brand kept") : T("sem questionário agora: depois, no Claude, peça \"configura minha marca\"", "skipping the questionnaire: later, ask Claude \"set up my brand\""));
    else if (!temMarca || (await sim(T("  Você já tem uma marca configurada. Responder de novo?", "  You already have a configured brand. Answer again?"), "n"))) {
      await questionarioMarca(perguntar, estudio);
      const py = comandoPython();
      py && roda(`${py} scripts/kit.py marca`, estudio) ? ok(T("marca aplicada ao estúdio", "brand applied to the studio")) : nao(T("rode 'python3 scripts/kit.py marca' no estúdio", "run 'python3 scripts/kit.py marca' in the studio"));
    } else ok(T("marca mantida", "brand kept"));
  }
  rl?.close();
  rl = null;

  // ── 6. teste final ─────────────────────────────────────────────────
  if (estudio) {
    titulo(T("6/6 Teste", "6/6 Test"));
    const py = comandoPython();
    py && roda(`${py} scripts/kit.py validar exemplo`, estudio, false) ? ok(T("o vídeo de exemplo passa na validação", "the example video passes validation")) : nao(T("validação do exemplo falhou", "example validation failed"));
    roda("npx remotion compositions src/index.ts", estudio, false) ? ok(T("o Remotion monta o projeto", "Remotion assembles the project")) : nao(T("o Remotion não montou o projeto: rode 'npx remotion compositions src/index.ts' no estúdio", "Remotion could not assemble the project: run 'npx remotion compositions src/index.ts' in the studio"));
    const rb = join(estudio, "cenas", "src", "components", "react-bits");
    if (existsSync(join(estudio, "cenas", "node_modules"))) {
      const n = existsSync(rb) ? readdirSync(rb).filter((f) => /\.(tsx|jsx)$/.test(f)).length : 0;
      roda("npx vite build --logLevel error --outDir dist --emptyOutDir", join(estudio, "cenas"), false)
        ? ok(T(`as telas animadas compilam (${n} componentes do React Bits nesta máquina)`, `animated screens build (${n} React Bits components on this machine)`))
        : nao(T("as telas animadas não compilaram: rode 'npx vite build' em cenas/", "animated screens failed to build: run 'npx vite build' in cenas/"));
    }
  }

  titulo(T(`Pronto: Claquete.ai ${VERSAO}`, `Done: Claquete.ai ${VERSAO}`));
  if (estudio) {
    console.log(T(`  Abra o Claude na pasta ${verde(pastaEstudio)} e diga ${verde('"quero fazer um vídeo"')}.`, `  Open Claude in ${verde(pastaEstudio)} and say ${verde('"I want to make a video"')}.`));
    console.log(T("  Ele pergunta o tipo (demonstração, aula animada, dica, caso, trilha) e, nas aulas, a duração de 2 a 5 minutos.", "  Claude asks for the type (demo, animated lesson, quick tip, walkthrough, track) and, for lessons, a duration of 2 to 5 minutes."));
    console.log(T(`  Para ver as telas animadas: ${verde('"faz a aula animada-exemplo"')} (cenas em React, fotografadas no tempo da voz).`, `  To see animated screens: ${verde('"make the animada-exemplo lesson"')} (React scenes captured in sync with the voice).`));
    console.log(T(`  Gravou no Screen Studio 4? ${verde('"edita minha gravação"')}: editada, híbrida e cortes em pé, com a sua voz.`, `  Recorded in Screen Studio 4? ${verde('"edit my recording"')}: edited, hybrid and vertical cuts with your voice.`));
    if (existsSync(join(estudio, "marca", "material"))) console.log(T(`  Para ele ler o material da marca: ${verde('"configura minha marca"')}.`, `  To have Claude read your brand material: ${verde('"set up my brand"')}.`));
  }
  console.log(fraco(T("  Durante as gravações a IA opera o computador: deixe a máquina livre e feche o que for pesado.\n", "  During recordings, Claude operates your computer: leave it free and close resource-heavy apps.\n")));
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
