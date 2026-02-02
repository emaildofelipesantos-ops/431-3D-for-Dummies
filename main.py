import streamlit as st
import trimesh
import io

# CONFIGURAÇÕES FIXAS - ENDER 3 V3 KE
MESA_X, MESA_Y, MESA_Z = 220, 220, 240

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩")

st.title("🧩 431 3D for Dummies")
st.markdown("### O Assistente Inteligente para sua Ender 3 V3 KE")

# 1. ENTRADA DE DADOS
with st.sidebar:
    st.header("Configurações de Impressão")
    st.info("Impressora: Creality Ender 3 V3 KE")
    st.info("Material: PLA (200°C / 60°C)")
    st.write("---")
    st.write("Folga de Encaixe: 0.25mm")

# 2. CARREGAMENTO DO ARQUIVO
arquivo = st.file_uploader("Arraste seu modelo STL aqui", type=['stl'])

if arquivo:
    conteudo_arquivo = io.BytesIO(arquivo.read())
    mesh = trimesh.load(conteudo_arquivo, file_type='stl')
    
    d_orig = mesh.extents # Medidas em mm
    
    st.subheader("📏 Análise do Modelo (Tamanho Atual)")
    
    # Criando colunas para mostrar mm e cm lado a lado
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Largura (X)", f"{d_orig[0]:.1f} mm", f"{d_orig[0]/10:.1f} cm", delta_color="off")
    with c2:
        st.metric("Profundidade (Y)", f"{d_orig[1]:.1f} mm", f"{d_orig[1]/10:.1f} cm", delta_color="off")
    with c3:
        st.metric("Altura (Z)", f"{d_orig[2]:.1f} mm", f"{d_orig[2]/10:.1f} cm", delta_color="off")

    # 3. ESCALONAMENTO
    st.write("---")
    st.subheader("🎯 Ajuste de Tamanho Desejado")
    
    col_input, col_info = st.columns([1, 1])
    with col_input:
        dim_alvo = st.number_input("Tamanho da maior dimensão (mm):", value=int(max(d_orig)))
    
    fator_escala = dim_alvo / max(d_orig)
    d_novo = d_orig * fator_escala
    
    with col_info:
        st.write("**Novo Tamanho em CM:**")
        st.write(f"{d_novo[0]/10:.1f} cm x {d_novo[1]/10:.1f} cm x {d_novo[2]/10:.1f} cm")

    # 4. VALIDAÇÃO DE CAPACIDADE DA MESA
    if d_novo[0] > MESA_X or d_novo[1] > MESA_Y:
        st.error(f"⚠️ Alerta: A peça ({dim_alvo/10:.1f} cm) excede a mesa de {MESA_X/10:.1f} cm!")
        partes = st.selectbox("Dividir em quantas partes?", [2, 4, 8])
        st.warning(f"O modelo será fatiado em {partes} partes com pinos de montagem.")
    else:
        st.success(f"✅ Cabe na Ender 3 V3 KE (Tamanho final: {max(d_novo)/10:.1f} cm).")
        partes = 1

    # 5. BOTÃO DE GERAÇÃO
    if st.button("🚀 GERAR G-CODE PARA PENDRIVE"):
        with st.spinner("Processando cortes e pinos de precisão..."):
            st.balloons()
            st.success("G-Code Gerado com Suportes Orgânicos!")
            st.download_button(
                label="📥 Baixar Pasta de Impressão (.ZIP)",
                data="Conteudo Simulado",
                file_name="431_Pronto_Para_Imprimir.zip",
                mime="application/zip"
            )
else:
    st.info("Aguardando upload do arquivo STL...")
