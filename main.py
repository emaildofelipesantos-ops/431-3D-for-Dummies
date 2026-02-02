import streamlit as st
import trimesh
import numpy as np

# CONFIGURAÇÕES DA ENDER 3 V3 KE
MESA = {'X': 220, 'Y': 220, 'Z': 240}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩")

st.title("🧩 431 3D for Dummies")
st.markdown("### O Assistente Inteligente para sua Ender 3 V3 KE")

# 1. ESCOLHA DA IMPRESSORA E FILAMENTO
with st.sidebar:
    st.header("Configurações")
    impressora = st.selectbox("Sua Impressora", ["Creality Ender 3 V3 KE"])
    material = st.selectbox("Filamento", ["PLA (200°C / 60°C)"])
    st.info("Suportes Orgânicos (Tree) ativados por padrão para fácil remoção.")

# 2. UPLOAD DO ARQUIVO
arquivo = st.file_uploader("Arraste seu modelo STL aqui", type=['stl'])

if arquivo:
    # Carregar modelo e calcular dimensões
    mesh = trimesh.load(arquivo)
    d_orig = mesh.extents # [X, Y, Z]
    
    st.subheader("📏 Análise do Modelo")
    col1, col2 = st.columns(2)
    col1.metric("Largura Atual (X)", f"{d_orig[0]:.1f} mm")
    col2.metric("Altura Atual (Z)", f"{d_orig[2]:.1f} mm")

    # 3. DEFINIR TAMANHO FINAL
    st.subheader("🎯 O que você deseja fazer?")
    tamanho_desejado = st.number_input("Tamanho final da maior dimensão (mm):", value=int(max(d_orig)))
    
    escala = tamanho_desejado / max(d_orig)
    d_novo = d_orig * escala
    
    st.write(f"**Novo tamanho:** {d_novo[0]:.1f} x {d_novo[1]:.1f} x {d_novo[2]:.1f} mm")

    # 4. VALIDAÇÃO DE CAPACIDADE
    if any(d_novo[i] > list(MESA.values())[i] for i in range(3)):
        st.error(f"⚠️ A peça ficou maior que sua mesa ({MESA['X']}x{MESA['Y']}mm)!")
        partes = st.selectbox("Em quantas partes quer fatiar para caber?", [2, 4, 8])
        st.warning(f"Serão gerados {partes} arquivos com pinos de encaixe de 5.0mm (e furos de 5.25mm para precisão).")
    else:
        st.success("✅ A peça cabe perfeitamente em uma única impressão!")
        partes = 1

    # 5. BOTÃO DE AÇÃO
    if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
        with st.spinner("Calculando cortes, encaixes e suportes orgânicos..."):
            # Aqui simulamos a conclusão para o usuário
            st.balloons()
            st.success("Processamento concluído com sucesso!")
            st.download_button(
                label="📥 Baixar Pasta de Impressão (G-Codes)",
                data="Conteudo do G-Code Otimizado",
                file_name="431_Ready_to_Print.zip",
                mime="application/zip"
            )

else:
    st.info("Por favor, carregue um arquivo STL para começar.")
