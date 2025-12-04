import streamlit as st
from groq import Groq
import json
import re

st.set_page_config(page_title="1_Roteiro_Viral", layout="wide")
st.title("🎬 Gerador de Roteiro Viral para YouTube")

# Cliente Groq
@st.cache_resource
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = get_groq_client()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")

    # MODELOS ATUALIZADOS (sem modelos deprecados)
    model = st.selectbox(
        "Modelo Groq",
        [
            "llama-3.3-70b-versatile",  # substitui o antigo 70B
            "llama-3.1-8b-instant",     # leve e rápido
        ],
        index=0,
    )

    temperatura = st.slider("Temperatura (criatividade)", 0.0, 1.0, 0.7, 0.1)

    nicho = st.selectbox(
        "Nicho do canal",
        ["Motivação", "Finanças", "Saúde", "Tecnologia", "Religião", "Negócios", "Educação"],
    )

    duracao = st.selectbox("Duração alvo", ["5-8 min", "8-12 min", "12-15 min"], index=1)

# Session state
if "roteiro_gerado" not in st.session_state:
    st.session_state.roteiro_gerado = None
if "historico_roteiros" not in st.session_state:
    st.session_state.historico_roteiros = []

def gerar_roteiro_viral(tema, nicho, duracao, tom="impactante"):
    minutos = duracao.split("-")[0]

    prompt = f"""
Você é um especialista em roteiros virais do YouTube com milhões de views.
Crie um ROTEIRO PERFEITO para vídeo de {minutos} minutos no nicho "{nicho}".

TEMA: {tema}

ESTRUTURA:
1. GANCHO
2. REENGAJAMENTO 1
3. PREPARAÇÃO
4. CLÍMAX
5. REENGAJAMENTO 2
6. CONCLUSÃO + CTA

Retorne em JSON com:
{{
  "titulo_video": "...",
  "descricao": "...",
  "tags": ["tag1","tag2"],
  "roteiro": {{
    "1_GANCHO": "...",
    "2_REENGAJAMENTO_1": "...",
    "3_PREPARACAO": "...",
    "4_CLIMAX": "...",
    "5_REENGAJAMENTO_2": "...",
    "6_CONCLUSAO_CTA": "..."
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

        try:
            return json.loads(conteudo)
        except Exception:
            m = re.search(r"\{.*\}", conteudo, re.DOTALL)
            if m:
                return json.loads(m.group())
            return {"erro": "Falha ao converter resposta em JSON", "raw": conteudo}
    except Exception as e:
        return {"erro": str(e)}

# UI principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Gerar Novo Roteiro")

    tema = st.text_area(
        "Qual o tema do seu vídeo?",
        placeholder="Ex: 5 segredos que os ricos usam para ficar mais ricos",
        height=100,
    )

    bt1, bt2 = st.columns(2)
    with bt1:
        if st.button("🚀 Gerar Roteiro Viral", type="primary"):
            if not tema.strip():
                st.warning("Informe um tema antes de gerar.")
            else:
                with st.spinner("Criando roteiro viral com IA..."):
                    resultado = gerar_roteiro_viral(tema, nicho, duracao)
                    st.session_state.roteiro_gerado = resultado
                    st.session_state.historico_roteiros.append(resultado)
                    st.rerun()
    with bt2:
        if st.button("🔄 Limpar roteiro atual"):
            st.session_state.roteiro_gerado = None
            st.rerun()

with col2:
    st.header("📊 Configuração Atual")
    st.info(f"**Nicho:** {nicho}")
    st.info(f"**Duração:** {duracao}")
    st.info(f"**Modelo:** {model}")
    st.info(f"**Temperatura:** {temperatura:.1f}")

# Exibição do roteiro
roteiro = st.session_state.roteiro_gerado
if roteiro and "erro" not in roteiro:
    st.header("✅ Roteiro Viral Gerado")

    c_tit, c_dl = st.columns([2, 1])
    with c_tit:
        st.markdown(f"### 🎥 {roteiro.get('titulo_video', 'Título gerado')}")
        st.caption(roteiro.get("descricao", ""))
    with c_dl:
        txt = f"Título: {roteiro.get('titulo_video','')}\n\n"
        txt += "ROTEIRO:\n\n"
        for secao, texto in roteiro.get("roteiro", {}).items():
            txt += f"{secao}\n{texto}\n\n"

        st.download_button(
            "💾 Download .txt",
            data=txt,
            file_name="roteiro_youtube.txt",
            mime="text/plain",
        )

    for i, (secao, texto) in enumerate(roteiro.get("roteiro", {}).items(), 1):
        with st.expander(f"{secao}", expanded=(i == 1)):
            st.markdown(texto)

    if "tags" in roteiro:
        st.subheader("🏷️ Tags sugeridas")
        st.code(", ".join(roteiro["tags"]))
elif roteiro and "erro" in roteiro:
    st.error(f"❌ Erro: {roteiro['erro']}")
    if "model_decommissioned" in roteiro["erro"]:
        st.info("Troque o modelo no selectbox para um dos modelos recomendados (ex: llama-3.3-70b-versatile).")
