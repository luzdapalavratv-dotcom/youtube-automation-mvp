import os
import json
import uuid
from datetime import datetime

import streamlit as st
from groq import Groq  # IA principal para roteiro [web:169][web:181]

st.set_page_config(page_title="1 – Roteiro Viral", layout="wide")
st.title("📝 1 – Gerador de Roteiro Longo para YouTube (Groq)")

# -------------------------------------------------------------------
# Integração com o "banco" (monitor)
# -------------------------------------------------------------------
def criar_db_vazio():
    return {"canais": {}}

if "db" not in st.session_state:
    st.session_state.db = criar_db_vazio()
db = st.session_state.db

if "canal_atual_id" not in st.session_state:
    st.session_state.canal_atual_id = None
if "video_atual_id" not in st.session_state:
    st.session_state.video_atual_id = None

canal_id = st.session_state.canal_atual_id
video_id = st.session_state.video_atual_id

if not canal_id or canal_id not in db["canais"]:
    st.error("Nenhum canal selecionado. Vá ao app principal (monitor) e escolha um canal/vídeo.")
    st.stop()

canal = db["canais"][canal_id]
videos = canal["videos"]
if not video_id or video_id not in videos:
    st.error("Nenhum vídeo selecionado. Vá ao monitor e escolha um vídeo para este canal.")
    st.stop()

video = videos[video_id]

# -------------------------------------------------------------------
# Artefatos de roteiro
# -------------------------------------------------------------------
if "artefatos" not in video:
    video["artefatos"] = {}

if "roteiro" not in video["artefatos"] or video["artefatos"]["roteiro"] is None:
    video["artefatos"]["roteiro"] = {
        "id": str(uuid.uuid4())[:8],
        "titulo_video": video.get("titulo", ""),
        "hook": "",
        "promessa": "",
        "estrutura": "",
        "roteiro": {},
        "image_prompts": {},  # prompts por parágrafo
        "tokens_uso": 0,
        "modelo_usado": "",
        "gerado_em": None,
    }

# -------------------------------------------------------------------
# Cliente Groq
# -------------------------------------------------------------------
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY não encontrado em st.secrets ou variáveis de ambiente.")
        st.stop()
    return Groq(api_key=api_key)

groq_client = get_groq_client()  # [web:169]
MODELO_GROQ = "llama-3.3-70b-versatile"  # [web:181]

# -------------------------------------------------------------------
# Sidebar – parâmetros de roteiro
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📺 Contexto")
    st.markdown(f"**Canal:** {canal.get('nome','')}")
    st.markdown(f"**Nicho:** {canal.get('nicho','')}")
    st.markdown(f"**Vídeo:** {video.get('titulo','')}")

    st.markdown("---")
    st.header("🎯 Objetivo do vídeo")

    objetivo = st.selectbox(
        "Função principal",
        [
            "História emocional longa",
            "Estudo bíblico narrativo",
            "Documentário inspirador",
        ],
        index=0,
    )

    duracao = "Longo (30-60 min)"

    st.markdown("---")
    st.header("🧑‍💻 Persona / Tom")

    persona_canal = canal.get("persona", "") or "Adultos interessados no tema do canal."
    persona_custom = st.text_area(
        "Persona do público",
        value=persona_canal,
        height=100,
    )

    tom_marca = canal.get(
        "tom_marca",
        "Tom conversado, profundo, acolhedor e didático, sem jargões difíceis.",
    )
    tom_custom = st.text_area(
        "Tom de voz da marca",
        value=tom_marca,
        height=100,
    )

    restricoes = st.text_area(
        "Palavras / temas a evitar",
        value=canal.get("palavras_proibidas", ""),
        height=80,
    )

# -------------------------------------------------------------------
# Função Groq – estrutura longa + prompts de imagem
# -------------------------------------------------------------------
def chamar_modelo_roteiro_groq(
    titulo_video: str,
    briefing: str,
    objetivo: str,
    persona: str,
    tom: str,
    restricoes: str,
    canal_nome: str,
    canal_nicho: str,
):
    """
    Gera roteiro longo com contagem aproximada de palavras por bloco
    e prompts de imagem para cada parágrafo.
    """

    sistema = (
        "Você é um roteirista profissional de vídeos longos para YouTube, "
        "especialista em storytelling e retenção. Sempre responde em JSON válido."
    )

    usuario = f"""
Contexto do canal:
- Nome do canal: {canal_nome}
- Nicho do canal: {canal_nicho}
- Persona do público: {persona}
- Tom de voz da marca: {tom}
- Palavras/temas proibidos (não use): {restricoes or "nenhuma informada"}

Briefing do vídeo:
- Tipo: {objetivo}
- Título provisório do vídeo: {titulo_video}
- Briefing adicional: {briefing or "nenhum briefing extra"}

Tarefa:
Crie um ROTEIRO COMPLETO em português brasileiro, em forma de história/narrativa, com a seguinte estrutura e tamanhos aproximados:

1. Hook: 1 parágrafo com cerca de 300 palavras.
2. Introdução com CTA: 3 parágrafos, cerca de 500 palavras no total.
3. Capítulo 1: 5 parágrafos, cerca de 1500 palavras no total.
4. Capítulo 2: 5 parágrafos, cerca de 1500 palavras no total.
5. Capítulo 3: 5 parágrafos, cerca de 1500 palavras no total.
6. Capítulo 4: 5 parágrafos, cerca de 1500 palavras no total.
7. Capítulo 5: 5 parágrafos, cerca de 1500 palavras no total.
8. Conclusão: desfecho da história com CTA, 3 parágrafos e cerca de 500 palavras no total.

Importante:
- Escreva todos os parágrafos como se fossem lidos em voz alta, com linguagem natural, envolvente e respeitosa.
- Não use listas nem Markdown no texto dos parágrafos, apenas prosa contínua.
- Adapte vocabulário e exemplos ao nicho do canal e à persona.

Além do texto, para CADA parágrafo, gere um prompt de IMAGEM extremamente descritivo (em inglês), próprio para ser usado em modelos de geração de imagens como Pollinations (estilo cinematográfico, alta qualidade, 16:9).

Formato OBRIGATÓRIO da resposta (JSON puro):

{{
  "hook": {{
    "paragrafos": ["texto do parágrafo único do hook"],
    "image_prompts": ["prompt em inglês para esse parágrafo"]
  }},
  "introducao": {{
    "paragrafos": ["p1", "p2", "p3"],
    "image_prompts": ["prompt p1", "prompt p2", "prompt p3"]
  }},
  "capitulo_1": {{
    "paragrafos": ["p1", "p2", "p3", "p4", "p5"],
    "image_prompts": ["...", "...", "...", "...", "..."]
  }},
  "capitulo_2": {{ ... mesmo formato de capitulo_1 ... }},
  "capitulo_3": {{ ... }},
  "capitulo_4": {{ ... }},
  "capitulo_5": {{ ... }},
  "conclusao": {{
    "paragrafos": ["p1", "p2", "p3"],
    "image_prompts": ["prompt p1", "prompt p2", "prompt p3"]
  }},
  "resumo": {{
    "hook": "frase curta de resumo do gancho",
    "promessa": "resumo do benefício do vídeo",
    "estrutura": "descrição em 2-4 frases da jornada do vídeo"
  }}
}}

Regras para os image_prompts:
- Sempre em inglês (mesmo que o roteiro esteja em português).
- Descrever a cena do parágrafo como um frame de filme 16:9.
- Não colocar texto escrito na imagem (sem phrases on screen).
- Incluir estilo (cinematic, ultra realistic, dramatic lighting, etc.).
"""

    resposta = groq_client.chat.completions.create(
        model=MODELO_GROQ,
        messages=[
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        temperature=0.7,
        max_tokens=8000,
    )

    conteudo = resposta.choices[0].message.content
    tokens_total = getattr(resposta.usage, "total_tokens", 0)

    inicio = conteudo.find("{")
    fim = conteudo.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("A resposta do modelo não contém JSON válido.")
    json_str = conteudo[inicio : fim + 1]

    data = json.loads(json_str)

    resumo = data.get("resumo", {})
    hook_resumo = resumo.get("hook", "").strip()
    promessa = resumo.get("promessa", "").strip()
    estrutura = resumo.get("estrutura", "").strip()

    roteiro_completo = {}
    image_prompts = {}

    blocos = [
        "hook",
        "introducao",
        "capitulo_1",
        "capitulo_2",
        "capitulo_3",
        "capitulo_4",
        "capitulo_5",
        "conclusao",
    ]

    for bloco in blocos:
        bloco_data = data.get(bloco, {}) or {}
        paragrafos = bloco_data.get("paragrafos", []) or []
        prompts = bloco_data.get("image_prompts", []) or []
        # garante mesmo tamanho
        if len(prompts) < len(paragrafos):
            prompts += ["cinematic wide shot, detailed, 4k, 16:9"] * (
                len(paragrafos) - len(prompts)
            )
        roteiro_completo[bloco] = paragrafos
        image_prompts[bloco] = prompts

    return {
        "hook": hook_resumo,
        "promessa": promessa,
        "estrutura": estrutura,
        "roteiro": roteiro_completo,
        "image_prompts": image_prompts,
        "tokens": tokens_total,
        "modelo": MODELO_GROQ,
    }

# -------------------------------------------------------------------
# Área principal – título e briefing
# -------------------------------------------------------------------
st.subheader("🎬 Título e briefing do vídeo")

col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    titulo_video = st.text_input(
        "Título do vídeo (visão inicial)",
        value=video.get("titulo", video["artefatos"]["roteiro"].get("titulo_video", "")),
    )
with col_t2:
    dur_estimada = st.selectbox(
        "Estimativa de duração (referência interna)",
        ["30-40 min", "40-60 min"],
        index=0,
    )

briefing = st.text_area(
    "Briefing adicional (contexto da história, personagens, referências bíblicas, etc.)",
    value=video.get("descricao", ""),
    height=140,
)

# -------------------------------------------------------------------
# Geração do roteiro
# -------------------------------------------------------------------
st.subheader("⚙️ Geração do roteiro com IA (Groq)")

col_bt1, col_bt2 = st.columns(2)

with col_bt1:
    if st.button("🚀 Gerar / regenerar roteiro completo", type="primary"):
        if not titulo_video.strip():
            st.warning("Informe ao menos um título para o vídeo.")
        else:
            if video["artefatos"]["roteiro"].get("roteiro"):
                st.info("Um roteiro já existe. O novo irá substituir o atual.")
            with st.spinner("Gerando roteiro longo com a IA da Groq..."):
                try:
                    resultado = chamar_modelo_roteiro_groq(
                        titulo_video=titulo_video.strip(),
                        briefing=briefing,
                        objetivo=objetivo,
                        persona=persona_custom,
                        tom=tom_custom,
                        restricoes=restricoes,
                        canal_nome=canal.get("nome", ""),
                        canal_nicho=canal.get("nicho", ""),
                    )

                    video["artefatos"]["roteiro"] = {
                        "id": video["artefatos"]["roteiro"].get(
                            "id", str(uuid.uuid4())[:8]
                        ),
                        "titulo_video": titulo_video.strip(),
                        "hook": resultado.get("hook", ""),
                        "promessa": resultado.get("promessa", ""),
                        "estrutura": resultado.get("estrutura", ""),
                        "roteiro": resultado.get("roteiro", {}),
                        "image_prompts": resultado.get("image_prompts", {}),
                        "tokens_uso": resultado.get("tokens", 0),
                        "modelo_usado": resultado.get("modelo", MODELO_GROQ),
                        "gerado_em": datetime.now().isoformat(),
                    }
                    video["status"]["1_roteiro"] = True
                    video["ultima_atualizacao"] = datetime.now().isoformat()
                    st.success("Roteiro gerado com sucesso pela Groq e salvo para este vídeo.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao chamar a IA da Groq: {e}")

with col_bt2:
    if st.button("🗑 Limpar roteiro atual"):
        video["artefatos"]["roteiro"] = {
            "id": str(uuid.uuid4())[:8],
            "titulo_video": titulo_video.strip(),
            "hook": "",
            "promessa": "",
            "estrutura": "",
            "roteiro": {},
            "image_prompts": {},
            "tokens_uso": 0,
            "modelo_usado": "",
            "gerado_em": None,
        }
        video["status"]["1_roteiro"] = False
        video["ultima_atualizacao"] = datetime.now().isoformat()
        st.success("Roteiro limpo para este vídeo.")
        st.rerun()

st.markdown("---")

# -------------------------------------------------------------------
# Resumo do roteiro
# -------------------------------------------------------------------
dados = video["artefatos"]["roteiro"]

st.subheader("📌 Resumo do roteiro")

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.markdown("**Hook (abertura forte)**")
    st.write(dados.get("hook", "") or "_Ainda não definido._")
with col_r2:
    st.markdown("**Promessa do vídeo**")
    st.write(dados.get("promessa", "") or "_Ainda não definida._")
with col_r3:
    st.markdown("**Estrutura geral**")
    st.write(dados.get("estrutura", "") or "_Ainda não definida._")

meta = {
    "Modelo": dados.get("modelo_usado") or "-",
    "Tokens (aprox.)": dados.get("tokens_uso") or 0,
    "Gerado em": (dados.get("gerado_em") or "")[:16],
}
st.caption(
    f"Modelo: {meta['Modelo']} · Tokens: {meta['Tokens (aprox.)']} · Gerado em: {meta['Gerado em']}"
)

st.markdown("---")

# -------------------------------------------------------------------
# Edição das seções e prompts (apenas visualização/ajuste)
# -------------------------------------------------------------------
st.subheader("🧩 Seções e parágrafos do roteiro")

roteiro_blocos = dados.get("roteiro", {}) or {}
image_prompts = dados.get("image_prompts", {}) or {}

if not roteiro_blocos:
    st.info(
        "Nenhum roteiro registrado ainda. Gere o roteiro com a IA da Groq "
        "para ver os capítulos e parágrafos."
    )
else:
    blocos_ordenados = [
        "hook",
        "introducao",
        "capitulo_1",
        "capitulo_2",
        "capitulo_3",
        "capitulo_4",
        "capitulo_5",
        "conclusao",
    ]
    labels = {
        "hook": "Hook",
        "introducao": "Introdução com CTA",
        "capitulo_1": "Capítulo 1",
        "capitulo_2": "Capítulo 2",
        "capitulo_3": "Capítulo 3",
        "capitulo_4": "Capítulo 4",
        "capitulo_5": "Capítulo 5",
        "conclusao": "Conclusão",
    }

    tabs = st.tabs([labels.get(b, b) for b in blocos_ordenados])

    for bloco, tab in zip(blocos_ordenados, tabs):
        paragrafos = roteiro_blocos.get(bloco, []) or []
        prompts = image_prompts.get(bloco, []) or []
        if len(prompts) < len(paragrafos):
            prompts += [""] * (len(paragrafos) - len(prompts))

        with tab:
            st.markdown(f"**{labels.get(bloco, bloco)} – parágrafos e prompts de imagem**")
            for i, texto_par in enumerate(paragrafos):
                st.markdown(f"**Parágrafo {i+1}**")
                novo_texto = st.text_area(
                    f"Texto do parágrafo {i+1}",
                    value=texto_par,
                    height=180,
                    key=f"{bloco}_par_{i}",
                )
                paragrafos[i] = novo_texto

                prompt_atual = prompts[i] if i < len(prompts) else ""
                novo_prompt = st.text_input(
                    f"Prompt de imagem (inglês) para o parágrafo {i+1}",
                    value=prompt_atual,
                    key=f"{bloco}_img_{i}",
                    help="Esse texto será usado apenas na página de Thumbnails para gerar a imagem.",
                )
                prompts[i] = novo_prompt

            roteiro_blocos[bloco] = paragrafos
            image_prompts[bloco] = prompts

if st.button("💾 Salvar alterações de texto e prompts"):
    video["artefatos"]["roteiro"]["roteiro"] = roteiro_blocos
    video["artefatos"]["roteiro"]["image_prompts"] = image_prompts
    video["artefatos"]["roteiro"]["titulo_video"] = titulo_video.strip()
    if not video["artefatos"]["roteiro"].get("gerado_em"):
        video["artefatos"]["roteiro"]["gerado_em"] = datetime.now().isoformat()
    video["status"]["1_roteiro"] = True
    video["ultima_atualizacao"] = datetime.now().isoformat()
    st.success("Roteiro e prompts de imagem atualizados para este vídeo.")

st.markdown("---")
st.caption(
    "Os prompts de imagem salvos aqui serão usados automaticamente na página "
    "**2 – Thumbnail / Imagens**, que gerará todas as imagens no Pollinations (modelo turbo)."
)
