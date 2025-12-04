import streamlit as st
from datetime import datetime
import uuid

st.set_page_config(page_title="1 – Roteiro Viral", layout="wide")
st.title("📝 1 – Gerador de Roteiro Viral para YouTube")

# -------------------------------------------------------------------
# Integra com o "banco" e seleção do monitor
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
# Garante estrutura de artefatos
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
        "tokens_uso": 0,
        "modelo_usado": "",
        "gerado_em": None,
    }

# -------------------------------------------------------------------
# Sidebar – contexto e parâmetros de roteiro
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
            "Educar (aula, explicação)",
            "Inspirar (história, testemunho)",
            "Converter (venda/call to action)",
            "Entreter (humor, storytelling)",
        ],
        index=0,
    )

    duracao = st.selectbox(
        "Duração desejada",
        [
            "Curto (3-5 min)",
            "Médio (6-10 min)",
            "Longo (11-20 min)",
        ],
        index=1,
    )

    persona = canal.get("persona", "")
    if not persona:
        persona = "Adultos interessados no tema do canal, nível iniciante/intermediário."

    st.markdown("---")
    st.header("🧑‍💻 Persona do público")
    persona_custom = st.text_area(
        "Quem deve assistir este vídeo?",
        value=persona,
        height=120,
    )

    st.markdown("---")
    st.header("🗣 Tom e voz da marca")

    tom_marca = canal.get(
        "tom_marca",
        "Direto, didático, com exemplos simples, evitando linguagem técnica em excesso.",
    )
    tom_custom = st.text_area(
        "Como o roteiro deve soar?",
        value=tom_marca,
        height=100,
    )

    st.markdown("---")
    st.header("⚠️ Restrições")
    proibidas = canal.get("palavras_proibidas", "")
    restricoes = st.text_area(
        "Palavras / temas a evitar",
        value=proibidas,
        height=80,
    )

# -------------------------------------------------------------------
# Modelo de IA (placeholder – aqui você pluga Groq / outro LLM)
# -------------------------------------------------------------------
def chamar_modelo_roteiro(prompt: str):
    """
    Esta função é um placeholder.
    Aqui você conecta a API do Groq, OpenAI, etc.
    Para fins de desenvolvimento, vamos só devolver um texto fake estruturado.
    """

    # Exemplo simples de retorno estruturado:
    texto = {
        "hook": "Você já se perguntou por que tantos canais não conseguem crescer mesmo postando todos os dias?",
        "promessa": "Neste vídeo, você vai entender um modelo simples para transformar qualquer ideia em um roteiro que realmente prende a atenção.",
        "estrutura": "Introdução rápida, explicação em 3 blocos, exemplo prático e chamada para ação no final.",
        "roteiro": {
            "Abertura": "Apresentação rápida + frase de impacto relacionada ao problema do público.",
            "Bloco 1 – Problema": "Mostrar o erro mais comum que as pessoas cometem.",
            "Bloco 2 – Solução": "Explicar o modelo ou passo a passo principal.",
            "Bloco 3 – Exemplo": "Aplicar o modelo a um caso prático.",
            "Encerramento": "Resumo + CTA clara (inscrever, comentar, próxima etapa).",
        },
    }
    return texto

# -------------------------------------------------------------------
# Área principal – edição do título e briefing
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
        "Estimativa de duração",
        ["5-7 min", "8-12 min", "13-20 min"],
        index=1,
    )

briefing = st.text_area(
    "Briefing adicional (opcional)",
    value=video.get("descricao", ""),
    height=120,
    help="Use para explicar o contexto específico, testemunho, produtos, história real, etc.",
)

# -------------------------------------------------------------------
# Geração do roteiro
# -------------------------------------------------------------------
st.subheader("⚙️ Geração do roteiro com IA")

col_bt1, col_bt2 = st.columns(2)

with col_bt1:
    if st.button("🚀 Gerar / regenerar roteiro completo", type="primary"):
        if not titulo_video.strip():
            st.warning("Informe ao menos um título para o vídeo.")
        else:
            with st.spinner("Gerando roteiro com IA..."):
                # Monta o prompt (poderia ser bem mais sofisticado)
                prompt = f"""
Você é um roteirista profissional de vídeos para YouTube.

Canal: {canal.get('nome','')}
Nicho: {canal.get('nicho','')}
Objetivo do vídeo: {objetivo}
Duração desejada: {duracao} ({dur_estimada})
Persona: {persona_custom}
Tom da marca: {tom_custom}
Restrições: {restricoes}

Título provisório: {titulo_video}

Briefing adicional:
{briefing}

Entregue:
- Um hook forte para os primeiros 10 segundos.
- Uma promessa clara do que a pessoa ganha assistindo.
- Uma descrição textual da estrutura do vídeo.
- Um roteiro dividido em seções nomeadas, com o texto de cada parte.
"""
                resultado = chamar_modelo_roteiro(prompt)

                # Atualiza artefatos
                video["artefatos"]["roteiro"] = {
                    "id": video["artefatos"]["roteiro"].get("id", str(uuid.uuid4())[:8]),
                    "titulo_video": titulo_video.strip(),
                    "hook": resultado.get("hook", ""),
                    "promessa": resultado.get("promessa", ""),
                    "estrutura": resultado.get("estrutura", ""),
                    "roteiro": resultado.get("roteiro", {}),
                    "tokens_uso": resultado.get("tokens", 0),
                    "modelo_usado": resultado.get("modelo", "mock-local"),
                    "gerado_em": datetime.now().isoformat(),
                }
                video["status"]["1_roteiro"] = True
                video["ultima_atualizacao"] = datetime.now().isoformat()
                st.success("Roteiro gerado e salvo para este vídeo.")
                st.rerun()

with col_bt2:
    if st.button("🗑 Limpar roteiro atual"):
        video["artefatos"]["roteiro"] = {
            "id": str(uuid.uuid4())[:8],
            "titulo_video": titulo_video.strip(),
            "hook": "",
            "promessa": "",
            "estrutura": "",
            "roteiro": {},
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
# Exibição / edição do roteiro salvo
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

st.markdown("---")
st.subheader("🧩 Seções do roteiro")

roteiro_secoes = dados.get("roteiro", {})

if not roteiro_secoes:
    st.info("Nenhuma seção de roteiro registrada ainda. Gere um roteiro ou escreva manualmente abaixo.")
    roteiro_secoes = {}

# Editor simples de seções
sec_nomes = list(roteiro_secoes.keys()) or ["Introdução", "Desenvolvimento", "Conclusão"]

tabs = st.tabs(sec_nomes)

for nome, tab in zip(sec_nomes, tabs):
    with tab:
        texto_secao = st.text_area(
            f"Texto da seção: {nome}",
            value=roteiro_secoes.get(nome, ""),
            height=220,
            key=f"secao_{nome}",
        )
        roteiro_secoes[nome] = texto_secao

if st.button("💾 Salvar alterações nas seções"):
    video["artefatos"]["roteiro"]["roteiro"] = roteiro_secoes
    video["artefatos"]["roteiro"]["titulo_video"] = titulo_video.strip()
    video["artefatos"]["roteiro"]["gerado_em"] = (
        video["artefatos"]["roteiro"]["gerado_em"] or datetime.now().isoformat()
    )
    video["status"]["1_roteiro"] = True
    video["ultima_atualizacao"] = datetime.now().isoformat()
    st.success("Roteiro atualizado para este vídeo.")

st.markdown("---")
st.caption(
    "Depois de estar satisfeito com o roteiro, siga para a página **2 – Thumbnails** "
    "para gerar as imagens de capa baseadas neste conteúdo."
)
