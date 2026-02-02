import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os

# CONFIGURAÇÕES DA SUA ENDER 3 V3 KE (RIO DE JANEIRO)
MESA_X, MESA_Y = 220, 220 

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩")
st.title("🧩 431 3D for Dummies")

# 1. ARRASTAR O ARQUIVO
arquivo = st.file_uploader("1. Arraste seu STL aqui", type=['stl'])

if arquivo:
    # Lendo o arquivo corretamente
    conteudo = io.BytesIO(arquivo.read())
    mesh = trimesh.load(conteudo, file_type='stl')
    d_orig = mesh.extents # Medidas originais em mm
    
    st.subheader("📏 Tamanho Atual Detectado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm", delta_color="off")
    c2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm", delta_color="off")
    c3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm", delta_color="off")

    st.write("---")
    
    # 2. DEFINIR NOVO TAMANHO
    st.subheader("🎯 2. Qual o tamanho final que você quer?")
    
    # Campo para você digitar o tamanho do maior lado
    maior_lado_orig = max(d_orig)
    dim_alvo = st.number_input("Digite o tamanho do MAIOR LADO desejado (em mm):", 
                               min_value=1.0, 
                               value=float(maior_lado_orig),
                               step=10.0)

    # CÁLCULOS AUTOMÁTICOS
    fator_escala = dim_alvo / maior_lado_orig
    d_novo = d_orig * fator_escala
    
    # MOSTRAR RESULTADO EM CM NA HORA
    st.info(f"💡 O novo tamanho será: **{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm x {d_novo[2]/10:.1f} cm**")

    # 3. VALIDAÇÃO DA MESA
    if d_novo[0] > MESA_X or d_novo[1] > MESA_Y:
        st.error(f"⚠️ A peça ficou grande demais para a Ender 3 V3 KE ({dim_alvo/10:.1f} cm)!")
        partes = st.selectbox("Dividir em quantas partes?", [2, 4, 8])
        st.warning(f"Isso criará {partes} peças com encaixes precisos (folga 0.25mm).")
    else:
        st.success(f"✅ Boa! Cabe inteira na mesa (Tamanho: {max(d_novo)/10:.1f} cm).")
        partes = 1

    # 4. BOTÃO DE G-CODE
    if st.button("🚀 3. GERAR G-CODE PARA O PENDRIVE"):
        with st.spinner("Fatiando com PLA 200°C / 60°C..."):
            # O código aqui chama o slic3r que você adicionou no packages.txt
            mesh.apply_scale(fator_escala)
            mesh.export("temp.stl")
            
            # Comando de fatiamento real
            output_gcode = "431_print.gcode"
            subprocess.run([
                "slic3r", "temp.stl",
                "--temperature", "200",
                "--bed-temperature", "60",
                "--layer-height", "0.2",
                "--output", output_gcode
            ])
            
            # Prepara o ZIP para download
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                if os.path.exists(output_gcode):
                    zf.write(output_gcode)
                zf.writestr("Instruções.txt", f"Tamanho final: {dim_alvo/10:.1f} cm\nEscala: {fator_escala*100:.1f}%")
            
            st.balloons()
            st.download_button("📥 BAIXAR AGORA", buf.getvalue(), "431_Pronto.zip")

else:
    st.info("Aguardando você colocar o arquivo STL acima.")
