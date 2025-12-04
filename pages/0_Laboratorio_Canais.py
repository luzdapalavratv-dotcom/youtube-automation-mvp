import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Laboratório de Canais", layout="wide")

# APIs
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY")

st.title("🔬 **0. LABORATÓRIO DE CANAIS**")
st.markdown("**Análise estratégica + Validação nicho → Produção certeira**")

# ===============================================
# SIDEBAR CONFIG
# ===============================================
with st.sidebar:
    st.header("🎯 Configuração")
    nicho_base = st.selectbox("Nicho Principal", [
        "Histórias Emocionais", "Mistério/Terror", "True Crime", 
        "Motivação", "Finanças Pessoais", "Curiosidades", "Romance"
    ])
    meta_monetizacao = st.selectbox("Meta", ["1k inscritos", "4k horas", "10k inscritos"])
    
    st.header("📊 APIs")
    st.success(f"✅ GROQ: {GROQ_API_KEY[:10]}...")
    st.success(f"✅ YouTube: {YOUTUBE_API_KEY[:10]}...")

# ===============================================
# ETAPA 1 - ANÁLISE NICHO
# ===============================================
if 'analise_completa' not in st.session_state:
    st.session_state.analise_completa = None

col1, col2 = st.columns([1, 3])

with col1:
    st.header("🔍 **Passo 1**")
    st.subheader("Definir Estratégia")
    
    if st.button("🚀 **ANALISAR NICHO com Groq IA**", type="primary"):
        with st.spinner("Groq Llama 3.1 405B analisando..."):
            st.session_state.analise_completa = analisar_nicho_groq(nicho_base, meta_monetizacao)

with col2:
    if st.session_state.analise_completa:
        st.header("📈 **Resultados IA**")
        analise = st.session_state.analise_completa
        
        st.metric("🎯 Micronicho Recomendado", analise.get('micronicho', 'Carregando...'))
        st.metric("📅 Frequência", analise.get('frequencia', 'Carregando...'))
        st.metric("⏱️ Duração Ideal", analise.get('duracao_ideal', 'Carregando...'))
        
        st.subheader("📝 Fórmulas Títulos")
        for i, titulo in enumerate(analise.get('titulos_formula', []), 1):
            st.code(f"{i}. {titulo}")
        
        st.subheader("🖼️ Estilo Thumbnails")
        st.write(f"**{analise.get('thumbnails_estilo', 'Carregando...')}**")
    else:
        st.info("👆 Clique 'ANALISAR NICHO' para começar!")

# ===============================================
# BOTÕES DE AÇÃO
# ===============================================
st.markdown("---")
col1, col2, col3 = st.columns(3)

if col1.button("✅ **SALVAR Estratégia → Próximo**", type="primary", disabled=not st.session_state.analise_completa):
    st.session_state.nicho_config = st.session_state.analise_completa
    st.success("✅ Configuração salva para próximos módulos!")
    st.balloons()

if col2.button("🔄 Nova Análise"):
    st.session_state.analise_completa = None
    st.rerun()

if col3.button("📋 Ver Checklist"):
    st.markdown("""
    **📋 CHECKLIST 2.1 TESTADO:**
    - ☐ Análise Groq funcionando
    - ☐ Métricas aparecendo  
    - ☐ Fórmulas títulos OK
    - ☐ Salvar estratégia OK
    """)

# ===============================================
# FUNÇÕES INTERNAS
# ===============================================
def gerar_roteiro_groq(prompt):
    """Groq API helper"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-405b-reasoning",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers=headers, json=data, timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Groq Error: {str(e)}")
        return None

def analisar_nicho_groq(nicho, meta):
    """Análise estratégica completa"""
    prompt = f"""ANALISE ESTRATÉGICA YouTube - RESponda JSON válido:

NICHO: "{nicho}"
META: {meta}

{{"nicho": "{nicho}",
  "micronicho_recomendado": "fórmula EXATA para viralizar",
  "frequencia_postagens": "X vídeos/semana",
  "duracao_ideal": "X minutos",
  "titulos_formula": ["exato1", "exato2", "exato3", "exato4", "exato5"],
  "thumbnails_estilo": "cores + estilo visual",
  "previsao_crescimento": "X inscritos 90 dias",
  "personagens_tipos": ["tipo1", "tipo2"]}}

SEJA ESPECÍFICO e PRONTO para produção."""

    resultado = gerar_roteiro_groq(prompt)
    
    # Tenta parse JSON (Groq às vezes adiciona texto)
    try:
        # Extrai JSON da resposta
        inicio = resultado.find('{')
        fim = resultado.rfind('}') + 1
        json_str = resultado[inicio:fim]
        return json.loads(json_str)
    except:
        # Fallback se JSON falhar
        return {
            "micronicho_recomendado": nicho + " otimizado",
            "frequencia_postagens": "5 vídeos/semana",
            "duracao_ideal": "12-15 minutos",
            "titulos_formula": [f"Exemplo {i+1}" for i in range(5)],
            "thumbnails_estilo": "Vermelho dramático + texto amarelo",
            "previsao_crescimento": "8k inscritos 90 dias"
        }

st.markdown("---")
st.caption("**MVP Teste 2.1 - Laboratório | Próximo: 2.2 Roteiro Viral**")

