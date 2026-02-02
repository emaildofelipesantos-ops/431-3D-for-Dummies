import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# CONFIGURAÇÕES DA SUA ENDER 3 V3 KE
MESA_X, MESA_Y = 220, 220 

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

st.title("🧩 431 3D for Dummies")

# 1. CARREGAMENTO DO ARQUIVO
arquivo = st.file_uploader("1. Arraste seu STL aqui", type=['stl'])

# Criamos um espaço reservado no CENTRO para mensagens de trabalho
area_de_trabalho = st.empty()

if arquivo:
    if 'confirmado' not in st.session_state:
        st.session_state.confirmado = False

    # Mensagem Central de Análise Inicial
    if 'analisado' not in st.session_state:
        with area_de_trabalho.container():
            st.info("⌛ **TRABALHANDO NO CENTRO:** Analisando geometria do modelo...")
            conteudo = io.BytesIO(arquivo.read())
            mesh = trimesh.load(conteudo, file_type='stl')
            st.session_state.mesh = mesh
            st.session_state.d_orig = mesh.extents
            st.session_state.analisado = True
            time.sleep(1)
            area_de_trabalho.empty() # Limpa o centro após terminar
    
    d_orig = st.session_state.d_orig

    st.subheader("📏 Tamanho Atual Detectado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm")
    c2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm")
    c3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm")

    st.write("---")
    
    # 2. DEFINIR NOVO TAMANHO
    st.subheader("🎯 2. Defina o novo tamanho")
    maior_lado_atual = float(max(d_orig))
    
    dim_alvo = st.number_input("Tamanho do MAIOR LADO desejado (mm):", value=maior_lado_atual)

    if st.button("✅ Confirmar Medidas"):
        with area_de_trabalho.container():
            st.warning("🔄 **TRABALHANDO NO CENTRO:** Aplicando novas dimensões...")
            time.sleep(1)
            st.session_state.confirmado = True
            area_de_trabalho.empty()

    if st.session_state.confirmado:
        fator_escala = dim_alvo / maior_lado_atual
        d_novo = d_orig * fator_escala
        st.info(f"💡 Novo tamanho: **{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm x {d_novo[2]/10:.1f} cm**")

        # 3. DIVISÃO
        partes_escolhidas = 1
        if d_novo[0] > MESA_X or d_novo[1] > MESA_Y:
            st.warning("⚠️ Peça excede a mesa da Ender 3 V3 KE.")
            partes_escolhidas = st.select_slider("Dividir em:", options=[2, 4, 6, 8], value=4)

        # 4. GERAÇÃO DO G-CODE (CARREGAMENTO CENTRALIZADO)
        if st.button("🚀 3. GERAR G-CODE REAL"):
            with area_de_trabalho.container():
                st.markdown("---")
                st.header("🤖 **PROCESSANDO G-CODE**")
                barra = st.progress(0)
                msg = st.empty()
                
                try:
                    msg.write("📐 Ajustando escala para 200°C/60°C...")
                    barra.progress(30)
                    
                    mesh_final = st.session_state.mesh.copy()
                    mesh_final.apply_scale(fator_escala)
                    temp_stl = "final.stl"
                    mesh_final.export(temp
