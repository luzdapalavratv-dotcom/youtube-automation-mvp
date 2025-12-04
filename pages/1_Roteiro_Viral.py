import os
import json
import uuid
import random
from datetime import datetime

import streamlit as st
from groq import Groq  # biblioteca oficial da Groq [web:166][web:169]

st.set_page_config(page_title="1 – Roteiro Viral", layout="wide")
st.title("📝 1 – Gerador de Roteiro Viral para YouTube (Groq)")

# -------------------------------------------------------------------
# DADOS DO MODO VIRAL (RICO VS POBRE)
# -------------------------------------------------------------------
CIDADES_BR = {
  "São Paulo": {
    "rico": ["Jardins", "Morumbi", "Higienópolis", "Alphaville", "Itaim Bibi"],
    "pobre": ["Heliópolis", "Paraisópolis", "Capão Redondo", "Cidade Tiradentes", "Grajaú"]
  },
  "Rio de Janeiro": {
    "rico": ["Leblon", "Ipanema", "Barra da Tijuca", "Gávea", "Jardim Botânico"],
    "pobre": ["Rocinha", "Cidade de Deus", "Complexo do Alemão", "Maré", "Vigário Geral"]
  },
  "Belo Horizonte": {
    "rico": ["Savassi", "Lourdes", "Belvedere", "Mangabeiras", "São Bento"],
    "pobre": ["Aglomerado da Serra", "Morro do Papagaio", "Ribeiro de Abreu", "Taquaril"]
  }
}

IDIOMAS = {
  "pt-BR": {
    "flag": "🇧🇷", "nome": "Português",
    "nomesRicos": ["Roberto", "Fernando", "Eduardo", "Ricardo", "Antônio", "Carlos", "Marcos", "Pedro"],
    "nomesPobres": ["Sofia", "Helena", "Maria", "Ana", "Clara", "Beatriz", "Lúcia", "Rosa"],
    "governantas": ["Dona Marta", "Dona Rosa", "Dona Fátima", "Dona Conceição"],
    "moeda": "reais",
    "cta1": "Se você acredita que o destino une as pessoas certas, digite DESTINO nos comentários agora!",
    "cta2": "Se esta história tocou seu coração, deixe seu LIKE e COMPARTILHE com quem é sua verdadeira família!"
  },
  "en-US": {
    "flag": "🇺🇸", "nome": "English",
    "nomesRicos": ["William", "James", "Robert", "Charles", "Richard", "Thomas", "Edward", "Henry"],
    "nomesPobres": ["Emma", "Lily", "Sophie", "Grace", "Olivia", "Mia", "Rose", "Lucy"],
    "governantas": ["Mrs. Patterson", "Mrs. Johnson", "Mrs. Williams", "Mrs. Brown"],
    "moeda": "dollars",
    "cta1": "If you believe destiny brings the right people together, type DESTINY in the comments now!",
    "cta2": "If this story touched your heart, LIKE and SHARE with someone who is your true family!"
  },
  "es-ES": {
    "flag": "🇪🇸", "nome": "Español",
    "nomesRicos": ["Carlos", "Miguel", "Fernando", "Antonio", "José", "Ricardo", "Alberto", "Francisco"],
    "nomesPobres": ["Sofía", "María", "Lucía", "Carmen", "Elena", "Isabel", "Rosa", "Ana"],
    "governantas": ["Doña Carmen", "Doña Rosa", "Doña María", "Doña Pilar"],
    "moeda": "euros",
    "cta1": "Si crees que el destino une a las personas correctas, escribe DESTINO en los comentarios!",
    "cta2": "Si esta historia tocó tu corazón, dale LIKE y COMPARTE con quien es tu verdadera familia!"
  }
}

TITULOS_FORMULAS = {
    "pt-BR": [
      "Milionário estava prestes a Perder a Empresa — até que a Menina Apareceu com sua Pasta Perdida",
      "Milionário ia tomar Café Envenenado — até que a Garotinha deu um tapa na xícara",
      "Milionário Viúvo estava prestes a Pular — até que a Menina diz algo que muda tudo",
      "Milionário ia ser preso injustamente — até que a Garotinha apareceu com seu celular perdido",
      "\"QUER SER MINHA FILHA?\" DISSE O MILIONÁRIO DOENTE PARA A GAROTINHA DE RUA",
      "Milionário DEMITIU a Faxineira por estar Cansada — mas Chorou quando a Filha dela revelou o motivo",
      "O MILIONÁRIO MANDOU DEMITIR A FAXINEIRA, MAS A FILHA DELA CHEGOU E ELE FICOU CHOCADO",
      "Milionário Odiava Crianças até que a Filha da Faxineira fez Algo que Mudou Tudo"
    ],
    "en-US": [
      "Millionaire was about to Lose his Company — until the Little Girl Showed Up",
      "Millionaire was about to Drink Poisoned Coffee — until the Little Girl Slapped the Cup",
      "Widowed Millionaire was about to Jump — until the Little Girl Said Something that Changed Everything",
      "Millionaire FIRED the Maid for Being Tired — but Cried when her Daughter Revealed the Reason"
    ],
    "es-ES": [
      "Millonario estaba a punto de Perder su Empresa — hasta que la Niña Apareció",
      "Millonario iba a tomar Café Envenenado — hasta que la Niña le dio un golpe a la taza",
      "Millonario Viudo estaba a punto de Saltar — hasta que la Niña dijo algo que lo cambió todo",
      "Millonario DESPIDIÓ a la Empleada por estar Cansada — pero Lloró cuando su Hija reveló el motivo"
    ]
}

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

# Variáveis de sessão para o modo viral
if "viral_personagens" not in st.session_state:
    st.session_state.viral_personagens = None
if "viral_idioma" not in st.session_state:
    st.session_state.viral_idioma = "pt-BR"

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

groq_client = get_groq_client()

MODELO_GROQ = "llama-3.3-70b-versatile"

# -------------------------------------------------------------------
# FUNÇÕES AUXILIARES VIRAL
# -------------------------------------------------------------------
def gerar_personagens_viral(idioma_key):
    config = IDIOMAS.get(idioma_key, IDIOMAS["pt-BR"])
    
    # Seleção de cidade (apenas BR ou genérica se for outro idioma para simplificar, 
    # ou expandir lógica se quiser mapas gringos)
    cidades_keys = list(CIDADES_BR.keys())
    cidade_nome = random.choice(cidades_keys)
    cidade_data = CIDADES_BR[cidade_nome]
    
    local_rico = random.choice(cidade_data["rico"])
    local_pobre = random.choice(cidade_data["pobre"])
    
    idade_rico = random.randint(55, 75)
    idade_crianca = random.randint(6, 12)
    fortuna = random.randint(200, 800)
    
    detalhes_rico = [
        "Guarda um relógio de bolso parado na hora exata do acidente",
        "Mantém um quarto trancado há 5 anos que nunca mais entrou",
        "Tem um piano de cauda que não toca desde a tragédia",
        "Usa a aliança de casamento mesmo após a viuvez",
        "Guarda uma foto virada para baixo na mesa do escritório"
    ]
    
    detalhes_crianca = [
        "Usa sapatos amarrados com barbante colorido mas mantém a dignidade",
        "Carrega uma caixinha de balas decorada com desenhos próprios",
        "Tem um caderno velho onde desenha janelas de casas bonitas",
        "Usa uma fita de cetim no cabelo, única herança da avó",
        "Tem um sorriso com dente faltando mas cheio de luz"
    ]
    
    return {
        "cidade": cidade_nome,
        "rico": {
            "nome": random.choice(config["nomesRicos"]),
            "idade": idade_rico,
            "local": f"{local_rico}, {cidade_nome}",
            "fortuna": f"{fortuna} milhões de {config['moeda']}",
            "trauma": "Perdeu a família em um acidente há 5 anos",
            "detalhe": random.choice(detalhes_rico)
        },
        "crianca": {
            "nome": random.choice(config["nomesPobres"]),
            "idade": idade_crianca,
            "local": f"{local_pobre}, {cidade_nome}",
            "situacao": "Vende balas no sinal para comprar remédios para a mãe doente",
            "detalhe": random.choice(detalhes_crianca)
        },
        "governanta": random.choice(config["governantas"]),
        "cta1": config["cta1"],
        "cta2": config["cta2"],
        "idioma_nome": config["nome"]
    }

# -------------------------------------------------------------------
# Sidebar – contexto e parâmetros de roteiro
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📺 Contexto")
    st.markdown(f"**Canal:** {canal.get('nome','')}")
    st.markdown(f"**Nicho:** {canal.get('nicho','')}")
    
    st.markdown("---")
    st.header("🎯 Objetivo do vídeo")

    objetivo = st.selectbox(
        "Função principal",
        [
            "Entreter (humor, storytelling)",
            "Educar (aula, explicação)",
            "Inspirar (história, testemunho)",
            "Converter (venda/call to action)",
        ],
        index=0,
    )

    duracao = st.selectbox(
        "Duração desejada",
        [
            "Curto (3-5 min)",
            "Médio (6-10 min)",
            "Longo (11-20 min)",
            "Muito Longo (20+ min)"
        ],
        index=1,
    )

    st.markdown("---")
    st.header("🧠 Configuração do Roteiro")

    tipo_roteiro = st.selectbox(
        "Tipo de roteiro",
        [
            "História Viral (Rico vs Pobre)",  # Opção NOVA
            "Aula passo a passo",
            "História emocional (Genérica)",
            "Lista de dicas",
            "Estudo bíblico estruturado",
        ],
        index=0,
    )

    # Lógica condicional para o modo Viral
    is_viral_mode = (tipo_roteiro == "História Viral (Rico vs Pobre)")
    
    if is_viral_mode:
        st.info("💎 **Modo Viral Ativado**")
        st.markdown("Configurações exclusivas para histórias de alto impacto emocional.")
        
        # Seleção de Idioma
        idioma_sel = st.selectbox(
            "Idioma do Vídeo",
            list(IDIOMAS.keys()),
            format_func=lambda x: f"{IDIOMAS[x]['flag']} {IDIOMAS[x]['nome']}",
            index=0
        )
        st.session_state.viral_idioma = idioma_sel
        
        nivel_emocao = "Extremo (Choro/Comoção)" # Força alto nível
        
        # Gerador de Títulos (Sugestão)
        if st.button("🎲 Sugerir Título Viral"):
            formulas = TITULOS_FORMULAS.get(idioma_sel, TITULOS_FORMULAS["pt-BR"])
            sugestao = random.choice(formulas)
            # Hack para atualizar o input de título via session_state se necessário,
            # ou apenas mostrar para o usuário copiar
            st.code(sugestao, language="text")
            st.caption("Copie o título acima para o campo principal.")

        st.markdown("---")
        st.subheader("👥 Personagens")
        
        if st.button("🎭 Gerar Novos Personagens"):
            st.session_state.viral_personagens = gerar_personagens_viral(idioma_sel)
        
        # Se não tiver personagens gerados, gera um padrão
        if not st.session_state.viral_personagens:
             st.session_state.viral_personagens = gerar_personagens_viral(idioma_sel)
             
        p = st.session_state.viral_personagens
        if p:
            with st.expander("Ver Detalhes dos Personagens", expanded=True):
                st.markdown(f"**Rico:** {p['rico']['nome']}, {p['rico']['idade']} anos")
                st.caption(f"Trauma: {p['rico']['trauma']} | Detalhe: {p['rico']['detalhe']}")
                st.markdown(f"**Criança:** {p['crianca']['nome']}, {p['crianca']['idade']} anos")
                st.caption(f"Luta: {p['crianca']['situacao']} | Detalhe: {p['crianca']['detalhe']}")
                st.markdown(f"**Governanta:** {p['governanta']}")
                st.markdown(f"**Ambientação:** {p['cidade']}")

    else:
        # Controles Padrão para outros tipos
        nivel_emocao = st.select_slider(
            "Nível de emoção na narrativa",
            options=["Baixo", "Médio", "Alto"],
            value="Médio",
        )

    st.markdown("---")
    
    # Resto da Sidebar Comum
    persona_canal = canal.get("persona", "")
    if not persona_canal:
        persona_canal = "Adultos interessados no tema do canal, nível iniciante/intermediário."

    st.header("🧑‍💻 Persona do público")
    persona_custom = st.text_area(
        "Quem deve assistir este vídeo?",
        value=persona_canal,
        height=100,
    )

    st.header("🗣 Tom e voz da marca")
    tom_marca = canal.get("tom_marca", "Direto, didático, com exemplos simples.")
    tom_custom = st.text_area(
        "Como o roteiro deve soar?",
        value=tom_marca,
        height=80,
    )
    
    restricoes = st.text_area("Palavras / temas a evitar", value=canal.get("palavras_proibidas", ""), height=80)

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
    # Argumentos opcionais para o modo Viral
    personagens_viral: dict = None
):
    """
    Usa Groq (llama-3.3-70b-versatile) para gerar roteiro em JSON.
    Se personagens_viral for fornecido, usa o Prompt Especializado Viral.
    """

    sistema = (
        "Você é um roteirista profissional de vídeos para YouTube. "
        "Sempre responde em JSON válido, sem comentários, sem texto fora do JSON."
    )
    
    # --------------------------------------------------------
    # SELEÇÃO DE PROMPT: MODO VIRAL vs MODO PADRÃO
    # --------------------------------------------------------
    if tipo_roteiro == "História Viral (Rico vs Pobre)" and personagens_viral:
        # --- PROMPT ESPECIALIZADO VIRAL (baseado no React App) ---
        p = personagens_viral
        
        usuario = f"""
Você é um roteirista especialista em histórias emocionantes "Rico vs Pobre" (estilo Dhar Mann).

DADOS DA HISTÓRIA:
- TÍTULO: "{titulo_video}"
- IDIOMA DO TEXTO: {p.get('idioma_nome', 'Português')}
- DURAÇÃO ALVO: {duracao}

PERSONAGENS (INCLUA ESTES DETALHES OBRIGATORIAMENTE):
- Rico: {p['rico']['nome']}, {p['rico']['idade']} anos. (Detalhe visual: {p['rico']['detalhe']}). Trauma: {p['rico']['trauma']}. Fortuna: {p['rico']['fortuna']}.
- Criança/Pobre: {p['crianca']['nome']}, {p['crianca']['idade']} anos. (Detalhe visual: {p['crianca']['detalhe']}). Situação: {p['crianca']['situacao']}.
- Governanta/Secundário: {p['governanta']}.
- Cidade: {p['cidade']}.

ESTRUTURA OBRIGATÓRIA (Narrativa Emocional):
1. GANCHO: Comece chocante. Apresente {p['rico']['nome']} e sua dor/arrogância.
2. LUTA: Mostre a dificuldade de {p['crianca']['nome']}.
3. ENCONTRO: O momento que eles se cruzam.
4. CTA DE MEIO: Insira exatamente a frase: "{p['cta1']}" num momento de suspense.
5. CONFLITO/CLÍMAX: Uma injustiça acontece ou uma revelação.
6. RESOLUÇÃO: O coração do rico amolece ou a verdade aparece.
7. LIÇÃO DE MORAL: Frase final impactante.
8. CTA FINAL: Insira exatamente a frase: "{p['cta2']}".

REGRAS DE FORMATAÇÃO DO TEXTO (CRÍTICO PARA TTS):
- Escreva o conteúdo dos blocos como TEXTO CORRIDO, pronto para ser lido em voz alta.
- NÃO use asteriscos (**), negrito, ou indicações de cena (ex: "Cena 1", "[Música triste]").
- NÃO coloque nomes antes das falas (ex: "Maria diz:"). Incorpore a fala naturalmente na narração.
- Use pontuação para indicar pausas.

Formato OBRIGATÓRIO da resposta (JSON):
{{
  "hook": "As primeiras 2 frases chocantes da história.",
  "promessa": "Resumo da lição de moral que será aprendida.",
  "estrutura": "Resumo da jornada de {p['rico']['nome']} e {p['crianca']['nome']}.",
  "roteiro": {{
    "Parte 1 - O Encontro": "Texto corrido narrando o início e o encontro.",
    "Parte 2 - O Conflito": "Texto corrido desenvolvendo o drama e inserindo a CTA de Meio.",
    "Parte 3 - A Revelação": "Texto corrido com o clímax e a resolução.",
    "Parte 4 - Epílogo e Lição": "Texto corrido com o final feliz, a lição de moral e a CTA Final."
  }}
}}
"""
    else:
        # --- PROMPT PADRÃO (Mantido do original) ---
        usuario = f"""
Contexto do canal:
- Nome do canal: {canal_nome}
- Nicho do canal: {canal_nicho}
- Persona do público: {persona}
- Tom de voz da marca: {tom}
- Palavras/temas proibidos: {restricoes or "nenhuma informada"}

Briefing do vídeo:
- Objetivo principal: {objetivo}
- Tipo de roteiro: {tipo_roteiro}
- Nível de emoção: {nivel_emocao}
- Duração: {duracao} (TTS est: {duracao_estimada})
- Título: {titulo_video}
- Briefing extra: {briefing or "nenhum"}

Tarefa:
Crie um roteiro COMPLETO e ORIGINAL para YouTube.

Formato OBRIGATÓRIO da resposta (JSON):
{{
  "hook": "frase inicial muito forte (5-10s).",
  "promessa": "o que a pessoa ganha assistindo.",
  "estrutura": "descrição da jornada.",
  "roteiro": {{
    "Abertura": "texto corrido da introdução.",
    "Bloco 1": "conteúdo 1.",
    "Bloco 2": "conteúdo 2 / exemplos.",
    "Bloco 3": "aprofundamento.",
    "Encerramento": "resumo e CTA."
  }}
}}

Regras:
1. Português brasileiro natural (salvo se solicitado outro idioma no briefing).
2. Sem markdown nos textos do roteiro.
3. Se for "História emocional", use storytelling.
"""

    resposta = groq_client.chat.completions.create(
        model=MODELO_GROQ,
        messages=[
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        temperature=0.7, # Um pouco mais criativo
        max_tokens=4096,
    )

    conteudo = resposta.choices[0].message.content
    tokens_total = getattr(resposta.usage, "total_tokens", 0)

    # Extração de JSON resiliente
    inicio = conteudo.find("{")
    fim = conteudo.rfind("}")
    if inicio == -1 or fim == -1:
        # Fallback simples se der erro muito grave, tenta limpar markdown code blocks
        conteudo = conteudo.replace("```json", "").replace("```", "")
        inicio = conteudo.find("{")
        fim = conteudo.rfind("}")
    
    if inicio == -1 or fim == -1:
        raise ValueError(f"A resposta do modelo não contém JSON válido. Resposta crua: {conteudo[:100]}...")
        
    json_str = conteudo[inicio : fim + 1]
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # Tentativa desesperada de correção de aspas se necessário (opcional)
        raise ValueError("Erro ao fazer parse do JSON retornado pelo modelo.")

    # Normalização
    roteiro_norm = {}
    raw_roteiro = data.get("roteiro", {})
    if isinstance(raw_roteiro, dict):
        for k, v in raw_roteiro.items():
            roteiro_norm[str(k)] = str(v).strip()
    
    return {
        "hook": data.get("hook", "").strip(),
        "promessa": data.get("promessa", "").strip(),
        "estrutura": data.get("estrutura", "").strip(),
        "roteiro": roteiro_norm,
        "tokens": tokens_total,
        "modelo": MODELO_GROQ,
    }

# -------------------------------------------------------------------
# Área principal – edição do título e briefing
# -------------------------------------------------------------------
st.subheader("🎬 Título e briefing do vídeo")

# Se estiver no modo viral e tivermos uma sugestão copiável, o usuário cola aqui
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
    label_botao = "🚀 Gerar Roteiro Viral" if is_viral_mode else "🚀 Gerar / regenerar roteiro completo"
    
    if st.button(label_botao, type="primary"):
        if not titulo_video.strip():
            st.warning("Informe ao menos um título para o vídeo.")
        else:
            if video["artefatos"]["roteiro"].get("roteiro"):
                st.info("Um roteiro já existe. O novo irá substituir o atual.")
            
            with st.spinner("Gerando roteiro com a IA da Groq..."):
                try:
                    # Prepara args opcionais
                    args_extras = {}
                    if is_viral_mode:
                        # Garante que temos personagens
                        if not st.session_state.viral_personagens:
                             st.session_state.viral_personagens = gerar_personagens_viral(st.session_state.viral_idioma)
                        args_extras["personagens_viral"] = st.session_state.viral_personagens

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
                        **args_extras # Passa os extras
                    )

                    video["artefatos"]["roteiro"] = {
                        "id": video["artefatos"]["roteiro"].get("id", str(uuid.uuid4())[:8]),
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
    st.markdown("**Promessa / Moral**")
    st.write(dados.get("promessa", "") or "_Ainda não definida._")
with col_r3:
    st.markdown("**Estrutura geral**")
    st.write(dados.get("estrutura", "") or "_Ainda não definida._")

meta = {
    "Modelo": dados.get("modelo_usado") or "-",
    "Tokens (aprox.)": dados.get("tokens_uso") or 0,
    "Gerado em": (dados.get("gerado_em") or "")[:16],
}
st.caption(f"Modelo: {meta['Modelo']} · Tokens: {meta['Tokens (aprox.)']} · Gerado em: {meta['Gerado em']}")

st.markdown("---")
st.subheader("🧩 Seções do roteiro")

roteiro_secoes = dados.get("roteiro", {}) or {}

if not roteiro_secoes:
    st.info("Nenhuma seção de roteiro registrada ainda.")
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
            f"Texto: {nome}",
            value=roteiro_secoes.get(nome, ""),
            height=300, # Aumentei um pouco a altura para facilitar a leitura dos roteiros longos
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
    "Após finalizar o roteiro, vá para **2 – Thumbnails**."
)
