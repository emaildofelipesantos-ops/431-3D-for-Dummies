import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# BANCO DE DADOS DE IMPRESSORAS
PRINTERS = {
    "Creality Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
    "Creality Ender 3 S1": {"x": 220, "y": 220, "z": 270},
    "Bambu Lab P1P/X1C": {"x": 256, "y": 256, "z": 256},
    "Prusa MK4": {"x": 250, "y": 210, "z": 250}
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS para o POP-UP DE LOADING CENTRALIZADO
st.markdown("""
    <style>
    .loading-overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.7);
        display: flex; justify-content: center; align-items: center;
        z-index: 9999; color: white; flex-direction: column;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 431 3D for Dummies")

# --- PASSO 1: ESCOLHA DA IMPRESSORA ---
st.subheader("🛠️ 1. Configuração da Máquina")
printer_name = st.selectbox("Selecione sua Impressora 3D:", list(PRINTERS.keys()))
vol = PRINTERS[printer_name]
st.info(f"Capacidade máxima: {vol['x']}x{vol['y']}mm (Mesa)")

# --- PASSO 2: UPLOAD ---
arquivo = st.file_uploader("2. Arraste seu arquivo STL aqui", type=['stl'])

if arquivo:
    if 'mesh' not in st.session_state:
        # POP-UP CENTRAL DE CARREGAMENTO
        with st.spinner("📦 BLOQUEANDO TELA: Analisando geometria do modelo..."):
            conteudo = io.BytesIO(arquivo.read())
            mesh = trimesh.load(conteudo, file_type='stl')
            st.session_state.mesh = mesh
            st.session_state.d_orig = mesh.extents
            st.toast("Modelo carregado com sucesso!", icon="✅")

    d_orig = st.session_state.d_orig

    st.subheader("📏 Tamanho Atual Detectado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm")
    c2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm")
    c3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm")

    # --- PASSO 3: TAMANHO DESEJADO ---
    st.write("---")
    st.subheader("🎯 3. Defina o novo tamanho")
    maior_lado_atual = float(max(d_orig))
    dim_alvo = st.number_input("Tamanho do MAIOR LADO desejado (mm):", value=maior_lado_atual, step=10.0)

    if st.button("✅ Confirmar Medidas"):
        st.session_state.confirmado = True
        st.toast("Medidas confirmadas!", icon="📍")

    if st.session_state.get('confirmado'):
        fator_escala = dim_alvo / maior_lado_atual
        d_novo = d_orig * fator_escala
        st.info(f"💡 Tamanho Final: **{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm**")

        # --- PASSO 4: DIVISÃO INTELIGENTE ---
        st.subheader("🧩 4. Divisões Sugeridas")
        
        # Lógica: Filtra apenas opções que fazem a peça caber na mesa
        opcoes_validas = []
        for p in [1, 2, 4, 6, 8, 12]:
            # Divisão simplificada de área: assume corte em grade
            dim_parte = dim_alvo / (p**0.5) 
            if dim_parte <= vol['x'] and dim_parte <= vol['y']:
                opcoes_validas.append(p)
        
        if not opcoes_validas:
            st.error("❌ Nem dividindo em 12 a peça cabe. Diminua o tamanho!")
        else:
            if 1 in opcoes_validas and len(opcoes_validas) == 1:
                st.success("✅ A peça cabe inteira!")
                partes_qtd = 1
            else:
                partes_qtd = st.selectbox(
                    "Selecione em quantas partes dividir (Apenas opções compatíveis):",
                    opcoes_validas,
                    index=len(opcoes_validas)-1 if 1 not in opcoes_validas else 0
                )

            # --- PASSO 5: GERAÇÃO COM LOADING CENTRAL ---
            if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
                # Simulação de bloqueio de tela centralizado
                placeholder = st.empty()
                with placeholder.container():
                    st.markdown(f'<div class="loading-overlay"><h1>🤖 TRABALHANDO NO G-CODE...</h1><p>Escalonando e fatiando para {printer_name}</p></div>', unsafe_allow_html=True)
                    
                    try:
                        # Processamento real
                        mesh_final = st.session_state.mesh.copy()
                        mesh_final.apply_scale(fator_escala)
                        mesh_final.export("temp.stl")
                        
                        subprocess.run(["slic3r", "temp.stl", "--output", "final.gcode"], check=True)
                        
                        buf = io.BytesIO()
                        with zipfile.ZipFile(buf, "w") as zf:
                            zf.write("final.gcode")
                        
                        placeholder.empty() # Remove o loading central
                        st.balloons()
                        st.download_button("📥 BAIXAR AGORA", buf.getvalue(), "431_Pronto.zip")
                    except Exception as e:
                        placeholder.empty()
                        st.error(f"Erro no motor de fatiamento: {e}")

else:
    # Reseta a sessão se o arquivo for removido
    for key in ['mesh', 'd_orig', 'confirmado']:
        if key in st.session_state: del st.session_state[key]
    st.info("Aguardando upload para iniciar a 431 3D for Dummies.")
