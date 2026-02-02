import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# 1. BANCO DE DADOS HIERÁRQUICO
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

# Configuração da Página
st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS para o POP-UP DE LOADING CENTRAL (BLOQUEIO TOTAL)
st.markdown("""
    <style>
    .loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.85); display: flex; 
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loading-box {
        padding: 50px; border: 3px solid #00FF00; border-radius: 20px; 
        background: #111; color: #00FF00; text-align: center;
        box-shadow: 0 0 30px #00FF00;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 431 3D for Dummies")

# --- PASSO 1: SELEÇÃO DE HARDWARE ---
st.subheader("🛠️ 1. Configuração de Hardware")
col_f, col_m = st.columns(2)
fabricante = col_f.selectbox("Fabricante:", sorted(list(DATABASE.keys())))
modelo = col_m.selectbox("Modelo:", sorted(list(DATABASE[fabricante].keys())))
vol = DATABASE[fabricante][modelo]

# --- PASSO 2: UPLOAD ---
arquivo = st.file_uploader("2. Carregar arquivo STL", type=['stl'])
pop_up = st.empty()

if arquivo:
    if 'mesh' not in st.session_state:
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO...</h1><p>Medindo geometria do modelo</p></div></div>', unsafe_allow_html=True)
            try:
                conteudo = io.BytesIO(arquivo.read())
                mesh = trimesh.load(conteudo, file_type='stl')
                st.session_state.mesh = mesh
                st.session_state.d_orig = mesh.extents
                time.sleep(1)
                pop_up.empty()
            except Exception as e:
                st.error(f"Erro ao ler STL: {e}")
                st.stop()

    d_orig = st.session_state.d_orig
    
    st.subheader("📏 Medidas Originais")
    c1, c2, c3 = st.columns(3)
    c1.metric("X", f"{d_orig[0]:.1f}mm", f"{d_orig[0]/10:.1f}cm")
    c2.metric("Y", f"{d_orig[1]:.1f}mm", f"{d_orig[1]/10:.1f}cm")
    c3.metric("Z", f"{d_orig[2]:.1f}mm", f"{d_orig[2]/10:.1f}cm")

    # --- PASSO 3: ESCALA E CORTE ---
    st.write("---")
    dim_alvo = st.number_input("Tamanho do maior lado desejado (mm):", value=float(max(d_orig)))

    if st.button("✅ Confirmar Medidas"):
        st.session_state.confirmado = True

    if st.session_state.get('confirmado'):
        f_escala = dim_alvo / max(d_orig)
        # Filtra apenas divisões que
