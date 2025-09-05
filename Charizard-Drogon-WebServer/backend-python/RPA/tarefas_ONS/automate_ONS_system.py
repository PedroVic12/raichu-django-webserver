import os
import re
import json
import pandas as pd
import tabula
import streamlit as st
import tempfile
from PyPDF2 import PdfReader
import google.generativeai as genai
import io
import pytesseract
from pdf2image import convert_from_path
from typing import List, Dict, Optional, Union
import camelot

# Import PowerQuery classes
from ClassPowerQuery import MiniPowerQuery

# Carregar variáveis de ambiente
#from dotenv import load_dotenv

#load_dotenv()

# --- Funções de Lógica de Negócio ---

PROMPT_USER = "Pegue o texto extraido do arquivo PDF e separe as informações em cada tabelas MUST e sua numeração no documento"

def gerar_resumo_com_gemini(texto):
    modelo = "gemini-2.5-pro"
    """Gera um resumo de um texto usando a API do Gemini."""
    st.info("🤖 Chamando a API do Gemini para gerar um resumo...")
    try:
        #genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        genai.configure(api_key="AIzaSyBMz4dNUD9FVFE7P7K_PD6I9URFm1REPy8")
        model = genai.GenerativeModel(modelo)
        prompt = f"{PROMPT_USER}\n\n{texto}"
        response = model.generate_content(prompt)
        return response.text if response and response.text else "Não foi possível gerar um resumo."
    except Exception as e:
        st.error(f"Erro ao chamar a API do Gemini: {e}")
        return "Falha ao gerar resumo."

def aplicar_regex_no_texto(texto, padroes_regex):
    """Aplica uma lista de padrões regex a um texto."""
    dados_regex = {}
    for nome, padrao in padroes_regex.items():
        match = re.search(padrao, texto, re.DOTALL)
        dados_regex[nome] = match.group(1).strip() if match else None
    return pd.DataFrame([dados_regex]) if dados_regex else pd.DataFrame()

# --- Funções de Extração de Dados ---

def extrair_texto_pypdf2(caminho_arquivo, paginas_str):
    """Extrai texto de páginas de um PDF usando PyPDF2."""
    texto_completo = ""
    reader = PdfReader(caminho_arquivo)
    paginas = parse_pages_string(paginas_str, len(reader.pages))
    for num_pagina in paginas:
        texto_completo += reader.pages[num_pagina].extract_text() or ""
    return texto_completo

def extrair_texto_ocr(caminho_arquivo, num_pagina):
    """Extrai texto de uma única página de um PDF usando Pytesseract OCR."""
    try:
        imagens = convert_from_path(caminho_arquivo, first_page=num_pagina, last_page=num_pagina)
        if imagens:
            return pytesseract.image_to_string(imagens[0], lang='por')
        return "Não foi possível converter a página para imagem."
    except Exception as e:
        st.error(f"Erro no OCR: {e}")
        st.warning("Certifique-se de que Tesseract e Poppler estão instalados.")
        return ""

def extrair_tabelas_avancado(caminho_arquivo, paginas_str, use_powerquery=True):
    """
    Extrai tabelas de um PDF usando múltiplas estratégias.
    
    Args:
        caminho_arquivo: Caminho para o arquivo PDF
        paginas_str: Páginas para processar (ex: '6-9', 'all')
        use_powerquery: Se True, aplica limpeza avançada nas tabelas
            - Remove linhas/colunas vazias
            - Remove duplicatas
            - Ajusta espaçamento
            - Corrige cabeçalhos
        
    Returns:
        Lista de DataFrames com as tabelas extraídas
    """
    try:
        # Tenta extrair com Camelot primeiro (melhor para tabelas bem formatadas)
        try:
            tables = camelot.read_pdf(
                caminho_arquivo,
                pages=paginas_str,
                flavor='lattice',
                strip_text='\n'
            )
            if tables:
                if use_powerquery:
                    return [processar_tabela_com_powerquery(table.df) for table in tables]
                return [table.df for table in tables]
        except Exception as e:
            st.warning(f"Aviso ao usar Camelot: {str(e)}")
        
        # Se Camelot falhar, tenta com Tabula
        try:
            tabelas = tabula.read_pdf(
                caminho_arquivo,
                pages=paginas_str,
                multiple_tables=True,
                stream=True,
                lattice=False,
                pandas_options={'header': None}
            )
            
            if not tabelas:
                st.info("Nenhuma tabela foi encontrada nas páginas especificadas.")
                return []
                
            if use_powerquery:
                return [processar_tabela_com_powerquery(df) for df in tabelas]
            return tabelas
            
        except JavaNotFoundError:
            st.error("Erro: Java não encontrado! O Tabula precisa do Java para funcionar.")
            st.warning("Por favor, instale o Java (JRE) em seu sistema e verifique se ele está no PATH.")
            return []
            
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao extrair as tabelas: {e}")
        return []

def processar_tabela_com_powerquery(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa um DataFrame usando MiniPowerQuery para limpeza e formatação.
    """
    # Cria um arquivo temporário para o MiniPowerQuery processar
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        temp_path = tmp.name
        df.to_csv(temp_path, index=False)
    
    try:
        # Processa com MiniPowerQuery
        mpq = MiniPowerQuery(temp_path)
        (mpq
         .trim_spaces()
         .drop_nulls(how='all')
         .drop_duplicates()
         .preview()
        )
        return mpq.df
    except Exception as e:
        st.warning(f"Aviso ao processar tabela com PowerQuery: {str(e)}")
        return df
    finally:
        # Remove o arquivo temporário
        try:
            os.unlink(temp_path)
        except:
            pass

# --- Funções Auxiliares ---

def parse_pages_string(paginas_str, total_paginas):
    """Converte a string de páginas (ex: '1-3,5') em uma lista de índices (base 0)."""
    if paginas_str.lower() == 'all':
        return list(range(total_paginas))
    
    paginas = set()
    faixas = paginas_str.replace(' ', '').split(',')
    for faixa in faixas:
        if '-' in faixa:
            inicio, fim = map(int, faixa.split('-'))
            paginas.update(range(inicio - 1, fim))
        else:
            paginas.add(int(faixa) - 1)
    return sorted(list(p for p in paginas if 0 <= p < total_paginas))

def df_to_excel_bytes(df):
    """Converte um único DataFrame para um objeto de bytes em formato Excel."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- Interface Principal do Streamlit ---

def main():
    st.set_page_config(layout="wide", page_icon="📄", page_title="Extrator de Dados de PDF", initial_sidebar_state="expanded")
    st.title("📄 Extrator de Dados de PDF")

    # Inicializar session state
    if 'texto_extraido' not in st.session_state:
        st.session_state.texto_extraido = ""
    if 'tabelas_extraidas' not in st.session_state:
        st.session_state.tabelas_extraidas = []
    if 'merged_df' not in st.session_state:
        st.session_state.merged_df = pd.DataFrame()

    # --- Sidebar com upload e detalhes do PDF ---
    with st.sidebar:
        st.header("Configuração")
        uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                st.session_state.caminho_arquivo_temp = tmp_file.name
            
            reader = PdfReader(st.session_state.caminho_arquivo_temp)
            num_pages = len(reader.pages)
            st.session_state.num_pages = num_pages

            st.subheader("Detalhes do PDF")
            st.write(f"**Nome:** {uploaded_file.name}")
            st.write(f"**Páginas:** {num_pages}")
            st.markdown("--- ")
            
            st.subheader("Visualizar Página")
            page_to_view = st.number_input(
                "Selecione uma página para ver:",
                min_value=1,
                max_value=num_pages,
                value=1,
                step=1,
                key="page_viewer"
            )
            if page_to_view:
                with st.spinner(f"Renderizando página {page_to_view}..."):
                    try:
                        images = convert_from_path(
                            st.session_state.caminho_arquivo_temp,
                            first_page=page_to_view,
                            last_page=page_to_view
                        )
                        if images:
                            st.image(images[0], caption=f"Página {page_to_view}", use_column_width=True)
                    except Exception as e:
                        st.error(f"Erro ao renderizar a página: {e}")

        else:
            st.session_state.caminho_arquivo_temp = None
            st.info("Aguardando upload de um arquivo PDF.")

    if not st.session_state.get('caminho_arquivo_temp'):
        st.warning("Por favor, faça o upload de um arquivo PDF na barra lateral para começar.")
        return

    # --- Abas de Funcionalidades ---
    tab1, tab2, tab3 = st.tabs(["📄 Extrair Texto (PyPDF2)", "👁️ Extrair Texto (OCR)", "📊 Extrair Tabelas (Tabula)"])

    with tab1:
        st.header("Extrair Texto com PyPDF2")
        paginas_pypdf2 = st.text_input("Páginas (ex: 1-3,5 ou 'all')", value='all', key="pypdf2_pages")
        if st.button("Extrair Texto", key="b_pypdf2"):
            with st.spinner("Extraindo texto..."):
                st.session_state.texto_extraido = extrair_texto_pypdf2(st.session_state.caminho_arquivo_temp, paginas_pypdf2)
            st.text_area("Texto Extraído", st.session_state.texto_extraido, height=300)

    with tab2:
        st.header("Extrair Texto com Pytesseract (OCR)")
        pagina_ocr = st.number_input("Selecione a Página", min_value=1, max_value=st.session_state.get('num_pages', 1), key="ocr_page")
        if st.button("Extrair com OCR", key="b_ocr"):
            with st.spinner(f"Processando OCR na página {pagina_ocr}..."):
                st.session_state.texto_extraido = extrair_texto_ocr(st.session_state.caminho_arquivo_temp, pagina_ocr)
            st.text_area("Texto Extraído por OCR", st.session_state.texto_extraido, height=300)

    with tab3:
        st.header("Extrair Tabelas")
        col1, col2 = st.columns(2)
        with col1:
            paginas_tabula = st.text_input(
                "Páginas (ex: 6-9 ou 'all')", 
                value='6-9',
                key="tabula_pages",
                help="Especifique o intervalo de páginas para extração. Ex: '6-9' para páginas 6 a 9"
            )
        with col2:
            use_powerquery = st.checkbox("Usar PowerQuery", value=True, 
                help="""Ativa o processamento avançado de tabelas:
                • Remove linhas/colunas vazias
                • Remove duplicatas
                • Ajusta espaçamento
                • Corrige cabeçalhos
                • Padroniza formatos""")
            
        if st.button("Extrair Tabelas", key="b_tabula"):
            with st.spinner("Extraindo tabelas..."):
                tabelas = extrair_tabelas_avancado(
                    st.session_state.caminho_arquivo_temp, 
                    paginas_tabula,
                    use_powerquery=use_powerquery
                )
                if tabelas is not None:
                    st.session_state.tabelas_extraidas = tabelas
                    st.session_state.merged_df = pd.DataFrame()
        
        if st.session_state.tabelas_extraidas:
            st.markdown("### Tabelas Encontradas")
            for i, df in enumerate(st.session_state.tabelas_extraidas):
                st.write(f"**Tabela {i+1}**")
                st.dataframe(df)
                excel_bytes = df_to_excel_bytes(df)
                st.download_button(
                    label=f"📥 Baixar Tabela {i+1} como XLSX",
                    data=excel_bytes,
                    file_name=f"tabela_{i+1}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_btn_{i}"
                )
                st.markdown("--- ")
            
            if st.button("Juntar Todas as Tabelas", key="b_merge"):
                with st.spinner("Juntando tabelas..."):
                    st.session_state.merged_df = pd.concat(st.session_state.tabelas_extraidas, ignore_index=True)
                st.success("Tabelas juntadas com sucesso!")
            
            if not st.session_state.merged_df.empty:
                st.markdown("### Tabela Unificada")
                st.dataframe(st.session_state.merged_df)
                st.download_button(
                    label="📥 Baixar Tabela Unificada como XLSX",
                    data=df_to_excel_bytes(st.session_state.merged_df),
                    file_name="tabelas_unificadas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_merged_btn"
                )

    st.markdown("--- ")
    # --- Expander para Ações Adicionais (Gemini e Regex) ---
    with st.expander("🤖 Opções Adicionais de Análise", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            usar_gemini = st.toggle("Analisar com Gemini")
            if usar_gemini and st.button("Executar Análise Gemini"):
                if st.session_state.texto_extraido:
                    resumo = gerar_resumo_com_gemini(st.session_state.texto_extraido)
                    st.markdown("### Resumo Gemini")
                    st.markdown(resumo)
                elif not st.session_state.merged_df.empty:
                    texto_tabelas = st.session_state.merged_df.to_string()
                    resumo = gerar_resumo_com_gemini(texto_tabelas)
                    st.markdown("### Resumo Gemini da Tabela Unificada")
                    st.markdown(resumo)
                elif st.session_state.tabelas_extraidas:
                    texto_tabelas = "\n\n".join([df.to_string() for df in st.session_state.tabelas_extraidas])
                    resumo = gerar_resumo_com_gemini(texto_tabelas)
                    st.markdown("### Resumo Gemini das Tabelas")
                    st.markdown(resumo)
                else:
                    st.warning("Nenhum texto ou tabela foi extraído ainda. Extraia dados em uma das abas acima primeiro.")

        with col2:
            usar_regex = st.toggle("Aplicar Regex")
            if usar_regex:
                default_regex = json.dumps({"CNPJ": r"CNPJ:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", "Valor_Total": r"Valor Total:\s*R\$?([\d,\.]+)"}, indent=4)
                regex_input = st.text_area("Padrões Regex (JSON)", value=default_regex, height=150)
                if st.button("Executar Regex"):
                    if st.session_state.texto_extraido:
                        padroes = json.loads(regex_input)
                        df_regex = aplicar_regex_no_texto(st.session_state.texto_extraido, padroes)
                        st.markdown("### Resultado do Regex")
                        st.dataframe(df_regex)
                    else:
                        st.warning("Não há texto extraído para aplicar Regex. Use a aba de extração de texto primeiro.")

if __name__ == '__main__':
    main()