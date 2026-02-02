import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# 1. BANCO DE DADOS MASSIVO DE FABRICANTES E MODELOS
DATABASE = {
    "Creality": {
        "Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
        "Ender 3 (V2/Neo/S1/Pro)": {"x": 220, "y": 220, "z": 250},
        "Ender 3 Max Neo": {"x": 300, "y": 300, "z": 340},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "Ender 5 S1 / Plus": {"x": 220, "y": 220, "z": 300},
        "CR-10 / CR-10S Pro": {"x": 300, "y": 300, "z": 400},
        "CR-M4": {"x": 450, "y": 450, "z": 470},
        "Sermoon V1 / D3": {"x": 175, "y": 175, "z": 165},
        "Outro Modelo Creality": {"x": 0, "y": 0, "z": 0}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "A1 (Padrão)": {"x": 256, "y": 256, "z": 256},
        "P1P / P1S": {"x": 256, "y": 256, "z": 256},
        "X1 / X1-Carbon / X1E": {"x": 256, "y": 256, "z": 256},
        "Outro Modelo Bambu": {"x": 0, "y": 0, "z": 0}
    },
    "Anycubic": {
        "Kobra 2 Neo / Pro": {"x": 220, "y": 220, "z": 250},
        "Kobra 2 Plus": {"x": 320, "y": 320, "z": 400},
        "Kobra 2 Max": {"x": 420, "y": 420, "z": 500},
        "Vyper / Chiron": {"x": 245, "y": 245, "z": 260},
        "Outro Modelo Anycubic": {"x": 0, "y": 0, "z": 0}
    },
    "Elegoo": {
        "Neptune 4 / 4 Pro": {"x": 225, "y": 225, "z": 265},
        "Neptune 4 Plus": {"x": 320, "y": 320, "z": 385},
        "Neptune 4 Max": {"x": 420, "y": 420, "z": 480},
        "Outro Modelo Elegoo": {"x": 0, "y": 0, "z": 0}
    },
    "Prusa / Voron / Outhers": {
        "Prusa MK3S+ / MK4": {"x": 250, "y": 210, "z": 210},
        "Prusa XL": {"x": 360, "y": 360, "z": 360},
        "Voron 2.4 (350)": {"x": 350, "y": 350, "z": 350},
        "RatRig V-Core 3": {"x": 400, "y": 400, "z": 400},
        "Sovol SV06 / SV07": {"x": 220, "y": 220, "z": 250},
        "Artillery Sidewinder": {"x": 300, "y": 300, "z": 400},
        "Modelo Não Listado": {"x": 0, "y": 0, "z": 0}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS PARA POP-UP DE LOADING CENTRALIZADO (BLOQUEIO TOTAL)
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

# Suporte para modelos não listados / lançamentos
if "Outro" in modelo or "Não Listado" in modelo:
    cx, cy, cz = st.columns(3)
    vol = {
        "x": cx.number_input("Largura Mesa (X):", 220), 
        "y": cy.number_input("Fundo Mesa (Y):", 220), 
        "z": cz.number_input("Altura Máxima (Z):", 250)
    }
else:
    vol = DATABASE[fab][modelo]

# --- PASSO 2: UPLOAD ---
arquivo = st.file_uploader("2. Carregar arquivo STL", type=['stl'])
pop_up = st.empty()

if arquivo:
    if 'mesh' not in st.session_state or st.session_state.get('file_id') != arquivo.name:
        st.session_state.file_id = arquivo.name
        st.session_state.confirmado = False
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO...</h1></div></div>', unsafe_allow_html=True)
            st.session_state.mesh = trimesh.load(io.BytesIO(arquivo.read()), file_type='stl')
            st.session_state.d_orig = st.session_state.mesh.extents
            pop_up.empty()

    d_orig = st.session_state.d_orig
    st.subheader("📏 Medidas do Objeto")
    m1, m2, m3 = st.columns(3)
    m1.metric("X (Largura)", f"{d_orig[0]:.1f}mm")
    m2.metric("Y (Fundo)", f"{d_orig[1]:.1f}mm")
    m3.metric("Z (Altura)", f"{d_orig[2]:.1f}mm")

    # --- PASSO 3: ESCALA PELA ALTURA (Z) ---
    st.write("---")
    st.subheader("🎯 2. Definir Altura Final (Z)")
    alt_alvo = st.number_input("Altura total desejada (mm):", value=float(d_orig[2]), step=10.0)

    if st.button("✅ Confirmar Novo Tamanho"):
        st.session_state.confirmado = True

    if st.session_state.get('confirmado'):
        fator = alt_alvo / d_orig[2]
        d_novo = d_orig * fator
        st.info(f"💡 Resultado Proporcional: {d_novo[0]:.1f}mm(X) x {d_novo[1]:.1f}mm(Y) x **{alt_alvo:.1f}mm(Z)**")

        # Filtro de cortes
        opcoes = [p for p in [1, 2, 4, 6, 8, 12] if (d_novo[0]/(p**0.5)) <= vol['x'] and (d_novo[1]/(p**0.5)) <= vol['y']]
        
        if not opcoes:
            st.error("❌ A peça não cabe. Reduza a altura.")
        else:
            qtd_partes = st.selectbox("Dividir em:", opcoes)

            # --- PASSO 4: GERAÇÃO DO G-CODE (EVITA QUEDA DE CONEXÃO) ---
            if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
                with pop_up.container():
                    st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>🤖 GERANDO G-CODE...</h1><p>Processando camadas no servidor</p></div></div>', unsafe_allow_html=True)
                    try:
                        # 1. Escala
                        m_final = st.session_state.mesh.copy().apply_scale(fator)
                        temp_stl = f"temp_{int(time.time())}.stl"
                        m_final.export(temp_stl)
                        
                        # 2. Comando Slic3r otimizado (rápido para não cair conexão)
                        output_gcode = "print_final.gcode"
                        process = subprocess.run([
                            "slic3r", temp_stl, 
                            "--no-gui", 
                            "--fill-density", "15%", 
                            "--layer-height", "0.2",
                            "--output", output_gcode
                        ], capture_output=True, text=True, timeout=120) # Timeout de 2 min

                        if process.returncode == 0:
                            buf = io.BytesIO()
                            with zipfile.ZipFile(buf, "w") as zf:
                                if os.path.exists(output_gcode):
                                    zf.write(output_gcode)
                                zf.writestr("Config.txt", f"Altura: {alt_alvo}mm\nPartes: {qtd_partes}")
                            
                            pop_up.empty()
                            st.balloons()
                            st.download_button("📥 BAIXAR AGORA", buf.getvalue(), "431_Pronto.zip")
                        else:
                            st.error(f"Erro no fatiador: {process.stderr}")
                    except Exception as e:
                        pop_up.empty()
                        st.error(f"Erro de Conexão/Processamento: {e}")
