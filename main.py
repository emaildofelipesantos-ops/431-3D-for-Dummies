import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# 1. BANCO DE DADOS ROBUSTO DE IMPRESSORAS
DATABASE = {
    "Creality": {
        "Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
        "Ender 3 (V2/Neo/S1)": {"x": 220, "y": 220, "z": 250},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "CR-M4": {"x": 450, "y": 450, "z": 470}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "P1P / P1S": {"x": 256, "y": 256, "z": 256},
        "X1 Carbon": {"x": 256, "y": 256, "z": 256}
    },
    "Prusa": {
        "MK4": {"x": 250, "y": 210, "z": 210},
        "XL": {"x": 360, "y": 360, "z": 360}
    },
    "Elegoo": {
        "Neptune 4 Max": {"x": 420, "y": 420, "z": 480}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS PARA O POP-UP DE LOADING QUE BLOQUEIA A TELA NO CENTRO
st.markdown("""
    <style>
    .loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.9); display: flex; 
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loading-box {
        padding: 40px; border: 3px solid #00FF00; border-radius: 20px; 
        background: #111; color: #00FF00; text-align: center;
        box-shadow: 0 0 20px #00FF00; min-width: 300px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 431 3D for Dummies")

# --- PASSO 1: ESCOLHA DA MÁQUINA ---
st.subheader("🛠️ 1. Seleção de Hardware")
c_fab, c_mod = st.columns(2)
fabricante = c_fab.selectbox("Fabricante:", sorted(list(DATABASE.keys())))
modelo = c_mod.selectbox("Modelo:", sorted(list(DATABASE[fabricante].keys())))
vol = DATABASE[fabricante][modelo]

# --- PASSO 2: UPLOAD ---
arquivo = st.file_uploader("2. Carregar arquivo STL", type=['stl'])
pop_up = st.empty()

if arquivo:
    if 'mesh' not in st.session_state:
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO...</h1><p>Medindo volume e geometria</p></div></div>', unsafe_allow_html=True)
            conteudo = io.BytesIO(arquivo.read())
            mesh = trimesh.load(conteudo, file_type='stl')
            st.session_state.mesh = mesh
            st.session_state.d_orig = mesh.extents
            time.sleep(1)
            pop_up.empty()

    d_orig = st.session_state.d_orig
    
    # --- MEDIDAS E STATUS (Organizado em colunas, sem o bloco JSON feio) ---
    st.subheader("📏 Informações do Modelo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm")
    col2.metric("Fundo (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm")
    col3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm")

    # Status técnico discreto abaixo das métricas
    st.write(f"📊 **Volume:** {st.session_state.mesh.volume/1000:.1f} cm³ | **Faces:** {len(st.session_state.mesh.faces)}")

    # --- PASSO 3: AJUSTE E DIVISÃO ---
    st.write("---")
    dim_alvo = st.number_input("Novo tamanho para o maior lado (mm):", value=float(max(d_orig)), step=10.0)

    if st.button("✅ Confirmar Medidas"):
        st.session_state.confirmado = True
        st.toast("Proporções salvas!")

    if st.session_state.get('confirmado'):
        f_escala = dim_alvo / max(d_orig)
        
        # Filtro inteligente de divisões
        opcoes = [p for p in [1, 2, 4, 6, 8, 12] if (dim_alvo/(p**0.5)) <= vol['x']]
        
        if not opcoes:
            st.error("❌ A peça não cabe nem dividida. Diminua o tamanho.")
        else:
            qtd_partes = st.selectbox("Dividir em quantas partes? (Apenas opções que cabem):", opcoes)

            # --- PASSO 4: GERAÇÃO COM BLOQUEIO ---
            if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
                with pop_up.container():
                    st.markdown(f'<div class="loading-overlay"><div class="loading-box"><h1>🤖 FAT
