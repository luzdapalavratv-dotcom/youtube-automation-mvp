import streamlit as st
import requests
import io
from PIL import Image
import random

st.set_page_config(page_title="2_Thumbnail_AB", layout="wide")
st.title("🖼️ Gerador de Thumbnails A/B Testing")

# --------------------------------------------------------------------
# Session state inicial
# --------------------------------------------------------------------
if "roteiro_gerado" not in st.session_state or st.session_state.roteiro_gerado is None:
    st.session_state.roteiro_gerado = {"titulo_video": "", "roteiro": {}}

if "thumbnail_a" not in st.session_state:
    st.session_state.thumbnail_a = None
if "thumbnail_b" not in st.session_state:
    st.session_state.thumbnail_b = None
if "prompt_a" not in st.session_state:
    st.session_state.prompt_a = ""
if "prompt_b" not in st.session_state:
    st.session_state.prompt_b = ""
if "vencedor" not in st.session_state:
    st.session_state.vencedor = None
if "thumbnails_historico" not in st.session_state:
    st.session_state.thumbnails_historico = []

# --------------------------------------------------------------------
# Sidebar configurações
# --------------------------------------------------------------------
with st.sidebar:
    st.header("🎯 Estratégias de Thumbnail")

    estrategia = st.selectbox(
        "Estratégia A/B",
        [
            "Emocional (rosto+texto)",
            "Curiosidade (números)",
            "Contraste (antes/depois)",
            "Luxo (produtos)",
        ],
    )

    qualidade = st.selectbox(
        "Modelo/qualidade (Pollinations)",
        ["flux", "turbo", "stable-diffusion"],
        index=0,
    )

    cores = st.multiselect(
        "Esquema de cores",
        ["Vermelho/Branco", "Azul/Dourado", "Preto/Amarelo", "Verde/Branco"],
        default=["Vermelho/Branco"],
    )

    st.markdown("---")
    st.header("🔤 Texto na thumbnail")
    incluir_texto = st.radio(
        "Adicionar texto escrito na thumbnail?",
        ["Com texto", "Sem texto"],
        index=0,
    )
    usar_texto = incluir_texto == "Com texto"

# --------------------------------------------------------------------
# Funções de geração
# --------------------------------------------------------------------
def gerar_thumbnail_pollinations(prompt, width=1280, height=720, model="flux"):
    """Gera thumbnail via Pollinations.ai (retorna PIL.Image ou None)."""
    url = (
        f"https://image.pollinations.ai/prompt/{prompt}"
        f"?width={width}&height={height}&model={model}&nologo=true&enhance=true"
    )
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            return Image.open(io.BytesIO(resp.content))
        return None
    except Exception:
        return None


def criar_prompts_thumbnail(roteiro_titulo, estrategia, usar_texto: bool, variante: str = ""):
    base = roteiro_titulo or "Vídeo viral YouTube"

    # Parte de texto (opcional)
    if usar_texto:
        texto_snippet = f"with bold text '{base[:30]}'"
    else:
        texto_snippet = "no text, focus only on image composition"

    if estrategia.startswith("Emocional"):
        core = (
            f"closeup dramatic face shocked expression, {texto_snippet}, "
            "youtube thumbnail, red background, high contrast, cinematic lighting"
        )
    elif estrategia.startswith("Curiosidade"):
        core = (
            f"mysterious scene, big number, {texto_snippet}, "
            "yellow and black high contrast, viral youtube thumbnail, 3d style"
        )
    elif estrategia.startswith("Contraste"):
        core = (
            f"split screen before and after dramatic transformation, {texto_snippet}, "
            "strong contrast colors, bold composition, youtube thumbnail"
        )
    elif estrategia.startswith("Luxo"):
        core = (
            f"luxury style, gold lighting, wealth or success concept, {texto_snippet}, "
            "black and gold colors, professional cinematic look"
        )
    else:
        core = (
            f"youtube thumbnail, {texto_snippet}, "
            "high contrast, bold composition, cinematic lighting"
        )

    if variante:
        core += f", {variante}"

    return core

# --------------------------------------------------------------------
# Interface principal
# --------------------------------------------------------------------
col1, col2 = st.columns([1.5, 1])

with col1:
    st.header("🎬 Roteiro Selecionado")

    roteiro = st.session_state.roteiro_gerado or {}
    titulo_base = roteiro.get("titulo_video", "")

    if titulo_base:
        st.markdown(f"### **{titulo_base}**")
        novo_titulo = st.text_input(
            "Editar título para thumbnail",
            value=titulo_base[:50],
        )
    else:
        novo_titulo = st.text_input(
            "Título do vídeo",
            "Exemplo de Thumbnail Viral",
        )

with col2:
    st.header("⚙️ Configuração Atual")
    st.info(f"**Estratégia:** {estrategia}")
    st.info(f"**Modelo:** {qualidade}")
    st.info(f"**Cores:** {', '.join(cores) if cores else 'Padrão'}")
    st.info(f"**Texto na thumbnail:** {'Com texto' if usar_texto else 'Sem texto'}")

# --------------------------------------------------------------------
# Botões de geração A / B
# --------------------------------------------------------------------
col_a, col_b, _ = st.columns([1, 1, 1])

with col_a:
    if st.button("🎨 Gerar Thumbnail A", type="primary"):
        with st.spinner("Gerando Thumbnail A com IA..."):
            prompt_a = criar_prompts_thumbnail(novo_titulo, estrategia, usar_texto)
            img_a = gerar_thumbnail_pollinations(prompt_a, model=qualidade)
            if img_a:
                st.session_state.thumbnail_a = img_a
                st.session_state.prompt_a = prompt_a
                st.session_state.vencedor = None
                st.success("Thumbnail A gerada!")
            else:
                st.error("Falha ao gerar Thumbnail A. Tente novamente.")

with col_b:
    if st.button("🖼️ Gerar Thumbnail B", type="secondary"):
        with st.spinner("Gerando Thumbnail B com IA..."):
            prompt_b = criar_prompts_thumbnail(
                novo_titulo, estrategia, usar_texto, "different angle, more dramatic"
            )
            img_b = gerar_thumbnail_pollinations(prompt_b, model=qualidade)
            if img_b:
                st.session_state.thumbnail_b = img_b
                st.session_state.prompt_b = prompt_b
                st.session_state.vencedor = None
                st.success("Thumbnail B gerada!")
            else:
                st.error("Falha ao gerar Thumbnail B. Tente novamente.")

# --------------------------------------------------------------------
# PREVIEW RÁPIDO
# --------------------------------------------------------------------
st.subheader("👁️ Preview rápido (miniaturas)")

prev_col_a, prev_col_b = st.columns(2)

with prev_col_a:
    st.caption("Preview A")
    if isinstance(st.session_state.thumbnail_a, Image.Image):
        st.image(st.session_state.thumbnail_a, width=120)
    else:
        st.text("Sem imagem A")

with prev_col_b:
    st.caption("Preview B")
    if isinstance(st.session_state.thumbnail_b, Image.Image):
        st.image(st.session_state.thumbnail_b, width=120)
    else:
        st.text("Sem imagem B")

st.markdown("---")

# --------------------------------------------------------------------
# Exibição A/B grande + votação
# --------------------------------------------------------------------
st.header("👀 Teste A/B – escolha a melhor")

img_a = st.session_state.thumbnail_a
img_b = st.session_state.thumbnail_b

if isinstance(img_a, Image.Image) or isinstance(img_b, Image.Image):
    c_img1, c_img2, c_vote = st.columns([1, 1, 1])

    with c_img1:
        st.subheader("Thumbnail A (grande)")
        if isinstance(img_a, Image.Image):
            st.image(img_a, use_column_width=True)
            if st.session_state.prompt_a:
                st.caption(st.session_state.prompt_a[:90] + "...")
        else:
            st.info("Ainda não gerada.")

        if st.button("⭐ Voto A (melhor CTR)", key="voto_a"):
            if isinstance(img_a, Image.Image):
                st.session_state.vencedor = "A"
                st.success("Thumbnail A marcada como vencedora.")
            else:
                st.warning("Gere a Thumbnail A primeiro.")

    with c_img2:
        st.subheader("Thumbnail B (grande)")
        if isinstance(img_b, Image.Image):
            st.image(img_b, use_column_width=True)
            if st.session_state.prompt_b:
                st.caption(st.session_state.prompt_b[:90] + "...")
        else:
            st.info("Ainda não gerada.")

        if st.button("⭐ Voto B (melhor CTR)", key="voto_b"):
            if isinstance(img_b, Image.Image):
                st.session_state.vencedor = "B"
                st.success("Thumbnail B marcada como vencedora.")
            else:
                st.warning("Gere a Thumbnail B primeiro.")

    # Downloads
    st.subheader("💾 Download das imagens")

    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        if isinstance(img_a, Image.Image):
            buf_a = io.BytesIO()
            img_a.save(buf_a, format="PNG")
            st.download_button(
                "📥 Download A",
                data=buf_a.getvalue(),
                file_name=f"thumbnail_A_{novo_titulo[:20]}.png",
                mime="image/png",
            )
    with c_dl2:
        if isinstance(img_b, Image.Image):
            buf_b = io.BytesIO()
            img_b.save(buf_b, format="PNG")
            st.download_button(
                "📥 Download B",
                data=buf_b.getvalue(),
                file_name=f"thumbnail_B_{novo_titulo[:20]}.png",
                mime="image/png",
            )
else:
    st.info("Gere pelo menos uma thumbnail A ou B para iniciar o teste A/B.")

# --------------------------------------------------------------------
# CTR estimado
# --------------------------------------------------------------------
st.subheader("📈 Previsão de CTR (simulada)")
if st.session_state.vencedor in ["A", "B"]:
    ctr_estimado = random.uniform(8.5, 15.2)
    st.metric("CTR estimado", f"{ctr_estimado:.1f}%", "↑ 2.3%")
else:
    st.caption("Escolha um vencedor A ou B para ver uma previsão simulada de CTR.")

# --------------------------------------------------------------------
# Histórico de thumbnails
# --------------------------------------------------------------------
st.subheader("🖼️ Histórico recente")

if st.button("➡️ Salvar no histórico atual"):
    if isinstance(img_a, Image.Image) or isinstance(img_b, Image.Image):
        st.session_state.thumbnails_historico.append(
            {
                "titulo": novo_titulo,
                "img_a": img_a if isinstance(img_a, Image.Image) else None,
                "img_b": img_b if isinstance(img_b, Image.Image) else None,
                "vencedor": st.session_state.vencedor,
                "usar_texto": usar_texto,
            }
        )
        st.success("Salvo no histórico.")
    else:
        st.warning("Gere pelo menos uma thumbnail antes de salvar.")

hist = st.session_state.thumbnails_historico[-4:]

if hist:
    for i, thumb in enumerate(hist):
        st.markdown(f"**{thumb.get('titulo','')[:40]}...**")
        c1, c2 = st.columns(2)
        with c1:
            if isinstance(thumb.get("img_a"), Image.Image):
                st.image(thumb["img_a"], width=200)
            else:
                st.caption("A: (sem imagem)")
        with c2:
            if isinstance(thumb.get("img_b"), Image.Image):
                st.image(thumb["img_b"], width=200)
            else:
                st.caption("B: (sem imagem)")
        st.caption(f"Vencedor: {thumb.get('vencedor', 'N/A')} | Texto: {'Sim' if thumb.get('usar_texto') else 'Não'}")
        st.divider()

st.markdown("---")
st.caption("Próxima etapa: 3_Audio_TTS.py – gerar áudio para o roteiro selecionado.")
