import streamlit as st
import groq
from groq import Groq
import json
import re

st.set_page_config(page_title="1_Roteiro_Viral", layout="wide")
st.title("🎬 Gerador de Roteiro Viral para YouTube")

# Inicializar cliente Groq
@st.cache_resource
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = get_groq_client()

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    model = st.selectbox("Modelo Groq", 
                        ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"], 
                        index=0)
    
    temperatura = st.slider("Temperatura (criatividade)", 0.0, 1.0, 0.7, 0.1)
    
    nicho = st.selectbox("Nicho do canal", 
                        ["Motivação", "Finanças", "Saúde", "Tecnologia", "Religião", "Negócios", "Educação"])
    
    duracao = st.selectbox("Duração alvo", ["5-8 min", "8-12 min", "12-15 min"], index=1)

# Session state para armazenar dados
if "roteiro_gerado" not in st.session_state:
    st.session_state.roteiro_gerado = None
if "historico_roteiros" not in st.session_state:
    st.session_state.historico_roteiros = []

def gerar_roteiro_viral(tema, nicho, duracao, tom="impactante"):
    """Gera roteiro viral otimizado para YouTube usando estrutura comprovada"""
    
    minutos = duracao.split("-")[0]
    
    prompt = f"""
    Você é um especialista em roteiros virais do YouTube com milhões de views. 
    Crie um ROTEIRO PERFEITO para vídeo de {minutos} minutos no nicho **{nicho}**.
    
    TEMA: {tema}
    
    **ESTRUTURA OBRIGATÓRIA do Roteiro Viral (use exatamente estes títulos):**
    
    1. **GANCHO (30 seg)**: Pergunta chocante/dado surpreendente/curiosidade irresistível
    2. **REENGajAMENTO 1**: 3 fatos rápidos + novo gancho (dúvida/paradoxo)
    3. **PREPARAÇÃO**: Construa tensão, dê pistas, use gatilhos mentais
    4. **CLÍMAX**: A revelação principal/melhor solução/verdade chocante  
    5. **REENGajAMENTO 2**: Resumo rápido + prova social/números
    6. **CONCLUSÃO + CTA**: Resumo final + call-to-action poderoso
    
    **REGRAS RÍGIDAS:**
    - Tom: {tom}, direto, conversacional como amigo íntimo
    - Linguagem: Palavras simples, frases curtas (15 palavras máx)
    - Cada seção: 80-150 palavras
    - Inclua marcações [PAUSA] e [ENFASE] onde necessário
    - Finalize com 3 CTAs específicos (like, comentário, inscrever)
    
    FORMATO JSON:
    {{
        "titulo_video": "Título otimizado com números/emojis",
        "descricao": "Primeiras linhas da descrição",
        "tags": ["tag1", "tag2", "tag3"],
        "roteiro": {{
            "1_GANCHO": "texto...",
            "2_REENGajAMENTO_1": "texto...", 
            "3_PREPARACAO": "texto...",
            "4_CLIMAX": "texto...",
            "5_REENGajAMENTO_2": "texto...",
            "6_CONCLUSAO_CTA": "texto..."
        }}
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperatura,
            max_tokens=4000
        )
        
        conteudo = response.choices[0].message.content.strip()
        
        # Tentar parsear JSON
        try:
            roteiro_json = json.loads(conteudo)
            return roteiro_json
        except:
            # Fallback: extrair JSON do texto
            json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"erro": "Falha no parsing", "raw": conteudo}
            
    except Exception as e:
        return {"erro": str(e)}

# Interface principal
col1, col2 = st.columns([2,1])

with col1:
    st.header("📝 Gerar Novo Roteiro")
    
    tema = st.text_area("Qual o tema do seu vídeo?", 
                       placeholder="Ex: 5 segredos que os ricos usam para ficar mais ricos",
                       height=100)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Gerar Roteiro Viral", type="primary"):
            with st.spinner("Criando roteiro viral com IA..."):
                resultado = gerar_roteiro_viral(tema, nicho, duracao)
                st.session_state.roteiro_gerado = resultado
                st.session_state.historico_roteiros.append(resultado)
                st.rerun()
    
    with col_btn2:
        if st.button("🔄 Novo Roteiro") and tema:
            st.session_state.roteiro_gerado = None
            st.rerun()

with col2:
    st.header("📊 Configuração Atual")
    st.info(f"**Nicho:** {nicho}")
    st.info(f"**Duração:** {duracao}")
    st.info(f"**Modelo:** {model}")
    st.info(f"**Temp:** {temperatura:.1f}")

# Exibir roteiro gerado
if st.session_state.roteiro_gerado and "erro" not in st.session_state.roteiro_gerado:
    roteiro = st.session_state.roteiro_gerado
    
    st.header("✅ Roteiro Viral Gerado!")
    
    col_titulo, col_download = st.columns([1,1])
    
    with col_titulo:
        st.markdown(f"### 🎥 **{roteiro.get('titulo_video', 'Título Gerado')}**")
        st.caption(roteiro.get('descricao', ''))
    
    with col_download:
        roteiro_txt = f"Título: {roteiro['titulo_video']}\n\n"
        roteiro_txt += "ROTEIRO:\n\n"
        for secao, texto in roteiro['roteiro'].items():
            roteiro_txt += f"{secao}\n{texto}\n\n"
        
        st.download_button(
            label="💾 Download .txt",
            data=roteiro_txt,
            file_name=f"roteiro_{nicho}_{tema[:20]}.txt",
            mime="text/plain"
        )
    
    # Exibir roteiro estruturado
    for i, (secao, texto) in enumerate(roteiro['roteiro'].items(), 1):
        with st.expander(f"📖 {secao}", expanded=(i==1)):
            st.markdown(f"**{secao}**")
            st.markdown(texto)
            st.divider()
    
    # Tags sugeridas
    if 'tags' in roteiro:
        st.subheader("🏷️ Tags Otimizadas")
        tags = ", ".join(roteiro['tags'][:15])
        st.code(tags)

elif st.session_state.roteiro_gerado and "erro" in st.session_state.roteiro_gerado:
    st.error(f"❌ Erro: {st.session_state.roteiro_gerado['erro']}")

# Histórico
if st.session_state.historico_roteiros:
    st.header("📚 Histórico de Roteiros")
    for i, rot in enumerate(st.session_state.historico_roteiros[-3:]):
        if "titulo_video" in rot:
            st.markdown(f"**{rot['titulo_video']}** - {len(rot['roteiro'])} seções")
    
    if st.button("🗑️ Limpar Histórico"):
        st.session_state.historico_roteiros = []
        st.session_state.roteiro_gerado = None
        st.rerun()

st.markdown("---")
st.caption("💡 Próximo: [2_Geracao_Imagem.py] → Gere thumbnails virais para este roteiro")

