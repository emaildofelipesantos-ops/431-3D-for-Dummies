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
        "Ender 3 Max Neo": {"x": 300, "y": 300, "z": 340},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "CR-M4": {"x": 450, "y": 450, "z": 470}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "A1": {"x": 256, "y": 256, "z": 256},
        "P1P / P1S": {"x": 256, "y": 256, "z": 256},
        "X1 Carbon / X1E": {"x": 256, "y": 256, "z": 256}
    },
    "Prusa": {
        "Mini+": {"x": 180, "y": 180, "z": 180},
        "MK4": {"x": 250, "y": 210, "z": 210},
        "XL": {"x": 360, "y": 360, "z": 360}
    },
    "Elegoo": {
        "Neptune 4 / 4 Pro": {"x": 225, "y": 225, "z": 265},
        "Neptune 4 Max": {"x": 420, "y": 420, "z": 480}
    },
    "Anycubic": {
        "Kobra 2 Neo/Pro": {"x": 220, "y": 220, "z": 250},
        "Kobra 2 Max": {"x": 420, "y": 420, "z": 500}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS PARA POP-UP DE LOADING CENTRAL (BLOQUEIO TOTAL)
st.markdown("""
    <style>
    .loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.95); display: flex; 
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loading-box {
        padding: 60px; border: 4px solid #00FF00; border-radius: 25px; 
        background: #000; color: #00FF00; text-align: center;
        box-shadow: 0 0 30px #00FF00; font-family: 'Courier New', Courier, monospace;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 431 3D for Dummies")

# --- PASSO 1: SELEÇÃO DE HARDWARE ---
st.subheader("🛠️ 1. Configuração da Impressora")
c_fab, c_mod = st.columns(2)
fabricante = c_fab.selectbox("Fabricante:", sorted(list(DATABASE.keys())))
modelo = c_mod.selectbox("Modelo:", sorted(list(DATABASE[fabricante].keys())))
vol = DATABASE[fabricante][modelo]

# --- PASSO 2: UPLOAD ---
arquivo = st.file_uploader("2. Arraste seu arquivo STL aqui", type=['stl'])
pop_up = st.empty()

if arquivo:
    if 'mesh' not in st.session_state:
        with pop_up.container():
            st.markdown('<div class="loading-overlay"><div class="loading-box"><h1>📦 ANALISANDO GEOMETRIA...</h1><p>Aguarde, o robô está medindo seu objeto.</p></div></div>', unsafe_allow_html=True)
            conteudo = io.BytesIO(arquivo.read())
            st.session_state.mesh = trimesh.load(conteudo, file_type='stl')
            st.session_state.d_orig = st.session_state.mesh.extents
            pop_up.empty()

    d_orig = st.session_state.d_orig
    
    # --- VISUALIZAÇÃO 3D E DADOS TÉCNICOS ---
    st.subheader("👁️ 3. Visualização e Medidas")
    
    # Exibição de medidas lado a lado (MM e CM)
    c1, c2, c3 = st.columns(3)
    c1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm")
    c2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm")
    c3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm")

    # Bloco de informações da malha (CORRIGIDO)
    st.json({
        "Volume Estimado": f"{st.session_state.mesh.volume/1000:.1f} cm³",
        "Complexidade (Faces)": len(st.session_state.mesh.faces),
        "Status da Malha": "Sólida e Pronta" if st.session_state.mesh.is_watertight else "Aviso: Malha com furos"
    })

    # --- PASSO 4: ESCALA E DIVISÃO ---
    st.write("---")
    st.subheader("🎯 4. Ajuste de Tamanho Final")
    dim_alvo = st.number_input("Novo tamanho para o MAIOR LADO (em mm):", value=float(max(d_orig)), step=10.0)

    if st.button("✅ Confirmar Escala e Calcular Cortes"):
        st.session_state.confirmado = True
        st.toast("Medidas confirmadas!", icon="📍")

    if st.session_state.get('confirmado'):
        f_escala = dim_alvo / max(d_orig)
        d_novo = d_orig * f_escala
        st.info(f"💡 Tamanho Final: **{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm x {d_novo[2]/10:.1f} cm**")

        # Filtro inteligente de divisões baseadas na mesa
        opcoes = [p for p in [1, 2, 4, 6, 8, 12, 16] if (dim_alvo/(p**0.5)) <= vol['x'] and (dim_alvo/(p**0.5)) <= vol['y']]
        
        if not opcoes:
            st.error(f"❌ Mesmo dividindo em 16, a peça não cabe na mesa da {modelo}. Diminua a escala.")
        else:
            qtd_partes = st.selectbox("Dividir em quantas partes? (Apenas opções compatíveis aparecem):", opcoes)

            # --- PASSO 5: GERAÇÃO DO G-CODE COM BLOQUEIO ---
            if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
                with pop_up.container():
                    st.markdown(f'<div class="loading-overlay"><div class="loading-box"><h1>🤖 FATIANDO G-CODE...</h1><p>Processando para {modelo}<br>PLA 200°C / 60°C</p></div></div>', unsafe_allow_html=True)
                    try:
                        m_final = st.session_state.mesh.copy().apply_scale(f_escala)
                        m_final.export("temp.stl")
                        
                        # Executa o motor Slic3r
                        subprocess.run(["slic3r", "temp.stl", "--output", "final.gcode"], check=True)
                        
                        buf = io.BytesIO()
                        with zipfile.ZipFile(buf, "w") as zf:
                            zf.write("final.gcode")
                            zf.writestr("Instruções_431.txt", f"Impressora: {modelo}\nEscala: {f_escala*100:.1f}%\nPartes: {qtd_partes}")
                        
                        pop_up.empty()
                        st.balloons()
                        st.download_button("📥 BAIXAR PACOTE COMPLETO", buf.getvalue(), f"431_{modelo}_Pronto.zip")
                    except Exception as e:
                        pop_up.empty()
                        st.error(f"Erro no processamento: {e}")
else:
    for key in ['mesh', 'd_orig', 'confirmado']:
        if key in st.session_state: del st.session_state[key]
    st.info("Aguardando upload para iniciar a configuração.")
