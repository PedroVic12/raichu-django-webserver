import pandas as pd
import re
import camelot
import tabula
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
from typing import Dict, List, Optional, Union


class MiniPowerQuery:
    def __init__(self, file_path: str = None):
        self.df = pd.DataFrame()
        self.file_path = file_path
        self.pdf_info = {}

    # -------------------- ANÁLISE INICIAL DO PDF --------------------
    def analyze_pdf(self, file_path: str):
        """Analisa o PDF para mostrar informações sobre tabelas e páginas."""
        print(f"Analisando PDF: {file_path}")
        
        # Informações básicas do PDF
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            print(f"📄 Total de páginas: {total_pages}")
        except Exception as e:
            print(f"Erro ao ler PDF com PyPDF2: {e}")
            total_pages = 0

        # Análise com Camelot para contar tabelas
        try:
            tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')
            print(f"📊 Tabelas encontradas com Camelot: {len(tables)}")
            
            for i, table in enumerate(tables):
                print(f"   Tabela {i+1}: {table.shape[0]}x{table.shape[1]} (página {table.page})")
                
            self.pdf_info = {
                'total_pages': total_pages,
                'total_tables': len(tables),
                'tables': tables
            }
            
        except Exception as e:
            print(f"Erro ao analisar com Camelot: {e}")
            self.pdf_info = {'total_pages': total_pages, 'total_tables': 0}
        
        return self

    # -------------------- EXTRAÇÃO DE DADOS --------------------
    def from_pdf_table(self, file_path: str, table_id: str = "Table011", pages: str = "all"):
        """Extrai tabela específica do PDF (equivalente ao Pdf.Tables do Power Query)."""
        try:
            if not hasattr(self, 'pdf_info') or not self.pdf_info:
                self.analyze_pdf(file_path)
            
            tables = camelot.read_pdf(file_path, pages=pages, flavor='lattice')
            
            # Se table_id for numérico (como "Table011"), pega pelo índice
            if table_id.startswith("Table"):
                table_num = int(re.findall(r'\d+', table_id)[0])
                if table_num <= len(tables):
                    self.df = tables[table_num - 1].df
                else:
                    print(f"Tabela {table_id} não encontrada. Usando primeira tabela.")
                    self.df = tables[0].df if tables else pd.DataFrame()
            else:
                self.df = tables[0].df if tables else pd.DataFrame()
                
        except Exception as e:
            print(f"Erro ao extrair tabela: {e}")
            self.df = pd.DataFrame()
        
        return self

    def force_all_columns_as_text(self):
        """Força todas as colunas como texto (equivalente ao TransformColumnTypes)."""
        for col in self.df.columns:
            self.df[col] = self.df[col].astype(str)
        return self

    # -------------------- MANIPULAÇÃO DE CABEÇALHOS --------------------
    def extract_header_rows(self, n_rows: int = 2):
        """Captura as primeiras n linhas e remove do DataFrame."""
        if len(self.df) < n_rows:
            print(f"DataFrame tem apenas {len(self.df)} linhas, menor que {n_rows}")
            return self
        
        # Captura as linhas
        self.header_rows = []
        for i in range(n_rows):
            self.header_rows.append(self.df.iloc[i].tolist())
        
        # Remove as linhas do DataFrame
        self.df = self.df.iloc[n_rows:].reset_index(drop=True)
        return self

    def create_concatenated_headers(self):
        """
        Cria nomes concatenados seguros (REPLICA EXATA do Power Query).
        Equivale a ColunasConcatenadas e ColunasUnicas do Power Query.
        """
        if not hasattr(self, 'header_rows') or len(self.header_rows) < 2:
            print("Nenhuma linha de cabeçalho encontrada. Execute extract_header_rows primeiro.")
            return self
        
        linha1, linha2 = self.header_rows[0], self.header_rows[1]
        
        # ETAPA 1: ColunasConcatenadas (igual ao Power Query)
        colunas_concatenadas = []
        for i in range(len(linha1)):
            # Converte para texto e aplica trim (igual ao Power Query)
            parte1 = str(linha1[i]).strip() if linha1[i] is not None else ""
            parte2 = str(linha2[i]).strip() if linha2[i] is not None else ""
            
            # Remove "None", "nan", "_" 
            if parte1 in ["None", "nan", "_"]:
                parte1 = ""
            if parte2 in ["None", "nan", "_"]:
                parte2 = ""
            
            # Lógica EXATA do Power Query
            if (parte1 == "" or parte1 == "_") and (parte2 == "" or parte2 == "_"):
                nome = f"Coluna{i + 1}"
            else:
                # Text.Combine({Parte1, Parte2}, " ")
                nome = f"{parte1} {parte2}".strip()
            
            colunas_concatenadas.append(nome)
        
        # ETAPA 2: ColunasUnicas (garante nomes únicos - igual ao Power Query)
        colunas_unicas = []
        for i, current_name in enumerate(colunas_concatenadas):
            # Verifica se nome já apareceu antes
            primeiros_n = colunas_concatenadas[:i]  # List.FirstN equivalente
            
            if current_name in primeiros_n:
                # Conta quantas vezes apareceu antes
                count = primeiros_n.count(current_name)
                nome_unico = f"{current_name} {count}"
            else:
                nome_unico = current_name
            
            colunas_unicas.append(nome_unico)
        
        # Aplica os nomes únicos às colunas
        self.df.columns = colunas_unicas
        self.colunas_concatenadas = colunas_concatenadas  # Salva para debug
        self.colunas_unicas = colunas_unicas  # Salva para debug
        
        return self

    # -------------------- DIVISÃO DE COLUNAS --------------------
    def identify_columns_with_delimiter(self, delimiter: str = "^"):
        """
        Identifica colunas que contêm o delimitador (REPLICA do Power Query).
        Equivale a ColunasParaDividir com List.Select e List.AnyTrue.
        """
        columns_to_split = []
        
        for col in self.df.columns:
            # List.FirstN(Table.Column(TabelaFinal, _), 100)
            valores_exemplo = self.df[col].head(100).tolist()
            
            # List.AnyTrue(List.Transform(valoresExemplo, (v) => v <> null and Text.Contains(Text.From(v), "^")))
            has_delimiter = any(
                v is not None and delimiter in str(v) 
                for v in valores_exemplo
            )
            
            if has_delimiter:
                columns_to_split.append(col)
        
        self.columns_to_split = columns_to_split
        print(f"🔍 Colunas para dividir: {columns_to_split}")
        return self

    def split_columns_by_delimiter(self, delimiter: str = "^"):
        """
        Divide colunas pelo delimitador (REPLICA EXATA do Power Query).
        Usa List.Accumulate equivalente para processar uma coluna de cada vez.
        """
        if not hasattr(self, 'columns_to_split'):
            self.identify_columns_with_delimiter(delimiter)
        
        # List.Accumulate equivalente - processa uma coluna de cada vez
        tabela_atual = self.df.copy()
        
        for nome_coluna in self.columns_to_split:
            # Table.SplitColumn equivalente
            novos_nomes = [f"{nome_coluna} Valor", f"{nome_coluna} Anotacao"]
            
            # Splitter.SplitTextByDelimiter("^", QuoteStyle.None)
            split_data = tabela_atual[nome_coluna].astype(str).str.split(delimiter, n=1, expand=True)
            
            # Se só tem uma coluna após split, cria a segunda vazia
            if split_data.shape[1] == 1:
                tabela_atual[novos_nomes[0]] = split_data[0]
                tabela_atual[novos_nomes[1]] = ""
            else:
                tabela_atual[novos_nomes[0]] = split_data[0]
                tabela_atual[novos_nomes[1]] = split_data[1].fillna("")
            
            # Remove coluna original
            tabela_atual = tabela_atual.drop(columns=[nome_coluna])
            
            # TransformColumnTypes - força como texto
            tabela_atual[novos_nomes[0]] = tabela_atual[novos_nomes[0]].astype(str)
            tabela_atual[novos_nomes[1]] = tabela_atual[novos_nomes[1]].astype(str)
        
        self.df = tabela_atual
        print(f"✂️ Divisão concluída. Novas colunas: {len(self.df.columns)}")
        return self

    # -------------------- PADRONIZAÇÃO DE NOMES --------------------
    def standardize_column_names(self, mapping: Dict[str, str]):
        """Padroniza nomes das colunas (equivalente ao RenameColumns do Power Query)."""
        # Só renomeia colunas que existem
        existing_mapping = {old: new for old, new in mapping.items() if old in self.df.columns}
        self.df = self.df.rename(columns=existing_mapping)
        
        if len(existing_mapping) != len(mapping):
            missing = set(mapping.keys()) - set(existing_mapping.keys())
            print(f"Colunas não encontradas: {missing}")
        
        return self

    # -------------------- FUNÇÃO PRINCIPAL --------------------
    def read_must_tables(self, pdf_path: str, pages: str = "all", table_id: str = "Table011"):
        """
        Função principal que replica exatamente o comportamento do Power Query.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            pages: Páginas a serem processadas (ex: "1-3", "all")
            table_id: ID da tabela (padrão "Table011")
        """
        
        # Mapeamento de padronização das colunas (igual ao Power Query)
        column_mapping = {
            # Colunas de Identificação
            "Ponto de Conexão Cód ONS¹": "Cód ONS",
            "Ponto de Conexão Instalação": "Instalação", 
            "Ponto de Conexão Tensão (kV)": "Tensão (kV)",
            "Período de Contratação De": "De",
            "Período de Contratação Até": "Até",

            # Colunas de Dados 2025
            "MUST - 2025 Ponta (MW) Valor": "Ponta 2025 Valor",
            "MUST - 2025 Ponta (MW) Anotacao": "Ponta 2025 Anotacao", 
            "MUST - 2025 Fora Ponta (MW) Valor": "Fora Ponta 2025 Valor",
            "MUST - 2025 Fora Ponta (MW) Anotacao": "Fora Ponta 2025 Anotacao",

            # Colunas de Dados 2026
            "MUST - 2026 Ponta (MW) Valor": "Ponta 2026 Valor",
            "MUST - 2026 Ponta (MW) Anotacao": "Ponta 2026 Anotacao",
            "MUST - 2026 Fora Ponta (MW) Valor": "Fora Ponta 2026 Valor", 
            "MUST - 2026 Fora Ponta (MW) Anotacao": "Fora Ponta 2026 Anotacao",
            
            # Colunas de Dados 2027
            "MUST - 2027 Ponta (MW) Valor": "Ponta 2027 Valor",
            "MUST - 2027 Ponta (MW) Anotacao": "Ponta 2027 Anotacao",
            "MUST - 2027 Fora Ponta (MW) Valor": "Fora Ponta 2027 Valor",
            "MUST - 2027 Ponta (MW) 1 Anotacao": "Fora Ponta 2027 Anotacao",

            # Colunas de Dados 2028
            "MUST - 2028 Ponta (MW) Valor": "Ponta 2028 Valor",
            "MUST - 2028 Ponta (MW) Anotacao": "Ponta 2028 Anotacao",
            "Fora Ponta (MW) 2 Valor": "Fora Ponta 2028 Valor",
            "Fora Ponta (MW) 2 Anotacao": "Fora Ponta 2028 Anotacao"
        }
        
        print("🔍 Iniciando análise do PDF...")
        
        # Executa todos os passos na mesma ordem do Power Query
        (self
         .analyze_pdf(pdf_path)                      # Análise inicial
         .from_pdf_table(pdf_path, table_id, pages) # Extração da tabela
         .force_all_columns_as_text()               # Força como texto
         .extract_header_rows(2)                    # Captura primeiras 2 linhas
         .create_concatenated_headers()             # Cria cabeçalhos concatenados
         .identify_columns_with_delimiter("^")      # Identifica colunas para dividir
         .split_columns_by_delimiter("^")           # Divide colunas por ^
         .standardize_column_names(column_mapping)  # Padroniza nomes das colunas
         )
        
        print("✅ Processamento concluído!")
        print(f"📊 DataFrame final: {self.df.shape[0]} linhas x {self.df.shape[1]} colunas")
        print(f"📋 Colunas: {list(self.df.columns)}")
        
        return self

    # -------------------- OPERAÇÕES AUXILIARES --------------------
    def drop_nulls(self, cols=None):
        """Remove linhas com valores nulos."""
        self.df = self.df.dropna(subset=cols)
        return self

    def drop_duplicates(self, cols=None):
        """Remove linhas duplicadas.""" 
        self.df = self.df.drop_duplicates(subset=cols)
        return self

    def trim_spaces(self):
        """Remove espaços em branco."""
        self.df = self.df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        return self

    def preview(self, n: int = 5):
        """Visualiza primeiras n linhas."""
        print(f"\n📋 Preview ({n} primeiras linhas):")
        print(self.df.head(n))
        return self

    # -------------------- EXPORTAÇÃO --------------------
    def export_excel(self, output_path: str):
        """Exporta para Excel."""
        self.df.to_excel(output_path, index=False)
        print(f"📁 Arquivo Excel exportado: {output_path}")
        return self

    def export_csv(self, output_path: str):
        """Exporta para CSV."""
        self.df.to_csv(output_path, index=False)
        print(f"📁 Arquivo CSV exportado: {output_path}")
        return self


# -------------------- EXEMPLO DE USO --------------------
if __name__ == "__main__":
    # Instancia a classe
    mpq = MiniPowerQuery()
    
    # Caminho do PDF (altere conforme necessário)
    pdf_path = "CUST-2002-123-41 - JAGUARI - RECON 2025-2028.pdf"
    
    # Executa o processamento completo
    try:
        (mpq
         .read_must_tables(pdf_path, pages="all")  # Processa todas as páginas
         .trim_spaces()                            # Remove espaços
         .drop_duplicates()                        # Remove duplicatas
         .preview(10)                              # Mostra preview
         .export_excel("saida_final_python.xlsx") # Exporta resultado
         )
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")