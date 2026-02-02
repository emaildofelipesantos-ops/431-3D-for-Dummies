import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# 1. BANCO DE DADOS COMPLETO
DATABASE = {
    "Creality": {
        "Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
        "Ender 3 (V2/Neo/S1/Pro)": {"x": 220, "y": 220, "z": 250},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "Personalizado": {"x": 0, "y": 0, "z": 0}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "Série P1 / X1": {"x": 256, "y": 256, "z": 256},
        "Personalizado": {"x": 0, "y": 0, "z": 0}
    },
    "Prusa": {
        "MK3 / MK4": {"x": 250, "y": 210, "z": 210},
        "XL": {"x": 360, "y": 360, "z": 360},
        "Personalizado": {"x": 0, "y": 0, "z": 0}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# Estilo para o POP-UP DE LOADING CENTRALIZADO
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
    cx, cy, cz = st.columns(3)
    vol = {"x": cx.number_input("Largura (X):", 220), "y": cy.number_input("Fundo (Y):", 220), "z": cz.number_input("Altura (Z):", 240)}
else:
    vol = DATABASE[fab][modelo]

# --- PASSO 2: UPLOAD E ANÁLISE ---
arquivo = st.file_uploader("2. Carregar arquivo STL", type=['stl'])
pop_up = st.empty()

if arquivo:
    # Reinicia se o arquivo mudar
    if 'file_id' not in st.session_state or st.session_state.file_id != arquivo.name:
        st.session_state.file_id = arquivo.name
        st.session_state.confirmado = False
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO...</h1></div></div>', unsafe_allow_html=True)
            st.session_state.mesh = trimesh.load(io.BytesIO(arquivo.read()), file_type='stl')
            st.session_state.d_orig = st.session_state.mesh.extents
            time.sleep(1)
            pop_up.empty()

    if 'mesh' in st.session_state:
        d_orig = st.session_state.d_orig
        st.subheader("📏 Medidas Originais")
        st.write(f"Largura: {d_orig[0]:.1f}mm | Fundo: {d_orig[1]:.1f}mm | **Altura: {d_orig[2]:.1f}mm**")
        st.write(f"📊 Volume: {st.session_state.mesh.volume/1000:.1f} cm³")

        # --- PASSO 3: ESCALA PELA ALTURA ---
        st.write("---")
        st.subheader("🎯 3. Ajuste de Tamanho (Base: Altura)")
        alt_alvo = st.number_input("Defina a ALTURA final (Z em mm):", value=float(d_orig[2]), step=10.0)

        if st.button("✅ Confirmar Medidas"):
            st.session_state.confirmado = True

        if st.session_state.get('confirmado'):
            fator = alt_alvo / d_orig[2]
            d_novo = d_orig * fator
            st.info(f"💡 Resultado: {d_novo[0]:.1f}mm (X) x {d_novo[1]:.1f}mm (Y) x **{d_novo[2]:.1f}mm (Z)**")

            # Filtro de cortes
            opcoes = [p for p in [1, 2, 4, 6, 8, 12] if (d_novo[0]/(p**0.5)) <= vol['x']]
            
            if not opcoes:
                st.error("❌ A peça não cabe. Reduza a altura.")
            else:
                qtd_partes = st.selectbox("Dividir em:", opcoes)

                # --- PASSO 4: GERAÇÃO ---
                if st.button("🚀 GERAR G-CODE"):
                    with pop_up.container():
                        st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>🤖 FATIANDO...</h1></div></div>', unsafe_allow_html=True)
                        try:
                            m_final = st.session_state.mesh.copy().apply_scale(fator)
                            m_final.export("temp.stl")
                            subprocess.run(["slic3r", "temp.stl", "--output", "f.gcode"], check=True)
                            
                            buf = io.BytesIO()
                            with zipfile.ZipFile(buf, "w") as zf:
                                zf.write("f.gcode")
                            
                            pop_up.empty()
                            st.balloons()
                            st.download_button("📥 BAIXAR", buf.getvalue(), "431_Pronto.zip")
                        except Exception as e:
                            pop_up.empty()
                            st.error(f"Erro: {e}")
