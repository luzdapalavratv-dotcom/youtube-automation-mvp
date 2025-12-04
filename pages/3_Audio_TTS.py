import streamlit as st
import asyncio
import edge_tts
import subprocess
import os
from datetime import datetime

st.set_page_config(page_title="3 – Áudio TTS", layout="wide")
st.title("🎙 3 – Gerador de Áudio TTS para o Vídeo")

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

# Garante estrutura de artefatos
if "artefatos" not in video:
    video["artefatos"] = {}
if "audio_path" not in video["artefatos"]:
    video["artefatos"]["audio_path"] = None
if "audio_info" not in video["artefatos"]:
    video["artefatos"]["audio_info"] = {}

roteiro = video["artefatos"].get("roteiro")

# -------------------------------------------------------------------
# Sidebar – motor de voz, voz e configurações
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📺 Contexto")
    st.markdown(f"**Canal:** {canal.get('nome','')}")
    st.markdown(f"**Vídeo:** {video.get('titulo','')}")

    st.markdown("---")
    st.header("🎛 Motor de voz")

    motor = st.selectbox(
        "Motor TTS",
        ["Edge-TTS (online)", "Piper TTS (local)"],
        index=0,
        help="Edge usa o serviço online da Microsoft; Piper é TTS local via binário `piper`.",
    )

    if motor == "Edge-TTS (online)":
        st.markdown("**Voz TTS (Edge-TTS)**")

        vozes_edge = {
            "🇺🇸 English (US) – Female": "en-US-JennyNeural",
            "🇺🇸 English (US) – Male": "en-US-GuyNeural",
            "🇧🇷 Português (BR) – Female": "pt-BR-FranciscaNeural",
            "🇧🇷 Português (BR) – Male": "pt-BR-AntonioNeural",
            "🇪🇸 Español (ES) – Female": "es-ES-ElviraNeural",
            "🇪🇸 Español (MX) – Female": "es-MX-DaliaNeural",
        }
        voz_label = st.selectbox("Voz", list(vozes_edge.keys()), index=2)
        voz_code = vozes_edge[voz_label]

        velocidade = st.slider("Velocidade (rate)", 0.5, 1.5, 1.0, 0.1)
        st.caption(
            "Edge-TTS usa vozes neurais online da Microsoft; aqui é usado apenas o controle de velocidade."
        )  # [web:184][web:185]

    else:
        st.markdown("**Modelo Piper TTS (local)**")

        # Caminho padrão bem explícito; ideal é setar PIPER_MODEL_PATH no ambiente
        default_model = os.environ.get(
            "PIPER_MODEL_PATH",
            "/usr/local/share/piper-voices/pt_BR-faber-medium.onnx",
        )  # [web:252][web:263]

        modelo_piper = st.text_input(
            "Caminho do modelo .onnx",
            value=default_model,
            help=(
                "Baixe um modelo pt_BR do repositório rhasspy/piper-voices e informe o caminho "
                "completo para o arquivo .onnx (o .onnx.json deve ficar na mesma pasta)."
            ),
        )

        voz_label = f"Piper – {os.path.basename(modelo_piper) or 'modelo não definido'}"
        voz_code = modelo_piper
        velocidade = 1.0

        st.caption(
            "Piper é TTS neural local. É preciso ter o executável `piper` instalado no PATH "
            "e o modelo .onnx + .onnx.json presentes no caminho informado."
        )  # [web:223][web:252]

# -------------------------------------------------------------------
# TTS Edge
# -------------------------------------------------------------------
async def gerar_audio_edge_tts(texto: str, voz: str, output_path: str, rate: float) -> None:
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("Texto vazio para TTS (Edge).")

    rate_percent = max(-50, min(50, int((rate - 1.0) * 100)))
    rate_str = f"{rate_percent:+d}%"

    ssml = f"""
<speak version="1.0" xml:lang="pt-BR">
  <prosody rate="{rate_str}">
    {texto}
  </prosody>
</speak>
""".strip()

    communicate = edge_tts.Communicate(ssml, voz)
    await communicate.save(output_path)


def run_tts_edge(texto: str, voz: str, rate: float) -> str | None:
    import tempfile

    texto = (texto or "").strip()
    if not texto:
        st.error("Texto vazio para TTS.")
        return None

    if len(texto) > 8000:
        texto = texto[:8000]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        output_path = tmp.name

    try:
        loop.run_until_complete(gerar_audio_edge_tts(texto, voz, output_path, rate))
        return output_path
    except Exception as e:
        st.error(f"Erro ao gerar áudio com Edge-TTS: {e}")
        return None
    finally:
        loop.close()

# -------------------------------------------------------------------
# TTS Piper (CLI)
# -------------------------------------------------------------------
def piper_disponivel() -> bool:
    from shutil import which
    return which("piper") is not None  # [web:226]


def run_tts_piper(texto: str, modelo_onnx: str) -> str | None:
    import tempfile

    texto = (texto or "").strip()
    if not texto:
        st.error("Texto vazio para TTS.")
        return None

    if not modelo_onnx:
        st.error("Nenhum caminho de modelo Piper informado.")
        return None

    if not os.path.exists(modelo_onnx):
        st.error(
            f"Modelo Piper não encontrado: {modelo_onnx}\n"
            "Baixe um modelo pt_BR (ex.: pt_BR-faber-medium.onnx) e ajuste o caminho na sidebar."
        )  # [web:252][web:263]
        return None

    if not piper_disponivel():
        st.error(
            "O comando `piper` não foi encontrado no sistema. "
            "Instale o binário Piper e coloque-o no PATH do sistema."
        )  # [web:223][web:226]
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        output_path = tmp.name

    cmd = [
        "piper",
        "--model",
        modelo_onnx,
        "--output_file",
        output_path,
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=texto.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            st.error("Erro ao executar Piper TTS.")
            st.code(proc.stderr.decode("utf-8")[-2000:], language="bash")
            return None
        return output_path
    except FileNotFoundError:
        st.error("Comando `piper` não encontrado (FileNotFoundError).")
        return None
    except Exception as e:
        st.error(f"Erro ao gerar áudio com Piper TTS: {e}")
        return None

# -------------------------------------------------------------------
# Texto base
# -------------------------------------------------------------------
st.subheader("📝 Texto que será narrado")

if roteiro and isinstance(roteiro, dict) and "roteiro" in roteiro:
    secoes = roteiro["roteiro"]
    secoes_nomes = list(secoes.keys())
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        secao_sel = st.selectbox("Escolha uma seção do roteiro para ouvir/editar", secoes_nomes)
    with col_s2:
        concatenar_todas = st.checkbox("Usar ROTEIRO COMPLETO (todas as seções)", value=False)

    if concatenar_todas:
        texto_base = ""
        for s, t in secoes.items():
            texto_base += f"[{s}]\n{t}\n\n"
    else:
        texto_base = secoes.get(secao_sel, "")
else:
    st.info("Nenhum roteiro salvo para este vídeo. Você pode colar um texto manualmente abaixo.")
    texto_base = ""

texto_manual = st.text_area(
    "Texto para narração (você pode editar o texto da seção ou colar algo completamente diferente)",
    value=texto_base,
    height=250,
)

# -------------------------------------------------------------------
# Geração do áudio
# -------------------------------------------------------------------
st.subheader("🎙 Gerar áudio")

col_g1, col_g2 = st.columns(2)
with col_g1:
    if st.button("🚀 Gerar áudio TTS", type="primary"):
        texto_limpo = (texto_manual or "").strip()
        if not texto_limpo:
            st.warning("Texto vazio. Preencha antes de gerar.")
        else:
            with st.spinner(f"Gerando áudio com {motor}..."):
                if motor == "Edge-TTS (online)":
                    audio_path = run_tts_edge(texto_limpo, voz_code, velocidade)
                else:
                    audio_path = run_tts_piper(texto_limpo, voz_code)

                if audio_path and os.path.exists(audio_path):
                    video["artefatos"]["audio_path"] = audio_path
                    video["artefatos"]["audio_info"] = {
                        "motor": motor,
                        "voz": voz_label,
                        "voz_code": voz_code,
                        "velocidade": velocidade if motor.startswith("Edge") else 1.0,
                        "gerado_em": datetime.now().isoformat(),
                        "texto_usado": texto_limpo[:5000],
                    }
                    video["status"]["3_audio"] = True
                    video["ultima_atualizacao"] = datetime.now().isoformat()
                    st.success("Áudio gerado e salvo no vídeo (etapa 3 concluída).")
with col_g2:
    if st.button("🗑 Remover áudio deste vídeo"):
        video["artefatos"]["audio_path"] = None
        video["artefatos"]["audio_info"] = {}
        video["status"]["3_audio"] = False
        video["ultima_atualizacao"] = datetime.now().isoformat()
        st.success("Áudio removido deste vídeo.")

st.markdown("---")

# -------------------------------------------------------------------
# Player e download
# -------------------------------------------------------------------
st.subheader("🎧 Player do áudio gerado")

audio_path_salvo = video["artefatos"].get("audio_path")

if audio_path_salvo and os.path.exists(audio_path_salvo):
    st.audio(audio_path_salvo)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        ext = ".mp3" if audio_path_salvo.lower().endswith(".mp3") else ".wav"
        mime = "audio/mpeg" if ext == ".mp3" else "audio/wav"
        with open(audio_path_salvo, "rb") as f:
            st.download_button(
                "💾 Baixar áudio",
                data=f.read(),
                file_name=f"audio_{video.get('titulo','video')[:20]}{ext}",
                mime=mime,
            )
    with col_d2:
        info = video["artefatos"].get("audio_info", {})
        st.markdown("**Configurações usadas:**")
        st.caption(
            f"Motor: {info.get('motor','-')}  \n"
            f"Voz: {info.get('voz','-')}  \n"
            f"Velocidade: {info.get('velocidade','-')}x"
        )
else:
    st.info("Nenhum áudio disponível ainda para este vídeo. Gere um áudio acima.")

st.markdown("---")
st.caption(
    "Após gerar o áudio TTS e salvar, volte ao **Monitor de Produção** "
    "para seguir para a etapa 4 (montagem do vídeo)."
)
