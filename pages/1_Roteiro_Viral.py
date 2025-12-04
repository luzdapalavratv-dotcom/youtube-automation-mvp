import os
import json
import uuid
from datetime import datetime

import streamlit as st
from groq import Groq  # biblioteca oficial da Groq [web:166][web:169]

st.set_page_config(page_title="1 – Roteiro Viral", layout="wide")
st.title("📝 1 – Gerador de Roteiro Viral para YouTube (Groq)")

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
# Garante estrutura de artefatos de roteiro
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
# Cliente Groq
# -------------------------------------------------------------------
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY não encontrado em st.secrets ou variáveis de ambiente.")
        st.stop()
    return Groq(api_key=api_key)

groq_client = get_groq_client()  # [web:169][web:180]

MODELO_GROQ = "llama-3.3-70b-versatile"  # modelo recomendado para texto longo [web:181]

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

    st.markdown("---")
    st.header("🧠 Tom dramático")

    nivel_emocao = st.select_slider(
        "Nível de emoção na narrativa",
        options=["Baixo", "Médio", "Alto"],
        value="Médio",
    )

    tipo_roteiro = st.selectbox(
        "Tipo de roteiro",
        [
            "Aula passo a passo",
            "História emocional",
            "Lista de dicas",
            "Estudo bíblico estruturado",
        ],
        index=0,
    )

    persona_canal = canal.get("persona", "")
    if not persona_canal:
        persona_canal = "Adultos interessados no tema do canal, nível iniciante/intermediário."

    st.markdown("---")
    st.header("🧑‍💻 Persona do público")
    persona_custom = st.text_area(
        "Quem deve assistir este vídeo?",
        value=persona_canal,
        height=120,
    )

    st.markdown("---")
    st.header("🗣 Tom e voz da marca")

    tom_marca = canal.get(
        "tom_marca",
        "Direto, didático, com exemplos simples, sem jargões difíceis.",
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
# Função de chamada ao Groq (JSON mode)
# -------------------------------------------------------------------
def chamar_modelo_roteiro_groq(
    titulo_video: str,
    briefing: str,
    objetivo: str,
    duracao: str,
    duracao_estimada: str,
    persona: str,
    tom: str,
    restricoes: str,
    nivel_emocao: str,
    tipo_roteiro: str,
    canal_nome: str,
    canal_nicho: str,
):
    """
    Usa Groq (llama-3.3-70b-versatile) para gerar roteiro em JSON com:
    hook, promessa, estrutura e dict de seções.
    """  # [web:169][web:181]

    sistema = (
        "Você é um roteirista profissional de vídeos para YouTube, especialista em "
        "roteiros envolventes otimizados para retenção, watch time e clareza didática. "
        "Sempre responde em JSON válido, sem comentários, sem texto fora do JSON."
    )

    # Prompt inspirado nas regras detalhadas do app Gemini (adaptado) [file:161]
    usuario = f"""
Contexto do canal:
- Nome do canal: {canal_nome}
- Nicho do canal: {canal_nicho}
- Persona do público: {persona}
- Tom de voz da marca: {tom}
- Palavras/temas proibidos (não use nem faça apologia): {restricoes or "nenhuma informada"}

Briefing do vídeo:
- Objetivo principal do vídeo: {objetivo}
- Tipo de roteiro: {tipo_roteiro}
- Nível de emoção desejado: {nivel_emocao}
- Duração desejada (macro): {duracao}
- Estimativa de duração para TTS: {duracao_estimada}
- Título provisório do vídeo: {titulo_video}
- Briefing adicional detalhado (situação, gancho, contexto): {briefing or "nenhum briefing extra"}

Tarefa:
Crie um roteiro COMPLETO e ORIGINAL para este vídeo de YouTube, fortemente alinhado ao nicho do canal e ao título.

Formato OBRIGATÓRIO da resposta:
Responda apenas com um JSON válido, no seguinte formato (sem comentários):

{{
  "hook": "frase inicial muito forte para os primeiros 5-10 segundos, em 1-2 frases.",
  "promessa": "explicação clara do que a pessoa vai ganhar assistindo até o final.",
  "estrutura": "descrição textual em 2-4 frases da jornada do vídeo.",
  "roteiro": {{
    "Abertura": "texto corrido da introdução, escrito para ser narrado em voz alta.",
    "Bloco 1": "texto corrido com o primeiro bloco de conteúdo.",
    "Bloco 2": "texto corrido com exemplos/aplicações.",
    "Bloco 3": "opcional: aprofundamento, perguntas retóricas, conexões emocionais.",
    "Encerramento": "resumo, CTA (inscrever-se, comentar, próxima etapa) e fechamento emocional."
  }}
}}

Regras importantes para o conteúdo do campo "roteiro":
1. Escreva tudo em português brasileiro natural, na segunda pessoa (você).
2. Sem listas, sem marcadores, sem Markdown, sem títulos de blocos na saída final (apenas texto corrido em cada campo).
3. Evite repetir literalmente o título do vídeo muitas vezes; use variações naturais.
4. Use perguntas retóricas, exemplos concretos e pequenas metáforas quando ajudarem a clareza.
5. Adapte vocabulário, referências e densidade de explicação ao nicho e à persona do canal.
6. Se o tipo de roteiro for "História emocional", estruture como storytelling com personagem, conflito e resolução.
7. Se for "Estudo bíblico estruturado", cite referências de forma respeitosa, mas sem escrever versículos inteiros.
"""

    resposta = groq_client.chat.completions.create(
        model=MODELO_GROQ,
        messages=[
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        temperature=0.6,
        max_tokens=4096,
    )

    conteudo = resposta.choices[0].message.content
    tokens_total = getattr(resposta.usage, "total_tokens", 0)

    # Tenta extrair JSON puro, mesmo que venha com texto antes/depois
    inicio = conteudo.find("{")
    fim = conteudo.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("A resposta do modelo não contém JSON válido.")
    json_str = conteudo[inicio : fim + 1]

    data = json.loads(json_str)

    # Normaliza campos esperados
    hook = data.get("hook", "").strip()
    promessa = data.get("promessa", "").strip()
    estrutura = data.get("estrutura", "").strip()
    roteiro = data.get("roteiro", {})

    if not isinstance(roteiro, dict):
        raise ValueError("Campo 'roteiro' não é um objeto JSON.")

    roteiro_norm = {}
    for nome_secao, texto in roteiro.items():
        roteiro_norm[str(nome_secao)] = str(texto).strip()

    return {
        "hook": hook,
        "promessa": promessa,
        "estrutura": estrutura,
        "roteiro": roteiro_norm,
        "tokens": tokens_total,
        "modelo": MODELO_GROQ,
    }

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
        "Estimativa de duração (usada como referência para TTS)",
        ["5-7 min", "8-12 min", "13-20 min"],
        index=1,
    )

briefing = st.text_area(
    "Briefing adicional (opcional)",
    value=video.get("descricao", ""),
    height=120,
    help="Use para explicar o contexto específico, passagem bíblica, exemplo real, oferta, etc.",
)

# -------------------------------------------------------------------
# Geração do roteiro com Groq
# -------------------------------------------------------------------
st.subheader("⚙️ Geração do roteiro com IA (Groq)")

col_bt1, col_bt2 = st.columns(2)

with col_bt1:
    if st.button("🚀 Gerar / regenerar roteiro completo", type="primary"):
        if not titulo_video.strip():
            st.warning("Informe ao menos um título para o vídeo.")
        else:
            # Confirmação leve se já existe roteiro
            if video["artefatos"]["roteiro"].get("roteiro"):
                st.info("Um roteiro já existe. O novo irá substituir o atual.")
            with st.spinner("Gerando roteiro com a IA da Groq..."):
                try:
                    resultado = chamar_modelo_roteiro_groq(
                        titulo_video=titulo_video.strip(),
                        briefing=briefing,
                        objetivo=objetivo,
                        duracao=duracao,
                        duracao_estimada=dur_estimada,
                        persona=persona_custom,
                        tom=tom_custom,
                        restricoes=restricoes,
                        nivel_emocao=nivel_emocao,
                        tipo_roteiro=tipo_roteiro,
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

meta = {
    "Modelo": dados.get("modelo_usado") or "-",
    "Tokens (aprox.)": dados.get("tokens_uso") or 0,
    "Gerado em": (dados.get("gerado_em") or "")[:16],
}
st.caption(
    f"Modelo: {meta['Modelo']} · Tokens: {meta['Tokens (aprox.)']} · Gerado em: {meta['Gerado em']}"
)

st.markdown("---")
st.subheader("🧩 Seções do roteiro")

roteiro_secoes = dados.get("roteiro", {}) or {}

if not roteiro_secoes:
    st.info(
        "Nenhuma seção de roteiro registrada ainda. Gere um roteiro com a IA da Groq "
        "ou escreva manualmente abaixo."
    )
    # Cria seções padrão para facilitar edição manual
    roteiro_secoes = {
        "Abertura": "",
        "Bloco 1": "",
        "Bloco 2": "",
        "Bloco 3": "",
        "Encerramento": "",
    }

sec_nomes = list(roteiro_secoes.keys())
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
    if not video["artefatos"]["roteiro"].get("gerado_em"):
        video["artefatos"]["roteiro"]["gerado_em"] = datetime.now().isoformat()
    video["status"]["1_roteiro"] = True
    video["ultima_atualizacao"] = datetime.now().isoformat()
    st.success("Roteiro atualizado para este vídeo.")

st.markdown("---")
st.caption(
    "Após finalizar o roteiro com a IA da Groq e eventuais ajustes manuais, "
    "vá para **2 – Thumbnails** para criar as capas com base neste conteúdo."
)
