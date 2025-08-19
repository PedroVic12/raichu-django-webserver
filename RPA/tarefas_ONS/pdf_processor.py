import pandas as pd
from PyPDF2 import PdfReader
import camelot
import tabula
from pathlib import Path
import traceback

class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.reader = PdfReader(pdf_path)
        self.num_paginas = len(self.reader.pages)
        self.tabelas_tabula = []
        self.tabelas_camelot = []
        self.texto_extraido = ""

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
            print(traceback.format_exc())
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
            print(traceback.format_exc())
            return 0

    def extrair_texto(self, paginas="all"):
        """Extrai texto das páginas especificadas"""
        try:
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
            
            self.texto_extraido = "\n".join(textos)
            return self.texto_extraido
            
        except Exception as e:
            print(f"Erro ao processar extração de texto: {e}")
            print(traceback.format_exc())
            return ""

    def processar_paginas(self, paginas="all"):
        """Processa todas as extrações para as páginas especificadas"""
        print(f"Processando páginas: {paginas}")
        print("Extraindo tabelas com Tabula...")
        num_tabula = self.extrair_tabelas_tabula(paginas)
        print(f"Tabelas extraídas com Tabula: {num_tabula}")
        
        print("Extraindo tabelas com Camelot...")
        num_camelot = self.extrair_tabelas_camelot(paginas)
        print(f"Tabelas extraídas com Camelot: {num_camelot}")
        
        print("Extraindo texto...")
        self.extrair_texto(paginas)
        
        return {
            'num_paginas': self.num_paginas,
            'num_tabelas_tabula': num_tabula,
            'num_tabelas_camelot': num_camelot,
            'texto_extraido': self.texto_extraido
        }
