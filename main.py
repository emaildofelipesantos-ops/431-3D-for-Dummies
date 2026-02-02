import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# BANCO DE DADOS ROBUSTO DE IMPRESSORAS
PRINTERS = {
    "Creality Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
    "Creality Ender 3 (V2/Neo/S1)": {"x": 220, "y": 220, "z": 250},
    "Creality Ender 5 S1": {"x": 220, "y": 220, "z": 280},
    "Creality K1 / K1C": {"x": 220, "y": 220, "z": 250},
    "Creality K1 Max": {"x": 300, "y": 300, "z": 300},
    "Bambu Lab A1 Mini": {"x": 180, "y": 180, "z": 180},
    "Bambu Lab (A1/P1/X1)": {"x": 256, "y": 256, "z": 256},
    "Prusa MK3S+ / MK4": {"x": 250, "y": 210, "z": 210},
    "Prusa XL": {"x": 360, "y": 360, "z": 360},
    "Prusa Mini+": {"x": 180, "y": 180, "z": 180},
    "Anycubic Kobra 2": {"x": 220, "y": 220, "z": 250},
    "Anycubic Kobra Max": {"x": 400, "y": 400, "z": 450},
    "Artillery Sidewinder X2": {"x": 300, "y": 300, "z": 400},
    "Elegoo Neptune 4": {"x": 225, "y": 225, "z": 265},
    "Elegoo Neptune 4 Max": {"x": 420, "y": 420, "z": 480}
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS para o POP-UP DE LOADING QUE BLOQUEIA A TELA
st.markdown("""
    <style>
    .loading-overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.85);
        display: flex; justify-content: center; align-items: center;
        z-index: 9999; color: #00FF00; flex-direction: column;
        text-align: center; font-family: sans-serif;
    }
    .loading-box {
        padding: 40px; border: 2px solid #00FF00; border-radius: 15px; background: #111;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 431 3D for Dummies")

# --- PASSO 1: ESCOLHA DA IMPRESSORA ---
st.subheader("🛠️ 1. Configuração da Máquina")
printer_name = st.selectbox("Selecione sua Impressora 3D:", sorted(list(PRINTERS.keys())))
vol = PRINTERS[printer_name]
st.write(f"📏 **Volume de Impressão:** {vol['x']}mm (X) x {vol['y']}mm (Y) x {vol['z']}mm (Z)")

# --- PASSO 2: UPLOAD ---
arquivo = st.file_uploader("2. Arraste seu arquivo STL aqui", type=['stl'])

if arquivo:
    # Espaço reservado para o Loading Central
    loading_placeholder = st.empty()

    if 'mesh' not in st.session_state:
        with loading_placeholder.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO GEOMETRIA...</h1><p>Aguarde, estamos processando o arquivo.</p></div></div>', unsafe_allow_html=True)
            conteudo = io.BytesIO(arquivo.read())
            mesh = trimesh.load(conteudo, file_type='stl')
            st.session_state.mesh = mesh
            st.session_state.d_orig = mesh.ext
