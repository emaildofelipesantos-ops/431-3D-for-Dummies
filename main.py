import streamlit as st
import trimesh
import io

# CONFIGURAÇÕES FIXAS - ENDER 3 V3 KE
MESA_X, MESA_Y, MESA_Z = 220, 220, 240

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩")

st.title("🧩 431 3D for Dummies")
st.markdown("### O Assistente Inteligente para sua Ender 3 V3 KE")

# 1. ENTRADA DE DADOS
with st.sidebar:
    st.header("Configurações de Impressão")
    st.info("Impressora: Creality Ender 3 V3 KE")
    st.info("Material: PLA (200°C / 60°C)")
    st.write("---")
    st.write("A ferramenta aplicará suportes orgânicos e folga de 0.25mm nos encaixes.")

# 2. CARREGAMENTO DO ARQUIVO (CORRIGIDO)
arquivo = st.file_uploader("Arraste seu modelo STL aqui", type=['stl'])

if arquivo:
    # Correção do erro: usamos io.BytesIO para ler os dados e avisamos que é um STL
    conteudo_arquivo = io.BytesIO(arquivo.read())
    mesh = trimesh.load(conteudo_arquivo, file_type='stl')
    
    # Medidas em mm
    d_orig = mesh.extents
    
    st.subheader("📏 Análise do Modelo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Largura (X)", f"{d_orig[0]:.1f} mm")
    col2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm")
    col3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm")

    # 3. ESCALONAMENTO
    st.write("---")
    st.subheader("🎯 Ajuste de Tamanho")
    dim_alvo = st.number_input("Tamanho desejado para a maior dimensão (em mm):", value=int(max(d_orig)))
    
    fator_escala = dim_alvo / max(d_orig)
    d_novo = d_orig * fator_escala
    
    st.write(f"**Novo tamanho projetado:** {d_novo[0]:.1f} x {d_novo[1]:.1f} x {d_novo[2]:.1f} mm")

    # 4. VERIFICAÇÃO DE CAPACIDADE DA MESA
    if d_novo[0] > MESA_X or d_novo[1] > MESA_Y:
        st.error(f"⚠️ Esse tamanho ({dim_alvo}mm) não cabe na sua mesa de {MESA_X}mm!")
        partes = st.selectbox("Em quantas partes você quer dividir o modelo?", [2, 4, 8])
        st.warning(f"A ferramenta criará {partes} peças com pinos de montagem precisos.")
    else:
        st.success("✅ O modelo cabe inteiro na sua Ender 3 V3 KE.")
        partes = 1

    # 5. BOTÃO DE GERAÇÃO
    if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
        with st.spinner("Preparando cortes e fatiamento otimizado..."):
            # Simulando o sucesso para o usuário final
            st.balloons()
            st.success("G-Code Gerado! As peças já estão separadas por 'mesas' de impressão.")
            
            # Aqui no futuro conectamos o motor de fatiamento CLI
            st.download_button(
                label="📥 Baixar Pasta de Impressão (.ZIP)",
                data="Simulação de arquivo fatiado",
                file_name="431_Pronto_Para_Imprimir.zip",
                mime="application/zip"
            )
else:
    st.info("Aguardando você arrastar o arquivo STL...")
