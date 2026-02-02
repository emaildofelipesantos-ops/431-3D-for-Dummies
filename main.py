import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os

# CONFIGURAÇÕES ENDER 3 V3 KE
MESA = {'X': 220, 'Y': 220, 'Z': 240}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩")
st.title("🧩 431 3D for Dummies")

arquivo = st.file_uploader("Arraste seu STL", type=['stl'])

if arquivo:
    conteudo_arquivo = io.BytesIO(arquivo.read())
    mesh = trimesh.load(conteudo_arquivo, file_type='stl')
    
    # Exibição mm e cm lado a lado
    d_orig = mesh.extents
    st.subheader("📏 Tamanho Detectado")
    c1, c2 = st.columns(2)
    c1.metric("Largura", f"{d_orig[0]:.1f}mm", f"{d_orig[0]/10:.1f}cm", delta_color="off")
    c2.metric("Altura", f"{d_orig[2]:.1f}mm", f"{d_orig[2]/10:.1f}cm", delta_color="off")

    dim_alvo = st.number_input("Tamanho final desejado (maior lado em mm):", value=int(max(d_orig)))
    fator = dim_alvo / max(d_orig)
    
    if st.button("🚀 GERAR G-CODE REAL"):
        with st.spinner("Fatiando para Ender 3 V3 KE..."):
            mesh.apply_scale(fator)
            temp_stl = "temp_model.stl"
            mesh.export(temp_stl)

            gcode_file = "projeto_431.gcode"
            # Comando que aciona o motor de fatiamento
            comando = [
                "slic3r", temp_stl,
                "--layer-height", "0.2",
                "--temperature", "200",
                "--first-layer-temperature", "200",
                "--bed-temperature", "60",
                "--fill-density", "15%",
                "--output", gcode_file
            ]
            
            try:
                subprocess.run(comando, check=True)
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w") as zf:
                    if os.path.exists(gcode_file):
                        zf.write(gcode_file)
                
                st.success("G-Code pronto para o pendrive!")
                st.download_button("📥 Baixar G-Code (.ZIP)", buf.getvalue(), "431_Ender3_V3KE.zip")
            except:
                st.error("Erro no motor de fatiamento. Verifique o arquivo packages.txt.")
