import streamlit as st
from groq import Groq
import json
import re
from datetime import datetime

st.set_page_config(page_title="1 – Roteiro Viral", layout="wide")
st.title("🎬 1 – Gerador de Roteiro Viral para YouTube")

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
# Cliente Groq
# -------------------------------------------------------------------
@st.cache_resource
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = get_groq_client()

# -------------------------------------------------------------------
# Sidebar – contexto do canal/vídeo e modelo
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📺 Contexto")

    st.markdown(f"**Canal:** {canal.get('nome','')}")
    st.markdown(f"**Vídeo:** {video.get('titulo','')}")

    st.markdown("---")
    st.header("⚙️ Modelo Groq")

    model = st.selectbox(
        "Modelo",
        [
            "llama-3.3-70b-versatile",  # recomendado
            "llama-3.1-8b-instant",     # mais rápido
        ],
        index=0,
    )

    temperatura = st.slider("Temperatura (criatividade)", 0.0, 1.0, 0.7, 0.1)

    nicho = canal.get("nicho", "")
    nicho = st.text_input("Nicho do canal", value=nicho)

    duracao = st.selectbox("Duração alvo", ["5-8 min", "8-12 min", "12-15 min"], index=1)

    tom_marca = canal.get("tom_marca", "Direto, motivacional, com humor leve.")
    tom_marca = st.text_area("Tom da marca", value=tom_marca, height=80)

# Campo para template de título vindo do Lab (opcional)
titulo_template = st.session_state.get("titulo_template", "")

# -------------------------------------------------------------------
# Função de geração
# -------------------------------------------------------------------
def gerar_roteiro_viral(tema, nicho, duracao, tom_marca, titulo_base=""):
    minutos = duracao.split("-")[0]

    prompt = f"""
Você é um roteirista profissional de YouTube, especialista em vídeos virais.

Canal:
- Nicho: {nicho}
- Tom da marca: {tom_marca}

Vídeo:
- Título base (opcional, pode melhorar): "{titulo_base or tema}"
- Tema: {tema}
- Duração desejada: {minutos} minutos

Objetivo:
Criar um roteiro COMPLETO e VIRAL para YouTube, estruturado e pronto para gravação.

REQUISITOS DE ESTILO:
- Linguagem simples, direta, conversacional (como amigo íntimo).
- Frases curtas (máx. ~15 palavras).
- Use pausas [PAUSA] e ênfases [ENFASE] quando fizer sentido.
- Evitar jargões técnicos pesados.
- Focar em benefício e curiosidade.

ESTRUTURA OBRIGATÓRIA DO ROTEIRO (use exatamente essas chaves):

1_GANCHO: Gancho inicial muito forte (30–45s) com curiosidade/choque/padrão quebrado.
2_REENGAJAMENTO_1: Reforço de curiosidade + promessa clara + micro-resumo.
3_PREPARACAO: História, contexto, identificação com o público, criar tensão.
4_CLIMAX: Entrega principal (segredos/dicas/passos) de forma clara e organizada.
5_REENGAJAMENTO_2: Novo gancho, prova social, reforço da transformação.
6_CONCLUSAO_CTA: Resumo rápido + CTAs poderosos (inscrever, like, comentário, próxima ação).

FORMATO DE RESPOSTA (JSON VÁLIDO):

{{
  "titulo_video": "Título otimizado e chamativo, com até ~70 caracteres",
  "descricao": "Primeiras linhas da descrição do vídeo otimizadas para clique",
  "tags": ["tag1", "tag2", "tag3"],
  "roteiro": {{
    "1_GANCHO": "texto do gancho...",
    "2_REENGAJAMENTO_1": "texto...",
    "3_PREPARACAO": "texto...",
    "4_CLIMAX": "texto...",
    "5_REENGAJAMENTO_2": "texto...",
    "6_CONCLUSAO_CTA": "texto..."
  }}
}}
"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperatura,
            max_tokens=4096,
        )
        conteudo = resp.choices[0].message.content.strip()

        # Tentar parsear JSON diretamente
        try:
            return json.loads(conteudo)
        except Exception:
            m = re.search(r"\{.*\}", conteudo, re.DOTALL)
            if m:
                return json.loads(m.group())
            return {"erro": "Falha ao converter resposta em JSON", "raw": conteudo}
    except Exception as e:
        return {"erro": str(e)}

# -------------------------------------------------------------------
# UI principal
# -------------------------------------------------------------------
st.subheader("📝 Configuração do vídeo")

col1, col2 = st.columns([2, 1])

with col1:
    tema = st.text_area(
        "Tema / ideia central do vídeo",
        value=video.get("titulo", ""),
        height=80,
        placeholder="Ex.: 7 segredos da renda passiva que ninguém conta",
    )

with col2:
    if titulo_template:
        st.markdown("**Template sugerido do Lab de Canais:**")
        st.code(titulo_template, language="text")
    else:
        st.caption("Nenhum template salvo ainda no Laboratório de Canais.")

if "roteiro_gerado" not in st.session_state:
    st.session_state.roteiro_gerado = None

col_bt1, col_bt2 = st.columns(2)
with col_bt1:
    if st.button("🚀 Gerar Roteiro Viral", type="primary"):
        if not tema.strip():
            st.warning("Informe pelo menos o tema do vídeo.")
        else:
            with st.spinner("Gerando roteiro com IA (Groq)..."):
                resultado = gerar_roteiro_viral(
                    tema=tema,
                    nicho=nicho,
                    duracao=duracao,
                    tom_marca=tom_marca,
                    titulo_base=video.get("titulo", "") or titulo_template,
                )
                st.session_state.roteiro_gerado = resultado

                # Se deu certo, salvar no "banco" do vídeo e marcar etapa 1 como concluída
                if resultado and "erro" not in resultado:
                    video["artefatos"]["roteiro"] = resultado
                    video["status"]["1_roteiro"] = True
                    video["ultima_atualizacao"] = datetime.now().isoformat()
                st.experimental_rerun()

with col_bt2:
    if st.button("🗑 Limpar roteiro atual"):
        st.session_state.roteiro_gerado = None
        video["artefatos"]["roteiro"] = None
        video["status"]["1_roteiro"] = False
        video["ultima_atualizacao"] = datetime.now().isoformat()
        st.experimental_rerun()

# Se já há roteiro salvo no vídeo, carregar em memória
if not st.session_state.roteiro_gerado and video.get("artefatos", {}).get("roteiro"):
    st.session_state.roteiro_gerado = video["artefatos"]["roteiro"]

roteiro = st.session_state.roteiro_gerado

st.markdown("---")

# -------------------------------------------------------------------
# Exibição do roteiro
# -------------------------------------------------------------------
st.subheader("📄 Roteiro gerado")

if roteiro and "erro" not in roteiro:
    titulo_final = roteiro.get("titulo_video", video.get("titulo", ""))
    descricao = roteiro.get("descricao", "")
    tags = roteiro.get("tags", [])
    partes = roteiro.get("roteiro", {})

    c_t1, c_t2 = st.columns([2, 1])
    with c_t1:
        st.markdown(f"### 🎥 {titulo_final}")
        st.caption(descricao)
    with c_t2:
        texto_download = f"Título: {titulo_final}\n\nDescrição:\n{descricao}\n\nRoteiro:\n\n"
        for secao, texto in partes.items():
            texto_download += f"{secao}\n{texto}\n\n"
        st.download_button(
            "💾 Baixar roteiro (.txt)",
            data=texto_download,
            file_name="roteiro_youtube.txt",
            mime="text/plain",
        )

    st.markdown("#### Estrutura do roteiro")
    for i, (secao, texto) in enumerate(partes.items(), start=1):
        with st.expander(f"{secao}", expanded=(i == 1)):
            st.markdown(texto)

    if tags:
        st.subheader("🏷 Tags sugeridas")
        st.code(", ".join(tags), language="text")
elif roteiro and "erro" in roteiro:
    st.error(f"❌ Erro ao gerar roteiro: {roteiro['erro']}")
    if "model_decommissioned" in roteiro["erro"]:
        st.info("O modelo foi descontinuado. Selecione outro modelo na barra lateral.")
else:
    st.info("Nenhum roteiro gerado ainda para este vídeo. Preencha o tema e clique em **Gerar Roteiro Viral**.")

st.markdown("---")
st.caption(
    "Após finalizar o roteiro, volte ao **Monitor de Produção** para acompanhar "
    "as próximas etapas (Thumbnails, Áudio, Vídeo, Publicação)."
)
