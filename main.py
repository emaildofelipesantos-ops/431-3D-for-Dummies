import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# 1. BANCO DE DADOS ROBUSTO (Categorizado e Expandido)
DATABASE = {
    "Creality": {
        "Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
        "Ender 3 (V2/Neo/S1/Pro)": {"x": 220, "y": 220, "z": 250},
        "Ender 3 Max / Max Neo": {"x": 300, "y": 300, "z": 340},
        "Ender 5 (S1/Pro/Plus)": {"x": 220, "y": 220, "z": 300},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "CR-10 (V2/V3/Smart/Max)": {"x": 300, "y": 300, "z": 400},
        "CR-M4": {"x": 450, "y": 450, "z": 470},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "A1": {"x": 256, "y": 256, "z": 256},
        "P1P / P1S": {"x": 256, "y": 256, "z": 256},
        "X1 / X1C / X1E": {"x": 256, "y": 256, "z": 256},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    },
    "Prusa": {
        "Mini+": {"x": 180, "y": 180, "z": 180},
        "MK2/MK3/MK4": {"x": 250, "y": 210, "z": 210},
        "XL (Single/Multi-Tool)": {"x": 360, "y": 360, "z": 360},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    },
    "Elegoo": {
        "Neptune 3 / 4 (Pro)": {"x": 225, "y": 225, "z": 265},
        "Neptune 3 / 4 Plus": {"x": 320, "y": 320, "z": 385},
        "Neptune 3 / 4 Max": {"x": 420, "y": 420, "z": 480},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    },
    "Anycubic": {
        "Kobra 2 (Neo/Pro)": {"x": 220, "y": 220, "z": 250},
        "Kobra 2 Plus": {"x": 320, "y": 320, "z": 400},
        "Kobra 2 Max": {"x": 420, "y": 420, "z": 500},
        "Personalizado (Digitar Medidas)": {"x": 0, "y": 0, "z": 0}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS PARA POP-UP DE LOADING CENTRAL (BLOQUEIO TOTAL)
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
st.subheader("🛠️ 1. Configuração da Impressora")
c_fab, c_mod = st.columns(2)
fabricante = c_fab.selectbox("Fabricante:", sorted(list(DATABASE.keys())))
modelo = c_mod.selectbox("Modelo:", sorted(list(DATABASE[fabricante].keys())))

# Lógica para modelos personalizados
if "Personalizado" in modelo:
    c_x, c_y = st.columns(2)
    vol_x = c_x.number_input("Largura Mesa (X em mm):", value=220)
    vol_y = c_y.number_input("Profundidade Mesa (Y em mm):", value=220)
    vol = {"x": vol_x, "y": vol_y}
else:
    vol = DATABASE[fabricante][modelo]

st.write(f"📏 **Espaço Útil Selecionado:** {vol['x']}x{vol['y']}mm")

# --- PASSO 2: UPLOAD ---
arquivo = st.file_uploader("2. Arraste seu arquivo STL aqui", type=['stl'])
pop_up = st.empty()

if arquivo:
    # Gerenciamento de Memória para evitar erro ao trocar arquivo
    if 'file_id' not in st.session_state or st.session_state.file_id != arquivo.name:
        st.session_state.file_id = arquivo.name
        st.session_state.confirmado = False
        if 'mesh' in st.session_state: del st.session_state.mesh

    if 'mesh' not in st.session_state:
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO...</h1><p>Processando geometria 3D</p></div></div>', unsafe_allow_html=True)
            try:
                conteudo = io.BytesIO(arquivo.read())
                mesh = trimesh.load(conteudo, file_type='stl')
                st.session_state.mesh = mesh
                st.session_state.d_orig = mesh.extents
                pop_up.empty()
            except Exception as e:
                st.error(f"Erro no arquivo: {e}")
                st.stop()

    d_orig = st.session_state.d_orig
    
    st.subheader("📏 Medidas Atuais")
    c1, c2, c3 = st.columns(3)
    c1.metric("X", f"{d_orig[0]:.1f}mm", f"{d_orig[0]/10:.1f}cm")
    c2.metric("Y", f"{d_orig[1]:.1f}mm", f"{d_orig[1]/10:.1f}cm")
    c3.metric("Z", f"{d_orig[2]:.1f}mm", f"{d_orig[2]/10:.1f}cm")

    # --- PASSO 3: ESCALA ---
    st.write("---")
    st.subheader("🎯 3. Novo Tamanho")
    maior_lado_atual = float(max(d_orig))
    dim_alvo = st.number_input("Tamanho do MAIOR LADO desejado (mm):", value=maior_lado_atual, step=10.0)

    if st.button("✅ Confirmar Novas Medidas"):
        st.session_state.confirmado = True
        st.toast("Confirmado! Escolha as opções de corte abaixo.", icon="🚀")

    if st.session_state.get('confirmado'):
        f_escala = dim_alvo / maior_lado_atual
        d_novo = d_orig * f_escala
        st.info(f"💡 Tamanho Projetado: **{d_novo[0]/10:.1f}cm x {d_novo[1]/10:.1f}cm**")

        # Divisões inteligentes baseadas na mesa escolhida
        opcoes = [p for p in [1, 2, 4, 6, 8, 12, 16] if (dim_alvo/(p**0.5)) <= vol['x']]
        
        if not opcoes:
            st.error("❌ A peça não cabe. Diminua o tamanho ou use uma impressora maior.")
        else:
            qtd_partes = st.selectbox("Dividir em quantas partes para a mesa?", opcoes)

            # --- PASSO 4: GERAÇÃO ---
            if st.button("🚀 GERAR G-CODE REAL"):
                with pop_up.container():
                    st.markdown(f'<div class="loading-overlay"><div class="loading-box"><h1>🤖 FATIANDO...</h1><p>Configurando para {modelo}</p></div></div>', unsafe_allow_html=True)
                    try:
                        m_final = st.session_state.mesh.copy().apply_scale(f_escala)
                        m_final.export("temp.stl")
                        
                        subprocess.run(["slic3r", "temp.stl", "--output", "print.gcode"], check=True)
                        
                        buf = io.BytesIO()
                        with zipfile.ZipFile(buf, "w") as zf:
                            zf.write("print.gcode")
                            zf.writestr("Instrucoes.txt", f"Máquina: {modelo}\nPartes: {qtd_partes}")
                        
                        pop_up.empty()
                        st.balloons()
                        st.download_button("📥 BAIXAR PACOTE COMPLETO", buf.getvalue(), f"431_{modelo}.zip")
                    except Exception as e:
                        pop_up.empty()
                        st.error(f"Erro técnico: {e}")
else:
    st.session_state.confirmado = False
    st.info("Aguardando upload para iniciar a 431 3D for Dummies.")
