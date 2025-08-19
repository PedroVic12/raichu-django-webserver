import os
import sys
import streamlit as st
from pathlib import Path
import pandas as pd
from advanced_pdf_processor import AdvancedPDFProcessor
from excel_handler import ExcelHandler

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Sistema de Processamento de PDFs ONS",
    page_icon="📊",
    layout="wide"
)

def main():
    st.title("📊 Sistema de Processamento de PDFs ONS")
    
    # Sidebar para upload e configurações
    with st.sidebar:
        st.header("Configurações")
        
        # Upload do arquivo
        uploaded_file = st.file_uploader("📤 Carregar arquivo PDF", type=["pdf"])
        
        # Configurações de processamento
        st.subheader("Opções de Processamento")
        paginas = st.text_input("Páginas (ex: 1-3,5,7-9)", "all")
        
        col1, col2 = st.columns(2)
        with col1:
            usar_ocr = st.checkbox("Usar OCR", value=True)
        with col2:
            usar_camelot = st.checkbox("Usar Camelot", value=True)
        
        # Botão de processamento
        processar = st.button("Processar PDF", type="primary", use_container_width=True)
    
    # Área principal
    if uploaded_file is not None:
        with st.expander("📄 Visualização do PDF", expanded=True):
            st.write(f"**Arquivo:** {uploaded_file.name}")
            
            # Salva o arquivo temporariamente
            temp_dir = Path(tempfile.mkdtemp())
            temp_pdf = temp_dir / uploaded_file.name
            temp_pdf.write_bytes(uploaded_file.getvalue())
            
            # Inicializa o processador
            processor = AdvancedPDFProcessor(temp_pdf)
            
            # Exibe metadados
            with st.spinner("Analisando PDF..."):
                metadados = processor.gerar_metadados()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Páginas", metadados['total_paginas'])
                with col2:
                    st.metric("Tabelas", metadados['tabelas_encontradas'])
                with col3:
                    st.metric("Tamanho", metadados['tamanho_arquivo'])
            
            # Processa o PDF quando o botão for clicado
            if processar:
                with st.spinner("Processando PDF..."):
                    # Extrai texto
                    texto = processor.extrair_texto_pdf(paginas)
                    
                    # Extrai tabelas
                    tabelas = processor.extrair_tabelas(paginas, usar_camelot=usar_camelot)
                    
                    # Processa com PowerQuery
                    df_powerquery = processor.processar_com_powerquery()
                    
                    # Gera relatório Excel
                    excel_handler = ExcelHandler(temp_dir / f"relatorio_{uploaded_file.name}.xlsx")
                    
                    # Adiciona resumo
                    excel_handler.adicionar_resumo({
                        'nome_arquivo': uploaded_file.name,
                        'num_paginas': metadados['total_paginas'],
                        'num_tabelas_tabula': len(tabelas['tabula']),
                        'num_tabelas_camelot': len(tabelas['camelot']),
                        'paginas_processadas': paginas
                    })
                    
                    # Adiciona tabelas
                    if tabelas['tabula']:
                        excel_handler.adicionar_tabelas(tabelas['tabula'], "Tabelas_Tabula")
                    if tabelas['camelot']:
                        excel_handler.adicionar_tabelas(tabelas['camelot'], "Tabelas_Camelot")
                    if not df_powerquery.empty:
                        excel_handler.adicionar_tabelas([df_powerquery], "Dados_PowerQuery")
                    
                    # Adiciona texto extraído
                    excel_handler.adicionar_texto(texto, "Texto_Extraido")
                    
                    # Salva o relatório
                    caminho_relatorio = excel_handler.salvar()
                    
                    # Exibe o relatório
                    st.success("Processamento concluído com sucesso!")
                    st.download_button(
                        label="📥 Baixar Relatório",
                        data=Path(caminho_relatorio).read_bytes(),
                        file_name=f"relatorio_{uploaded_file.name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # Exibe prévia dos dados
                    st.subheader("Prévia dos Dados")
                    
                    tab1, tab2, tab3 = st.tabs(["Texto", "Tabelas (Tabula)", "Tabelas (Camelot)"])
                    
                    with tab1:
                        st.text_area("Texto Extraído", texto, height=300)
                    
                    with tab2:
                        if tabelas['tabula']:
                            st.dataframe(tabelas['tabula'][0].head())
                        else:
                            st.info("Nenhuma tabela extraída com Tabula.")
                    
                    with tab3:
                        if tabelas['camelot']:
                            st.dataframe(tabelas['camelot'][0].head())
                        else:
                            st.info("Nenhuma tabela extraída com Camelot.")

if __name__ == "__main__":
    # Adiciona o diretório atual ao path para importações
    sys.path.append(str(Path(__file__).parent))
    
    # Executa o Streamlit
    import streamlit.cli as stcli
    
    if st._is_running_with_streamlit:
        main()
    else:
        sys.argv = ["streamlit", "run", str(Path(__file__).absolute())]
        sys.exit(stcli.main())
