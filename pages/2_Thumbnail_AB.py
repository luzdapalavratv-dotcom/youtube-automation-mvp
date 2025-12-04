import streamlit as st
import requests
import io
from PIL import Image
import random
from datetime import datetime

st.set_page_config(page_title="2 – Thumbnail A/B/C", layout="wide")
st.title("🖼 2 – Gerador de Thumbnails A/B/C para YouTube")

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
# Session state local dessa página
# -------------------------------------------------------------------
defaults = {
    "thumbnail_a": None,
    "thumbnail_b": None,
    "thumbnail_c": None,
    "prompt_a": "",
    "prompt_b": "",
    "prompt_c": "",
    "vencedor_thumb": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Garante estrutura de thumbs no artefato do vídeo
if "thumbs" not in video["artefatos"] or video["artefatos"]["thumbs"] is None:
    video["artefatos"]["thumbs"] = {
        "img_a": None,
        "img_b": None,
        "img_c": None,
        "prompt_a": "",
        "prompt_b": "",
        "prompt_c": "",
        "vencedor": None,
        "experimentos": [],
    }

# -------------------------------------------------------------------
# Sidebar – contexto e opções
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📺 Contexto")

    st.markdown(f"**Canal:** {canal.get('nome','')}")
    st.markdown(f"**Vídeo:** {video.get('titulo','')}")

    st.markdown("---")
    st.header("🎯 Estratégia da Thumbnail")

    estrategia = st.selectbox(
        "Estratégia visual",
        [
            "Emocional (rosto+expressão forte)",
            "Curiosidade (mistério/números)",
            "Contraste (antes/depois)",
            "Luxo (produtos/patrimônio)",
        ],
    )

    qualidade = st.selectbox(
        "Modelo Pollinations",
        ["flux", "turbo", "stable-diffusion"],
        index=0,
    )

    cores = st.multiselect(
        "Esquema de cores sugerido",
        ["Vermelho/Branco", "Azul/Dourado", "Preto/Amarelo", "Verde/Branco", "Roxo/Branco"],
        default=["Vermelho/Branco"],
    )

    st.markdown("---")
    st.header("🔤 Texto na Thumbnail")

    modo_texto = st.selectbox(
        "Tipo de texto na imagem",
        [
            "Imagem limpa (sem texto)",
            "Pouco texto (título curto)",
            "Muito texto (título grande)",
        ],
        index=1,
    )

    st.markdown("---")
    st.header("😊 Expressão emocional")

    expressao = st.selectbox(
        "Expressão principal",
        ["Chocado(a)", "Feliz", "Sério", "Misterioso", "Bravo(a)"],
        index=0,
    )

    st.markdown("---")
    st.header("🧪 Experimento")

    nome_experimento = st.text_input(
        "Nome do experimento A/B/C",
        value=f"Thumb {datetime.now().strftime('%d/%m %H:%M')}",
    )

# -------------------------------------------------------------------
# Funções auxiliares
# -------------------------------------------------------------------
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


def montar_descricao_texto(titulo: str):
    base = titulo or "YouTube video"
    if modo_texto.startswith("Imagem limpa"):
        return "no text, clean composition, focus only on subject and background"
    if modo_texto.startswith("Pouco texto"):
        return f"short bold text '{base[:18]}', large readable font, few words"
    return f"large bold text '{base[:28]}', big title, multiple words, still highly readable"


def montar_expressao():
    if expressao == "Chocado(a)":
        return "shocked expression, wide open eyes, strong emotion"
    if expressao == "Feliz":
        return "happy smiling face, positive energy"
    if expressao == "Sério":
        return "serious face, focused, intense look"
    if expressao == "Misterioso":
        return "mysterious look, half shadows, intrigue"
    if expressao == "Bravo(a)":
        return "angry face, intense, confrontational"
    return ""


def montar_cores():
    if not cores:
        return "high contrast color palette"
    return ", ".join(cores) + " color palette, high contrast"


def criar_prompt(titulo: str, estrategia: str, variante: str = ""):
    base = titulo or video.get("titulo", "") or "viral YouTube video"
    texto_instr = montar_descricao_texto(base)
    expr = montar_expressao()
    cores_txt = montar_cores()

    if estrategia.startswith("Emocional"):
        core = (
            f"closeup human face, {expr}, {texto_instr}, "
            "cinematic lighting, depth of field, highly detailed, "
            f"{cores_txt}, composition optimized for YouTube thumbnail"
        )
    elif estrategia.startswith("Curiosidade"):
        core = (
            f"scene that creates curiosity about {base}, maybe a big number or object, "
            f"{texto_instr}, {cores_txt}, dramatic lighting, cinematic, mystery vibe"
        )
    elif estrategia.startswith("Contraste"):
        core = (
            f"split screen before and after transformation related to {base}, "
            f"{texto_instr}, {cores_txt}, strong contrast left vs right, bold layout"
        )
    elif estrategia.startswith("Luxo"):
        core = (
            f"luxury and wealth concept related to {base}, gold lighting, reflections, "
            f"{texto_instr}, {cores_txt}, cinematic, professional photo"
        )
    else:
        core = (
            f"youtube thumbnail about {base}, {texto_instr}, {cores_txt}, cinematic lighting"
        )

    if variante:
        core += f", {variante}"

    return core

# -------------------------------------------------------------------
# Interface principal
# -------------------------------------------------------------------
st.subheader("📝 Conteúdo base")

titulo_base = video.get("titulo", "")
novo_titulo = st.text_input(
    "Texto base (usado no prompt, se houver texto na imagem)",
    value=titulo_base[:60] if titulo_base else "Exemplo de Thumbnail Viral",
)

# -------------------------------------------------------------------
# Geração A / B / C + delete
# -------------------------------------------------------------------
st.subheader("⚙️ Geração das variações")

col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button("🎨 Gerar A"):
        with st.spinner("Gerando Thumbnail A..."):
            prompt_a = criar_prompt(novo_titulo, estrategia, "version A")
            img_a = gerar_thumbnail_pollinations(prompt_a, model=qualidade)
            if img_a:
                st.session_state.thumbnail_a = img_a
                st.session_state.prompt_a = prompt_a
                st.session_state.vencedor_thumb = None
                st.success("Thumbnail A gerada!")
            else:
                st.error("Falha ao gerar Thumbnail A.")
    if st.button("🗑 Apagar A"):
        st.session_state.thumbnail_a = None
        st.session_state.prompt_a = ""
        st.success("Thumbnail A apagada.")

with col_b:
    if st.button("🖼 Gerar B"):
        with st.spinner("Gerando Thumbnail B..."):
            prompt_b = criar_prompt(
                novo_titulo, estrategia, "different camera angle, version B"
            )
            img_b = gerar_thumbnail_pollinations(prompt_b, model=qualidade)
            if img_b:
                st.session_state.thumbnail_b = img_b
                st.session_state.prompt_b = prompt_b
                st.session_state.vencedor_thumb = None
                st.success("Thumbnail B gerada!")
            else:
                st.error("Falha ao gerar Thumbnail B.")
    if st.button("🗑 Apagar B"):
        st.session_state.thumbnail_b = None
        st.session_state.prompt_b = ""
        st.success("Thumbnail B apagada.")

with col_c:
    if st.button("🧪 Gerar C"):
        with st.spinner("Gerando Thumbnail C..."):
            prompt_c = criar_prompt(
                novo_titulo, estrategia, "different background, version C"
            )
            img_c = gerar_thumbnail_pollinations(prompt_c, model=qualidade)
            if img_c:
                st.session_state.thumbnail_c = img_c
                st.session_state.prompt_c = prompt_c
                st.session_state.vencedor_thumb = None
                st.success("Thumbnail C gerada!")
            else:
                st.error("Falha ao gerar Thumbnail C.")
    if st.button("🗑 Apagar C"):
        st.session_state.thumbnail_c = None
        st.session_state.prompt_c = ""
        st.success("Thumbnail C apagada.")

# -------------------------------------------------------------------
# Preview pequeno
# -------------------------------------------------------------------
st.subheader("👁️ Preview rápido (miniaturas)")

p1, p2, p3 = st.columns(3)
with p1:
    st.caption("Preview A")
    if isinstance(st.session_state.thumbnail_a, Image.Image):
        st.image(st.session_state.thumbnail_a, width=120)
    else:
        st.text("Sem A")

with p2:
    st.caption("Preview B")
    if isinstance(st.session_state.thumbnail_b, Image.Image):
        st.image(st.session_state.thumbnail_b, width=120)
    else:
        st.text("Sem B")

with p3:
    st.caption("Preview C")
    if isinstance(st.session_state.thumbnail_c, Image.Image):
        st.image(st.session_state.thumbnail_c, width=120)
    else:
        st.text("Sem C")

st.markdown("---")

# -------------------------------------------------------------------
# Exibição grande + votação
# -------------------------------------------------------------------
st.subheader("👀 Teste A/B/C – escolha a vencedora")

img_a = st.session_state.thumbnail_a
img_b = st.session_state.thumbnail_b
img_c = st.session_state.thumbnail_c

g1, g2, g3 = st.columns(3)
with g1:
    st.markdown("### A")
    if isinstance(img_a, Image.Image):
        st.image(img_a, use_column_width=True)
        if st.session_state.prompt_a:
            st.caption(st.session_state.prompt_a[:110] + "...")
    else:
        st.info("Gere a opção A.")
    if st.button("⭐ Voto A", key="vote_a"):
        if isinstance(img_a, Image.Image):
            st.session_state.vencedor_thumb = "A"
            st.success("A marcada como vencedora.")
        else:
            st.warning("Gere a A primeiro.")

with g2:
    st.markdown("### B")
    if isinstance(img_b, Image.Image):
        st.image(img_b, use_column_width=True)
        if st.session_state.prompt_b:
            st.caption(st.session_state.prompt_b[:110] + "...")
    else:
        st.info("Gere a opção B.")
    if st.button("⭐ Voto B", key="vote_b"):
        if isinstance(img_b, Image.Image):
            st.session_state.vencedor_thumb = "B"
            st.success("B marcada como vencedora.")
        else:
            st.warning("Gere a B primeiro.")

with g3:
    st.markdown("### C")
    if isinstance(img_c, Image.Image):
        st.image(img_c, use_column_width=True)
        if st.session_state.prompt_c:
            st.caption(st.session_state.prompt_c[:110] + "...")
    else:
        st.info("Gere a opção C.")
    if st.button("⭐ Voto C", key="vote_c"):
        if isinstance(img_c, Image.Image):
            st.session_state.vencedor_thumb = "C"
            st.success("C marcada como vencedora.")
        else:
            st.warning("Gere a C primeiro.")

# -------------------------------------------------------------------
# CTR estimado e anotação de CTR real
# -------------------------------------------------------------------
st.subheader("📈 CTR estimado (simulado) + CTR real")

if st.session_state.vencedor_thumb in ["A", "B", "C"]:
    ctr_estimado = random.uniform(8.5, 15.2)
    col_ce1, col_ce2 = st.columns(2)
    with col_ce1:
        st.metric("CTR estimado", f"{ctr_estimado:.1f}%", "↑ 2.3%")
    with col_ce2:
        ctr_real = st.text_input(
            "Opcional: CTR real observado no YouTube Studio (%)",
            placeholder="Ex.: 9.8",
        )
        st.caption("Preencha depois que o vídeo rodar um tempo para comparar.")
else:
    st.caption("Escolha A, B ou C como vencedora para ver a CTR estimada.")

# -------------------------------------------------------------------
# Salvar no artefato do vídeo + histórico
# -------------------------------------------------------------------
st.subheader("💾 Salvar resultado no vídeo")

if st.button("Salvar thumbs no vídeo"):
    thumbs = video["artefatos"]["thumbs"]
    thumbs["img_a"] = st.session_state.thumbnail_a
    thumbs["img_b"] = st.session_state.thumbnail_b
    thumbs["img_c"] = st.session_state.thumbnail_c
    thumbs["prompt_a"] = st.session_state.prompt_a
    thumbs["prompt_b"] = st.session_state.prompt_b
    thumbs["prompt_c"] = st.session_state.prompt_c
    thumbs["vencedor"] = st.session_state.vencedor_thumb

    thumbs["experimentos"].append(
        {
            "nome": nome_experimento,
            "vencedor": st.session_state.vencedor_thumb,
            "modo_texto": modo_texto,
            "estrategia": estrategia,
            "expressao": expressao,
            "modelo": qualidade,
            "titulo_base": novo_titulo,
            "data": datetime.now().isoformat(),
        }
    )

    # Marca etapa 2 como concluída se houver ao menos uma thumb
    if any(isinstance(x, Image.Image) for x in [img_a, img_b, img_c]):
        video["status"]["2_thumbnail"] = True
    video["ultima_atualizacao"] = datetime.now().isoformat()

    st.success("Thumbnails salvas no vídeo e etapa 2 marcada como concluída.")

# Mostrar histórico de experimentos salvos para este vídeo
hist = video["artefatos"]["thumbs"].get("experimentos", [])[-5:]
if hist:
    st.subheader("🖼 Histórico de experimentos deste vídeo")
    for item in reversed(hist):
        st.markdown(
            f"**Experimento:** {item.get('nome','')}  \n"
            f"**Vencedor:** {item.get('vencedor','N/A')}  |  "
            f"**Texto:** {item.get('modo_texto','')}  |  "
            f"**Estratégia:** {item.get('estrategia','')}  |  "
            f"**Expressão:** {item.get('expressao','')}"
        )
        st.caption(f"Data: {item.get('data','')[:16]}")
        st.divider()

st.markdown("---")
st.caption(
    "Após escolher a melhor thumbnail e salvar, volte ao **Monitor de Produção** "
    "para acompanhar as próximas etapas (Áudio, Vídeo, Publicação)."
)
