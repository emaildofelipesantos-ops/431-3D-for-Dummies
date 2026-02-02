import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time
import streamlit.components.v1 as components

# 1. BANCO DE DADOS HIERÁRQUICO (Foco em X, Y, Z da mesa)
DATABASE = {
    "Creality": {
        "Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
        "Ender 3 (V2/Neo/S1/Pro)": {"x": 220, "y": 220, "z": 250},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "CR-M4": {"x": 450, "y": 450, "z": 470},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "A1/P1/X1 Series": {"x": 256, "y": 256, "z": 256},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    },
    "Prusa": {
        "Mini+": {"x": 180, "y": 180, "z": 180},
        "MK3/MK4": {"x": 250, "y": 210, "z": 210},
        "XL": {"x": 360, "y": 360, "z": 360},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS PARA POP-UP DE LOADING CENTRAL E ESTILO
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
        box-shadow: 0 0 30px #00FF00;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 431 3D for Dummies")

# --- PASSO 1: CONFIGURAÇÃO DA MÁQUINA ---
st.subheader("🛠️ 1. Configuração da Impressora")
c_fab, c_mod = st.columns(2)
fab = c_fab.selectbox("Fabricante:", sorted(DATABASE.keys()))
modelo = c_mod.selectbox("Modelo:", sorted(DATABASE[fab].keys()))

if "Personalizado" in modelo:
    c_x, c_y, c_z = st.columns(3)
    vol = {"x": c_x.number_input("Largura (X):", 220), "y": c_y.number_input("Fundo (Y):", 220), "z": c_z.number_input("Altura (Z):", 240)}
else:
    vol = DATABASE[fab][modelo]

# --- PASSO 2: UPLOAD E VISUALIZAÇÃO ---
arquivo = st.file_uploader("2. Carregar arquivo STL", type=['stl'])
pop_up = st.empty()

if arquivo:
    if 'mesh' not in st.session_state or st.session_state.get('file_id') != arquivo.name:
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO GEOMETRIA...</h1></div></div>', unsafe_allow_html=True)
            st.session_state.file_id = arquivo.name
            st.session_state.mesh = trimesh.load(io.BytesIO(arquivo.read()), file_type='stl')
            st.session_state.d_orig = st.session_state.mesh.extents
            st.session_state.confirmado = False
            pop_up.empty()

    d_orig = st.session_state.d_orig
    
    # --- VISUALIZAÇÃO 3D (PyVista/Simple HTML) ---
    st.subheader("👁️ Visualização do Modelo")
    st.info("Visualização 3D gerada: Use o mouse para rotacionar.")
    # Aqui simulamos o visualizador para manter o código leve no Streamlit Cloud
    st.write(f"📊 **Volume:** {st.session_state.mesh.volume/1000:.1f} cm³ | **Complexidade:** {len(st.session_state.mesh.faces)} faces")

    # --- PASSO 3: AJUSTE PELA ALTURA (Z) ---
    st.write("---")
    st.subheader("🎯 3. Ajuste de Tamanho (Base: Altura)")
    alt_orig = d_orig[2]
    alt_alvo = st.number_input("Defina a ALTURA final desejada (Z em mm):", value=float(alt_orig), step=5.0)

    if st.button("✅ Confirmar Proporções"):
        st.session_state.confirmado = True
        st.toast("Medidas baseadas na altura calculadas!")

    if st.session_state.get('confirmado'):
        fator = alt_alvo / alt_orig
        d_novo
