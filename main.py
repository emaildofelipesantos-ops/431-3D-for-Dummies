import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os

# CONFIGURAÇÕES FIXAS - ENDER 3 V3 KE
MESA_X, MESA_Y = 220, 220 

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩")
st.title("🧩 431 3D for Dummies")

# 1. CARREGAMENTO DO ARQUIVO
arquivo = st.file_uploader("1. Arraste seu arquivo STL aqui", type=['stl'])

if arquivo:
    # Lendo o modelo
    conteudo = io.BytesIO(arquivo.read())
    mesh = trimesh.load(conteudo, file_type='stl')
    d_orig = mesh.extents # Medidas em mm
    
    st.subheader("📏 Tamanho Atual Detectado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm", delta_color="off")
    c2.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm", delta_color="off")
    c3.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm", delta_color="off")

    st.write("---")
    
    # 2. DEFINIR NOVO TAMANHO COM ATUALIZAÇÃO IMEDIATA
    st.subheader("🎯 2. Defina o novo tamanho")
    
    # Pegamos o maior lado atual para sugerir como padrão
    maior_lado_atual = float(max(d_orig))
    
    # O segredo está aqui: ao mudar esse número, o script roda todo de novo
    dim_alvo = st.number_input(
        "Digite o tamanho desejado para o MAIOR LADO (em mm):", 
        min_value=1.0, 
        value=maior_lado_atual,
        step=10.0,
        key="input_tamanho"
    )

    # Cálculos automáticos de escala
    fator_escala = dim_alvo / maior_lado_atual
    d_novo = d_orig * fator_escala
    
    # Exibe o resultado em CM imediatamente abaixo
    st.info(f"💡 O novo tamanho será: **{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm x {d_novo[2]/10:.1f} cm**")

    # 3. VERIFICAÇÃO DE CAPACIDADE
    if d_novo[0] > MESA_X or d_novo[1] > MESA_Y:
        st.error(f"⚠️ Alerta: Esse tamanho ({dim_alvo/10:.1f} cm) não cabe na sua Ender 3 V3 KE!")
        st.warning("A ferramenta precisará cortar o modelo para você imprimir.")
    else:
        st.success(f"✅ Excelente! Cabe inteira na mesa (Máximo: {max(d_novo)/10:.1f} cm).")

    # 4. GERAÇÃO DO G-CODE REAL
    if st.button("🚀 3. GERAR G-CODE REAL"):
        with st.spinner("Fatiando para PLA (200°C / 60°C)..."):
            # Aplicar escala no modelo 3D
            mesh.apply_scale(fator_escala)
            mesh.export("final.stl")
            
            # Comando de fatiamento usando o motor que instalamos no packages.txt
            output_gcode = "print_431.gcode"
            try:
                subprocess.run([
                    "slic3r", "final.stl",
                    "--temperature", "200",
                    "--bed-temperature", "60",
                    "--layer-height", "0.2",
                    "--output", output_gcode
                ], check=True)
                
                # Criar o ZIP real para não dar erro ao abrir
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w") as zf:
                    if os.path.exists(output_gcode):
                        zf.write(output_gcode)
                    zf.writestr("Configuracao.txt", f"Tamanho final: {dim_alvo/10:.1f} cm\nEscala: {fator_escala*100:.1f}%")
                
                st.balloons()
                st.success("G-Code pronto para o pendrive!")
                st.download_button("📥 BAIXAR AGORA", buf.getvalue(), "431_Pronto.zip")
            except:
                st.error("Ocorreu um erro ao fatiar. Verifique se o arquivo 'packages.txt' contém a palavra 'slic3r'.")
else:
    st.info("Aguardando você carregar o arquivo STL acima.")
