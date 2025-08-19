import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Análise MUST",
    page_icon="📊",
    layout="wide"
)

# --- Funções de Lógica e Processamento ---

def standardize_columns(df):
    """
    Renomeia as colunas do DataFrame para um formato padronizado,
    inspirado na lógica de transformação do Power Query.
    """
    rename_map = {}
    for col in df.columns:
        clean_col = col.strip().replace('\n', ' ')
        
        # Colunas de Identificação
        if re.search(r'Instalação', clean_col, re.IGNORECASE):
            rename_map[col] = 'Instalacao'
        
        # Colunas de 2025
        elif re.search(r'MUST - 2025 Ponta.*Valor', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2025_Valor'
        elif re.search(r'MUST - 2025 Ponta.*Anotacao', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2025_Anotacao'
        elif re.search(r'Fora\s*Ponta.*Valor', clean_col, re.IGNORECASE) and not re.search(r'[123]', clean_col):
            rename_map[col] = 'Fora_Ponta_2025_Valor'
            
        # Colunas de 2026
        elif re.search(r'MUST - 2026 Ponta.*Valor', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2026_Valor'
        elif re.search(r'MUST - 2026 Ponta.*Anotacao', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2026_Anotacao'
        elif re.search(r'Fora\s*Ponta.*1.*Valor', clean_col, re.IGNORECASE):
            rename_map[col] = 'Fora_Ponta_2026_Valor'
            
        # Colunas de 2027
        elif re.search(r'MUST - 2027 Ponta.*Valor', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2027_Valor'
        elif re.search(r'MUST - 2027 Ponta.*Anotacao', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2027_Anotacao'
        elif re.search(r'Fora\s*Ponta.*2.*Valor', clean_col, re.IGNORECASE):
            rename_map[col] = 'Fora_Ponta_2027_Valor'
            
        # Colunas de 2028
        elif re.search(r'MUST - 2028 Ponta.*Valor', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2028_Valor'
        elif re.search(r'MUST - 2028 Ponta.*Anotacao', clean_col, re.IGNORECASE):
            rename_map[col] = 'Ponta_2028_Anotacao'
        elif re.search(r'Fora\s*Ponta.*3.*Valor|MUST - 2028 Fora Ponta.*Valor', clean_col, re.IGNORECASE):
            rename_map[col] = 'Fora_Ponta_2028_Valor'
            
    df.rename(columns=rename_map, inplace=True)
    return df

# --- Carregamento e Cache dos Dados ---
@st.cache_data
def load_all_data():
    """
    Carrega todos os dados CSV de strings, padroniza as colunas e retorna
    um dicionário de DataFrames do Pandas.
    """
    cpfl_paulista_csv_data = """Ponto de Conexão Cód ONS¹,Instalação," Tensão\n(kV)","Período de\nContratação De",Até,"MUST - 2025 Ponta\n(MW) Valor","MUST - 2025 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) Valor"," Fora\nPonta\n(MW) Anotacao","MUST - 2026 Ponta\n(MW) Valor","MUST - 2026 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 1 Valor"," Fora\nPonta\n(MW) 1 Anotacao","MUST - 2027 Ponta\n(MW) Valor","MUST - 2027 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 2 Valor"," Fora\nPonta\n(MW) 2 Anotacao","MUST - 2028 Ponta\n(MW) Valor","MUST - 2028 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 3 Valor"," Fora\nPonta\n(MW) 3 Anotacao"
SPAJIV138-A,"AJINOMOTO VAL - 138\nkV (A)",138,1/Jan,31/Dez,"115,200",{(I)},"107,100",{(I)},"115,200",{(I)},"107,100",{(I)},"115,200",{(I)},"107,100",{(I)},"115,200",{(I)},"107,100",{(I)}
SPBAR-138,BARIRI - 138 kV (A),138,1/Jan,31/Dez,"20,000",,"24,500",,"20,000",,"24,500",,"20,000",,"24,500",,"20,000",,
SPIAC-138-A,IACANGA - 138 kV (A),138,1/Jan,31/Dez,"17,000",{(A)},"18,400",{(A)},"17,000",{(A)},"18,400",{(A)},"17,000",{(A)},"16,500",{(A)},"14,500",{(A)},
SPIBG-138,IBITINGA-SE - 138 kV (A),138,1/Jan,31/Dez,"55,100",{(C)},"59,900",{(C)},"55,100",{(C)},"59,900",{(C)},"55,100",{(C)},"59,900",{(C)},"55,100",{(C)},
SPPEN-138,PENAPOLIS - 138 kV (A),138,1/Jan,31/Dez,"40,000",,"40,000",,"40,000",,"40,000",,"40,000",,"40,000",,"40,000",,
"""
    piratininga_csv_data = """Ponto de Conexão Cód ONS¹,Instalação," Tensão\n(kV)","Período de\nContratação De",Até,"MUST - 2025 Ponta\n(MW) Valor","MUST - 2025 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) Valor"," Fora\nPonta\n(MW) Anotacao","MUST - 2026 Ponta\n(MW) Valor","MUST - 2026 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 1 Valor"," Fora\nPonta\n(MW) 1 Anotacao","MUST - 2027 Ponta\n(MW) Valor","MUST - 2027 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 2 Valor"," Fora\nPonta\n(MW) 2 Anotacao","MUST - 2028 Ponta\n(MW) Valor","MUST - 2028 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 3 Valor"," Fora\nPonta\n(MW) 3 Anotacao"
SPBOT2138-A,AGUA BRANCA - 138 kV (A),138,1/Jan,31/Dez,"33,800",,"36,100",,"34,200",,"36,500",,"34,600",,"36,900",,"35,000",,"37,400",
SPBSA-88,B. SANTISTA - 88 kV (A),88,1/Jan,31/Dez,"202,500",,"202,500",,"202,500",,"202,500",,"202,500",,"202,500",,"202,500",,
SPBOJ-88,BOM JARDIM - 88 kV (A),88,1/Jan,31/Dez,"417,000","{(A)}\n(B)","465,000","{(A)}\n(B)","417,000","{(A)}\n(B)","465,000","{(A)}\n(B)","433,000","{(A)}\n(B)","468,000","{(A)}\n(B)","433,000","{(A)}\n(B)","468,300","{(A)}\n(B)"
"SPVIC-13,8","VIC. CARVALHO - 13,8 kV (A)",13,1/Jan,31/Dez,"36,200",,"36,200",{(A)},-,-,,"32,940",,"32,940",{(A)},"32,940",,"32,940",{(A)},,
"""
    neoenergia_elektro_csv_data = """Ponto de Conexão Cód ONS¹,Instalação," Tensão\n(kV)","Período de\nContratação De",Até,"MUST - 2025 Ponta\n(MW) Valor","MUST - 2025 Ponta\n(MW) Anotacao",Coluna7," Fora\nPonta\n(MW) Valor"," Fora\nPonta\n(MW) Anotacao","MUST - 2026 Ponta\n(MW) Valor","MUST - 2026 Ponta\n(MW) Anotacao",Coluna10," Fora\nPonta\n(MW) 1 Valor"," Fora\nPonta\n(MW) 1 Anotacao","MUST - 2027 Ponta\n(MW) Valor","MUST - 2027 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 2 Valor"," Fora\nPonta\n(MW) 2 Anotacao"," Ponta\n(MW) Valor"," Ponta\n(MW) Anotacao","MUST - 2028 Fora\nPonta\n(MW) Valor","MUST - 2028 Fora\nPonta\n(MW) Anotacao"
SPVOT1138,VOTUPORANGA 1 - 138 kV (A),138,1/Jul,31/Dez,"51,800","{(A)}\n(B)",,"66,000",{(B)},-,-,,-,,-,,-,,-,,-,
SPVOT1138,VOTUPORANGA 1 - 138 kV (A),138,1/Jan,31/Dez,-,-,,-,,"51,800","{(A)}\n(B)",,"66,000",{(B)},"51,800","{(A)}\n(B)","66,000",{(B)},"51,800",{(B)},"66,000",{(B)}
SPCEDA138-A,CEDASA - 138 kV (A),138,1/Jan,31/Jul,"43,700",,,"46,800",,-,,-,,-,,-,,-,,-,
SPCEDA138-A,CEDASA - 138 kV (A),138,1/Ago,31/Dez,"45,100",{(A)},,"47,300",{(A)},-,-,,-,,-,,-,,-,,-,,-,
"""
    eletropaulo_csv_data = """Cód ONS,Instalação," Tensão\n(kV)","Período de\nContratação De",Até,"MUST - 2025 Ponta\n(MW) Valor","MUST - 2025 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) Valor"," Fora\nPonta\n(MW) Anotacao","MUST - 2026 Ponta\n(MW) Valor","MUST - 2026 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 1 Valor"," Fora\nPonta\n(MW) 1 Anotacao","MUST - 2027 Ponta\n(MW) Valor","MUST - 2027 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 2 Valor"," Fora\nPonta\n(MW) 2 Anotacao"," Ponta\n(MW) Valor"," Ponta\n(MW) Anotacao","MUST - 2028 Fora\nPonta\n(MW) Valor","MUST - 2028 Fora\nPonta\n(MW) Anotacao"
SPANH-88--A,ANHANGUERA - 88 kV (C),88,1/Jan,31/Dez,"630,260",,"621,226",{(C)},"631,000",,"622,000",{(C)},"631,000",,"622,000",{(C)},"631,000",,"622,000",{(C)}
SPMRE-88--A,MIGUEL REALE - 88 kV (A),88,1/Jan,30/Jun,"282,185",,"279,892",{(D)},-,-,,-,,-,,-,,-,
SPMRE-88--A,MIGUEL REALE - 88 kV (A),88,1/Jul,31/Dez,"253,967",{(A)},"251,903","{(A)}\n(D)",-,-,,-,,-,,-,,-,
SPMRE-88--A,MIGUEL REALE - 88 kV (A),88,1/Jan,31/Dez,-,-,,-,,"340,257",,"347,864",{(D)},"340,257",,"347,864",{(D)},"340,257",,"347,864",{(D)}
SPSCDS88--A,S.CAETANO SUL88kVA,88,1/Jan,31/Dez,-,-,,-,,"300,000",,"300,000",{(B)},"300,000",,"265,000",,"300,000",,"265,000",
"""
    jaguari_csv_data = """ Cód ONS¹,Instalação," Tensão\n(kV)","Período de\nContratação De",Até,"MUST - 2025 Ponta\n(MW) Valor","MUST - 2025 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) Valor"," Fora\nPonta\n(MW) Anotacao","MUST - 2026 Ponta\n(MW) Valor","MUST - 2026 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 1 Valor"," Fora\nPonta\n(MW) 1 Anotacao","MUST - 2027 Ponta\n(MW) Valor","MUST - 2027 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 2 Valor"," Fora\nPonta\n(MW) 2 Anotacao","MUST - 2028 Ponta\n(MW) Valor","MUST - 2028 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 3 Valor"," Fora\nPonta\n(MW) 3 Anotacao"
SPAJGU138,ANTARTICA JAG - 138 kV (A),138,1/Jan,31/Dez,"44,000",,"47,000",{(B)},"44,000",,"47,000",{(B)},"44,000",,"47,000",{(B)},"44,000",,"47,000",{(B)}
SPMOC-138,MOCOCA - 138 kV (A),138,1/Jan,30/Jun,"35,640",,"34,020",{(B)},-,-,,-,,-,,-,,-,
SPMOC-138,MOCOCA - 138 kV (A),138,1/Jul,31/Dez,"32,076",{(A)},"30,618","{(A)}\n(B)",-,-,,-,,-,,-,,-,
SPMOC-138,MOCOCA - 138 kV (A),138,1/Jan,31/Dez,-,-,,-,,"32,076",{(A)},"30,618","{(A)}\n(B)","32,076",{(A)},"30,618","{(A)}\n(B)","32,076",,"30,618",{(B)}
SPMOCQ138-A,MOCOCA 4 - 138 kV (A),138,1/Jan,31/Dez,"39,500",,"30,600",{(F)},"46,500",,"30,600",{(F)},"46,500",,"30,600",{(F)},"46,500",,"30,600",{(F)}
"""
    sul_sudeste_csv_data = """ Cód ONS¹,Instalação," Tensão\n(kV)","Período de\nContratação De",Até,"MUST - 2025 Ponta\n(MW) Valor","MUST - 2025 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) Valor"," Fora\nPonta\n(MW) Anotacao","MUST - 2026 Ponta\n(MW) Valor","MUST - 2026 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 1 Valor"," Fora\nPonta\n(MW) 1 Anotacao","MUST - 2027 Ponta\n(MW) Valor","MUST - 2027 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 2 Valor"," Fora\nPonta\n(MW) 2 Anotacao","MUST - 2028 Ponta\n(MW) Valor","MUST - 2028 Ponta\n(MW) Anotacao"," Fora\nPonta\n(MW) 3 Valor"," Fora\nPonta\n(MW) 3 Anotacao"
SPUFA-138,ALTO ALEGRE -138 kV (A),138,2025-01-01,2025-12-31,"3,000",{(D)},"3,500",{(D)},"3,000",{(D)},"3,500",{(D)},"3,000",{(D)},"3,500",{(D)},"3,000",{(D)},"3,500",{(D)}
SPPVE-138,PRE.VENCESLAU -138 kV (A),138,2025-01-01,2025-12-31,"77,300",{(M)},"85,700",{(M)},"77,300",{(M)},"85,700",{(M)},"77,300",{(M)},"85,700",{(M)},"77,300",{(M)},"85,700",{(M)}
SPQUA288--A,QUATA II - 88 kV (A),88,2025-01-01,2025-12-31,"15,100",,"15,100",,"15,100",,"15,100",,"15,100",,"15,100",,"15,100",,"15,100",
SPRAN-88,"RANCHARIA - 88 kV\n(A)",88,2025-01-01,2025-12-31,"20,800",,"22,300",,"22,300",,"22,300",,"22,300",,"22,300",,"22,300",,"22,300",
"""
    
    company_data_map = {
        'CPFL Paulista': cpfl_paulista_csv_data,
        'Piratininga': piratininga_csv_data,
        'Neoenergia Elektro': neoenergia_elektro_csv_data,
        'Eletropaulo': eletropaulo_csv_data,
        'Jaguari': jaguari_csv_data,
        'Sul-Sudeste (Geral)': sul_sudeste_csv_data
    }
    
    all_dfs = {}
    for company, csv_data in company_data_map.items():
        df = pd.read_csv(io.StringIO(csv_data))
        df = standardize_columns(df) # Aplica a padronização
        all_dfs[company] = df
        
    return all_dfs

def parse_value(value):
    """Converte um valor de string (ex: '1.234,56') para float."""
    if not isinstance(value, str) or value.strip() in ['', '-']:
        return 0.0
    return float(value.replace('.', '').replace(',', '.'))

def get_annotations(text):
    """Extrai anotações de uma string (ex: '{(A)}' -> ['A'])."""
    if not isinstance(text, str):
        return []
    return re.findall(r'\((\w+)\)', text)

def process_data_for_year(df, year):
    """
    Processa o DataFrame para um ano específico, usando nomes de colunas padronizados.
    """
    # Nomes de colunas agora são previsíveis
    ponta_valor_col = f'Ponta_{year}_Valor'
    ponta_anotacao_col = f'Ponta_{year}_Anotacao'
    fora_ponta_valor_col = f'Fora_Ponta_{year}_Valor'
    instalacao_col = 'Instalacao'

    required_cols = [ponta_valor_col, fora_ponta_valor_col, instalacao_col]
    if not all(col in df.columns for col in required_cols):
        st.error(f"Não foi possível encontrar as colunas padronizadas para o ano de {year}. A estrutura do CSV pode ter mudado.")
        return None

    # Cálculos
    total_pontos = len(df)
    total_must_ponta = df[ponta_valor_col].apply(parse_value).sum()
    total_must_fora_ponta = df[fora_ponta_valor_col].apply(parse_value).sum()

    # Contagem de anotações
    all_anotacoes = []
    if ponta_anotacao_col in df.columns:
        df[ponta_anotacao_col].dropna().apply(lambda x: all_anotacoes.extend(get_annotations(x)))
    
    anotacoes_counts = pd.Series(all_anotacoes).value_counts()

    # Top 10 instalações
    top_instalacoes = df[[instalacao_col, ponta_valor_col]].copy()
    top_instalacoes['Valor'] = top_instalacoes[ponta_valor_col].apply(parse_value)
    top_instalacoes = top_instalacoes.nlargest(10, 'Valor')

    return {
        "kpis": {
            "Total de Pontos": total_pontos,
            "MUST Total - Ponta (MW)": total_must_ponta,
            "MUST Total - Fora Ponta (MW)": total_must_fora_ponta
        },
        "anotacoes_counts": anotacoes_counts,
        "top_instalacoes": top_instalacoes
    }


# --- Componentes da UI ---

def render_header():
    """Renderiza o cabeçalho da página."""
    st.title("📊 Dashboard de Análise de Contratos (MUST)")
    st.markdown("Visualize as estatísticas de demanda contratada por empresa e ano.")

def render_filters(company_options):
    """Renderiza os filtros de empresa e ano."""
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.selected_company = st.selectbox(
            "Selecione a Empresa:",
            options=company_options,
            key="company_selector"
        )
    with col2:
        st.session_state.selected_year = st.selectbox(
            "Selecione o Ano:",
            options=["2025", "2026", "2027", "2028"],
            key="year_selector"
        )

def render_kpis(kpis):
    """Renderiza os cartões de métricas (KPIs)."""
    cols = st.columns(3)
    for i, (title, value) in enumerate(kpis.items()):
        with cols[i]:
            st.metric(label=title, value=f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

def render_charts(anotacoes_counts, top_instalacoes):
    """Renderiza os gráficos de anotações e top instalações."""
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuição de Anotações (Ressalvas)")
        if not anotacoes_counts.empty:
            fig = px.pie(
                anotacoes_counts,
                values=anotacoes_counts.values,
                names=anotacoes_counts.index,
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma anotação encontrada para o período selecionado.")
            
    with col2:
        st.subheader("Top 10 Instalações por Demanda (Ponta)")
        if not top_instalacoes.empty:
            fig = px.bar(
                top_instalacoes,
                x='Valor',
                y='Instalacao',
                orientation='h',
                text='Valor',
                labels={'Valor': 'MUST Ponta (MW)', 'Instalacao': ''}
            )
            fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há dados de instalações para exibir.")

def render_structural_problems_table():
    """Renderiza a tabela de problemas estruturais."""
    st.subheader("Análise de Problemas Estruturais")
    problems_data = [
        { 'ID Problema': 'LT138POC-SJBV2', 'Detalhe do Problema': 'violação da capacidade de carregamento de longa duração da LT 138 kV Poços de Caldas – São João da Boa Vista 2 C1/C2', 'Cenário': 'principalmente no período da entressafra da cana-de-açúcar e em condições de despachos reduzidos nas usinas dos rios Pardo e Tietê', 'ID Solução': 'Em estudo pela EPE', 'Detalhe da Solução': 'NÃO HÁ' },
        { 'ID Problema': 'LT138SJRP-CAT', 'Detalhe do Problema': 'violação da capacidade de carregamento da LT 138 kV São José do Rio Preto – Catanduva C1/C2', 'Cenário': 'qualquer condição', 'ID Solução': 'ReA nº 12.639/2022', 'Detalhe da Solução': 'reconstrução /recondutoramento da LT 138 kV São José do Rio Preto – Catanduva C1/C2, de 49,3 km de extensão, CD, para capacidade mínima de 206 / 242 MVA, em condição normal/emergência de operação e obras associadas, autorizadas à CTEEP através da ReA ANEEL nº 12.639/2022, com prazo contratual para junho de 2027' },
        { 'ID Problema': 'LT138RPT-PFE', 'Detalhe do Problema': 'violação da capacidade de carregamento de longa duração na LT 138 kV Ribeirão Preto – Porto Ferreira C1/C2', 'Cenário': 'qualquer condição', 'ID Solução': 'NÃO HÁ', 'Detalhe da Solução': 'NÃO HÁ' },
        { 'ID Problema': 'TR500/345-POC', 'Detalhe do Problema': 'violação da capacidade de carregamento de longa duração da transformação 500/345 kV da SE Poços de Caldas', 'Cenário': 'qualquer condição', 'ID Solução': 'TR no POTEE', 'Detalhe da Solução': 'Reforço indicado nessa transformação no POTEE 2024 - 2ª Emissão, a ser autorizado a ELETROBRAS pela ANEEL' },
        { 'ID Problema': 'LT138SJRP-CAT, LT138SJRP-MIR2, Subtensão', 'Detalhe do Problema': 'Violação da capacidade de carregamento de longa duração nas LT 138 kV São José do Rio Preto – Catanduva C1/C2 e LT 138 kV São José do Rio Preto – Mirassol II C1/C2 e subtensão', 'Cenário': 'período da entressafra da cana-de-açúcar e principalmente em condições de despachos reduzidos nas usinas do Tietê', 'ID Solução': 'ReA Nª 12.639/2022, ReA nº 616/2023', 'Detalhe da Solução': 'entrada em operação das obras abaixo relacionadas: a) reconstrução/recondutoramento da LT 138 kV São José do Rio Preto – Catanduva autorizada à CTEEP através da ReA Nª 12.639/2022, com prazo contratual previsto para jun/2025 e prevista atualmente pela Transmissora para novembro de 2026; b) a substituição de equipamentos terminais na extremidade da SE São José do Rio Preto, autorizada à CTEEP através do Despacho ANEEL nº 616/2023 com previsão de conclusão para março de 2026' }
    ]
    problems_df = pd.DataFrame(problems_data)
    st.dataframe(problems_df, use_container_width=True)


# --- Aplicação Principal ---

def main():
    """Função principal que executa a aplicação Streamlit."""
    
    # Carrega os dados
    all_dfs = load_all_data()
    
    # Inicializa o session_state se ainda não existir
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = list(all_dfs.keys())[0]
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = "2025"

    # Renderiza os componentes da UI
    render_header()
    render_filters(list(all_dfs.keys()))
    
    st.divider()

    # Processa os dados com base nos filtros selecionados
    selected_df = all_dfs[st.session_state.selected_company]
    processed_data = process_data_for_year(selected_df, st.session_state.selected_year)

    # Renderiza os resultados
    if processed_data:
        render_kpis(processed_data["kpis"])
        st.divider()
        render_charts(processed_data["anotacoes_counts"], processed_data["top_instalacoes"])
        st.divider()

    render_structural_problems_table()
    
    # Adiciona instruções de como usar no rodapé
    st.sidebar.title("Como Usar")
    st.sidebar.info(
        """
        1. **Selecione a Empresa** no primeiro menu para carregar os dados correspondentes.
        2. **Selecione o Ano** no segundo menu para filtrar as informações para o período desejado.
        3. Os cartões e gráficos serão atualizados automaticamente com base na sua seleção.
        """
    )


if __name__ == "__main__":
    main()
