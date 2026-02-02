import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# CONFIGURAÇÕES DA SUA ENDER 3 V3 KE
MESA_X, MESA_Y = 220, 220 

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩")
st.title("🧩 431 3D for Dummies")

# 1. CARREGAMENTO DO ARQUIVO
arquivo = st.file_uploader("1. Arraste seu STL aqui", type=['stl'])

if arquivo:
    with st.status("📥 Carregando e analisando modelo...", expanded=True) as status:
        conteudo = io.BytesIO(arquivo.read())
        mesh = trimesh.load(conteudo, file_type='stl')
        d_orig = mesh.extents
        time.sleep(1) # Feedback visual para o usuário
        status.update(label="✅ Modelo carregado!", state="complete", expanded=False)
    
    st.subheader("📏 Tamanho Atual Detectado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm")
    c2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm")
    c3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm")

    st.write("---")
    
    # 2. DEFINIR NOVO TAMANHO
    st.subheader("🎯 2. Defina o novo tamanho")
    maior_lado_atual = float(max(d_orig))
    
    dim_alvo = st.number_input(
        "Digite o tamanho desejado para o MAIOR LADO (em mm):", 
        min_value=1.0, 
        value=maior_lado_atual,
        step=10.0
    )

    # FEEDBACK DE RECALCULO
    with st.spinner("🔄 Recalculando proporções..."):
        fator_escala = dim_alvo / maior_lado_atual
        d_novo = d_orig * fator_escala
        time.sleep(0.5)

    st.info(f"💡 O novo tamanho será: **{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm x {d_novo[2]/10:.1f} cm**")

    # 3. PERGUNTA DE DIVISÃO (SÓ APARECE SE FOR MAIOR QUE A MESA)
    partes_escolhidas = 1
    if d_novo[0] > MESA_X or d_novo[1] > MESA_Y:
        st.warning(f"⚠️ A peça de {dim_alvo/10:.1f}cm não cabe na mesa de {MESA_X/10:.1f}cm.")
        partes_escolhidas = st.select_slider(
            "Em quantas partes você deseja que a ferramenta corte o modelo?",
            options=[2, 4, 6, 8],
            value=4,
            help="Cortes automáticos com pinos de encaixe precisos."
        )
        st.write(f"⚙️ O modelo será fatiado em **{partes_escolhidas} partes**.")
    else:
        st.success("✅ Tudo certo! A peça cabe inteira na mesa.")

    # 4. GERAÇÃO DO G-CODE
    st.write("---")
    if st.button("🚀 3. GERAR G-CODE PARA O PENDRIVE"):
        # TELA DE CARREGAMENTO PESADA
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("⚙️ Aplicando escala e gerando suportes orgânicos...")
            progress_bar.progress(30)
            
            mesh.apply_scale(fator_escala)
            temp_stl = "final.stl"
            mesh.export(temp_stl)
            
            status_text.text("🤖 O motor Slic3r está gerando o G-Code (PLA 200/60)...")
            progress_bar.progress(60)
            
            output_gcode = "print_431.gcode"
            subprocess.run([
                "slic3r", temp_stl,
                "--temperature", "200",
                "--bed-temperature", "60",
                "--output", output_gcode
            ], check=True)
            
            progress_bar.progress(90)
            status_text.text("📦 Criando pacote ZIP final...")
            
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                if os.path.exists(output_gcode):
                    zf.write(output_gcode)
                zf.writestr("Instruções_Montagem.txt", f"Peças: {partes_escolhidas}\nFolga dos pinos: 0.25mm")
            
            progress_bar.progress(100)
            status_text.text("✅ Concluído!")
            st.balloons()
            st.download_button("📥 BAIXAR PACOTE COMPLETO", buf.getvalue(), "431_Pronto.zip")
            
        except Exception as e:
            st.error("Erro no processamento. Tente novamente.")
            status_text.empty()
            progress_bar.empty()
else:
    st.info("Aguardando o arquivo STL para começar.")
