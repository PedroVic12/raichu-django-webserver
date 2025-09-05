from openpyxl_guide import ExcelOpenPyXLGuide
from ClassPowerQuery import MiniPowerQuery
import regex
import pandas as pd
from PyPDF2 import PdfReader
import camelot
import tabula
from pathlib import Path

class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.reader = PdfReader(pdf_path)
        self.num_paginas = len(self.reader.pages)
        self.tabelas_tabula = []
        self.tabelas_camelot = []
        self.anotacoes = []

    def extrair_tabelas_tabula(self, paginas="all"):
        """Extrai tabelas usando Tabula"""
        try:
            self.tabelas_tabula = tabula.read_pdf(
                self.pdf_path,
                pages=paginas,
                multiple_tables=True,
                stream=True,
                lattice=False,
                pandas_options={'header': None}
            )
            return len(self.tabelas_tabula)
        except Exception as e:
            print(f"Erro ao extrair com Tabula: {e}")
            return 0

    def extrair_tabelas_camelot(self, paginas="all"):
        """Extrai tabelas usando Camelot"""
        try:
            tables = camelot.read_pdf(
                self.pdf_path,
                pages=paginas,
                flavor='lattice',
                strip_text='\n'
            )
            self.tabelas_camelot = [table.df for table in tables]
            return len(self.tabelas_camelot)
        except Exception as e:
            print(f"Erro ao extrair com Camelot: {e}")
            return 0

    def extrair_texto(self, paginas="all"):
        """Extrai texto das páginas especificadas"""
        if paginas == "all":
            paginas = range(1, self.num_paginas + 1)
        elif isinstance(paginas, str) and '-' in paginas:
            start, end = map(int, paginas.split('-'))
            paginas = range(start, end + 1)
        
        textos = []
        for num in paginas:
            try:
                texto = self.reader.pages[num-1].extract_text()
                if texto:
                    textos.append(f"--- Página {num} ---\n{texto}\n")
            except Exception as e:
                print(f"Erro ao extrair texto da página {num}: {e}")
        
        return "\n".join(textos)

def main():
    # Configuração
    path = Path.home() / "Downloads"
    pdf_path = path / "quadro_horarios_telecom.pdf"
    output_excel = path / "relatorio_extracao.xlsx"
    
    # Inicializar processador PDF
    processador = PDFProcessor(str(pdf_path))
    
    # Extrair tabelas
    num_tabula = processador.extrair_tabelas_tabula("6-9")  # Extrai das páginas 6 a 9
    num_camelot = processador.extrair_tabelas_camelot("6-9")
    
    # Extrair texto
    texto_extraido = processador.extrair_texto("6-9")
    
    # Processar com PowerQuery
    try:
        mpq = MiniPowerQuery(str(pdf_path))
        (mpq
         .trim_spaces()
         .drop_nulls()
         .drop_duplicates()
         .rename_columns({"Disciplina": "Materia"})
        )
        df_powerquery = mpq.df
        print("Dados processados com PowerQuery:")
        print(df_powerquery.head())
    except Exception as e:
        print(f"Erro no PowerQuery: {e}")
        df_powerquery = pd.DataFrame()

    # Criar relatório Excel
    excel = ExcelOpenPyXLGuide(str(output_excel))
    excel.criar_arquivo()
    
    # Adicionar resumo
    excel.escrever_celula("A1", "Relatório de Extração de PDF")
    excel.escrever_celula("A2", f"Arquivo: {pdf_path.name}")
    excel.escrever_celula("A3", f"Total de Páginas: {processador.num_paginas}")
    excel.escrever_celula("A4", f"Tabelas extraídas (Tabula): {num_tabula}")
    excel.escrever_celula("A5", f"Tabelas extraídas (Camelot): {num_camelot}")
    
    # Adicionar dados do PowerQuery
    if not df_powerquery.empty:
        excel.adicionar_planilha("Dados PowerQuery")
        excel.escrever_dataframe("A1", df_powerquery)
    
    # Adicionar texto extraído
    excel.adicionar_planilha("Texto Extraído")
    excel.escrever_celula("A1", "Texto das Páginas 6-9")
    excel.ajustar_largura_coluna("A", 100)  # Ajustar largura da coluna
    excel.escrever_celula("A2", texto_extraido)
    
    # Salvar relatório
    excel.salvar()
    print(f"Relatório salvo em: {output_excel}")

if __name__ == "__main__":
    main()
