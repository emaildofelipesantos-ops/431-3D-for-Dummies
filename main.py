import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# CONFIGURAÇÕES DA SUA ENDER 3 V3 KE
MESA_X, MESA_Y = 220, 220 

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout="centered")

# CSS para garantir que as mensagens de carregamento fiquem bem destacadas no centro
st.markdown("""
    <style>
    .stAlert { margin-top: 20px; text-align: center; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 431 3D for Dummies")

# Espaço reservado no TOPO/CENTRO para avisos de trabalho
aviso_central = st.empty()

# 1. CARREGAMENTO DO ARQUIVO
arquivo = st.file_uploader("1. Arraste seu STL aqui", type=['stl'])

if arquivo:
    if 'confirmado' not in st.session_state:
        st.session_state.confirmado = False

    if 'analisado' not in st.session_state:
        with aviso_central.container():
            st.warning("⚠️ **TRABALHANDO:** Analisando geometria do modelo...")
            conteudo = io.BytesIO(arquivo.read())
            mesh = trimesh.load(conteudo, file_type='stl')
            st.session_state.mesh = mesh
            st.session_state.d_orig = mesh.extents
            st.session_state.analisado = True
            time.sleep(1)
            aviso_central.empty()
    
    d_orig = st.session_state.d_orig

    st.subheader("📏 Tamanho Atual Detectado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm")
    c2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm")
    c3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm")

    st.write("---")
    
    # 2. DEFINIR NOVO TAMANHO
    st.subheader("🎯 2. Defina o novo tamanho")
    maior_lado_atual = float(max(d_orig))
    dim_alvo = st.number_input("Tamanho do MAIOR LADO desejado (mm):", value=maior_lado_atual)

    if st.button("✅ Confirmar Medidas"):
        with aviso_central.container():
            st.warning("🔄 **TRABALHANDO:** Aplicando novas dimensões...")
            time.sleep(1)
            st.session_state.confirmado = True
            aviso_central.empty()

    if st.session_state.confirmado:
        fator_escala = dim_alvo / maior_lado_atual
        d_novo = d_orig * fator_escala
        st.info(f"💡 Novo tamanho: **{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm x {d_novo[2]/10:.1f} cm**")

        # 3. DIVISÃO
        partes_escolhidas = 1
        if d_novo[0] > MESA_X or d_novo[1] > MESA_Y:
            st.warning("⚠️ Peça excede a mesa da Ender 3 V3 KE.")
            partes_escolhidas = st.select_slider("Dividir em:", options=[2, 4, 6, 8], value=4)

        # 4. GERAÇÃO DO G-CODE (CORREÇÃO DO ERRO DE SINTAXE)
        if st.button("🚀 3. GERAR G-CODE REAL"):
            with aviso_central.container():
                st.header("🤖 **PROCESSANDO G-CODE**")
                barra = st.progress(0)
                msg = st.empty()
                
                try:
                    msg.write("📐 Ajustando escala para 200°C/60°C...")
                    barra.progress(30)
                    
                    mesh_final = st.session_state.mesh.copy()
                    mesh_final.apply_scale(fator_escala)
                    
                    # CORREÇÃO DA LINHA 87 (Parêntese fechado corretamente)
                    temp_stl = "final.stl"
                    mesh_final.export(temp_stl)
                    
                    msg.write("⚙️ Motor Slic3r trabalhando... Aguarde.")
                    barra.progress(70)
                    
                    output_gcode = "print_431.gcode"
                    subprocess.run(["slic3r", temp_stl, "--output", output_gcode], check=True)
                    
                    barra.progress(100)
                    st.success("✅ G-Code Gerado com Sucesso!")
                    
                    # Criação do ZIP Real
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w") as zf:
                        if os.path.exists(output_gcode):
                            zf.write(output_gcode)
                        zf.writestr("Instruções.txt", f"Tamanho: {dim_alvo/10:.1f} cm\nEscala: {fator_escala*100:.1f}%")
                    
                    st.download_button("📥 BAIXAR AGORA", buf.getvalue(), "431_Pronto.zip")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")
else:
    st.session_state.confirmado = False
    st.session_state.analisado = False
    st.info("Aguardando upload para iniciar.")
