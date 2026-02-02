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
        "Ender 3 (V2/Neo/S1/Pro)": {"x": 220, "y": 220, "z": 250},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "CR-M4": {"x": 450, "y": 450, "z": 470},
        "Personalizado": {"x": 0, "y": 0, "z": 0}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "A1 / P1 / X1 Series": {"x": 256, "y": 256, "z": 256}
    },
    "Prusa": {
        "MK3 / MK4": {"x": 250, "y": 210, "z": 210},
        "XL": {"x": 360, "y": 360, "z": 360}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS PARA O POP-UP DE LOADING CENTRAL (BLOQUEIO TOTAL)
st.markdown("""
    <style>
    .loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.9); display: flex; 
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loading-box {
        padding: 50px; border: 3px solid #00FF00; border-radius: 20px; 
        background: #111; color: #00FF00; text-align: center;
        box-shadow: 0 0 30px #00FF00; font-family: 'Courier New', Courier, monospace;
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
    c1, c2, c3 = st.columns(3)
    vol = {
        "x": c1.number_input("Largura (X):", 220), 
        "y": c2.number_input("Fundo (Y):", 220), 
        "z": c3.number_input("Altura (Z):", 240)
    }
else:
    vol = DATABASE[fab][modelo]

# --- PASSO 2: UPLOAD E ANÁLISE ---
arquivo = st.file_uploader("2. Carregar arquivo STL", type=['stl'])
pop_up = st.empty()

if arquivo:
    # Gerencia troca de arquivo para não dar erro de memória
    if 'file_id' not in st.session_state or st.session_state.file_id != arquivo.name:
        st.session_state.file_id = arquivo.name
        st.session_state.confirmado = False
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO...</h1></div></div>', unsafe_allow_html=True)
            try:
                st.session_state.mesh = trimesh.load(io.BytesIO(arquivo.read()), file_type='stl')
                st.session_state.d_orig = st.session_state.mesh.extents
                pop_up.empty()
            except Exception as e:
                st.error(f"Erro ao processar STL: {e}")
                st.stop()

    if 'mesh' in st.session_state:
        d_orig = st.session_state.d_orig
        
        # --- MEDIDAS DO MODELO ---
        st.subheader("📏 Informações do Objeto")
        m1, m2, m3 = st.columns(3)
        m1.metric("Largura (X)", f"{d_orig[0]:.1f}mm")
        m2.metric("Fundo (Y)", f"{d_orig[1]:.1f}mm")
        m3.metric("Altura (Z)", f"{d_orig[2]:.1f}mm")

        # --- PASSO 3: ESCALA PELA ALTURA ---
        st.write("---")
        st.subheader("🎯 2. Definir Nova Altura (Z)")
        alt_alvo = st.number_input("Altura final desejada (mm):", value=float(d_orig[2]), step=10.0)

        if st.button("✅ Confirmar Novo Tamanho"):
            st.session_state.confirmado = True
            st.toast("Proporções calculadas!", icon="📐")

        if st.session_state.get('confirmado'):
            fator = alt_alvo / d_orig[2]
            d_novo = d_orig * fator
            
            st.info(f"💡 Resultado: {d_novo[0]:.1f}mm (X) x {d_novo[1]:.1f}mm (Y) x **{alt_alvo:.1f}mm (Z)**")

            # Filtro inteligente de cortes para caber na mesa X e Y
            opcoes = [p for p in [1, 2, 4, 6, 8, 12, 16] if (d_novo[0]/(p**0.5)) <= vol['x'] and (d_novo[1]/(p**0.5)) <= vol['y']]
            
            if not opcoes:
                st.error("❌ Peça grande demais. Reduza a altura ou use uma impressora maior.")
            else:
                qtd_partes = st.selectbox("Em quantas partes dividir para caber na mesa?", opcoes)

                # --- PASSO 4: GERAÇÃO DO G-CODE ---
                if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
                    with pop_up.container():
                        st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>🤖 GERANDO G-CODE...</h1><p>Fatiando modelo e calculando suportes</p></div></div>', unsafe_allow_html=True)
                        try:
                            # Aplica escala
                            m_final = st.session_state.mesh.copy().apply_scale(fator)
                            temp_stl = "final_export.stl"
                            m_final.export(temp_stl)
                            
                            # Comando Slic3r otimizado para servidor
                            output_gcode = "print_ready.gcode"
                            result = subprocess.run([
                                "slic3r", temp_stl, "--no-gui", "--output", output_gcode
                            ], capture_output=True, text=True)

                            if result.returncode != 0:
                                st.error(f"Erro no motor Slic3r: {result.stderr}")
                            else:
                                buf = io.BytesIO()
                                with zipfile.ZipFile(buf, "w") as zf:
                                    zf.write(output_gcode)
                                    zf.writestr("Configuracao.txt", f"Altura: {alt_alvo}mm\nPartes: {qtd_partes}\nFator: {fator*100:.1f}%")
                                
                                pop_up.empty()
                                st.balloons()
                                st.download_button("📥 BAIXAR PACOTE COMPLETO", buf.getvalue(), f"431_{modelo}.zip")
                        except Exception as e:
                            pop_up.empty()
                            st.error(f"Erro fatal: {e}")
else:
    st.info("Arraste um arquivo STL para começar a 431 3D for Dummies.")
