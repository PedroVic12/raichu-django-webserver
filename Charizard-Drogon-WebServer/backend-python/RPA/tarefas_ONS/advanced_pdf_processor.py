import os
import re
import pandas as pd
import tabula
import pytesseract
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from typing import List, Dict, Optional, Union
import camelot
import tempfile
import io
from pathlib import Path

class AdvancedPDFProcessor:
    def __init__(self, pdf_path: str):
        """
        Inicializa o processador de PDF avançado.
        
        Args:
            pdf_path: Caminho para o arquivo PDF a ser processado
        """
        self.pdf_path = Path(pdf_path)
        self.reader = PdfReader(str(self.pdf_path))
        self.num_paginas = len(self.reader.pages)
        self.texto_extraido = ""
        self.tabelas_tabula = []
        self.tabelas_camelot = []
        self.anotacoes = []
        
    def extrair_texto_pdf(self, paginas: str = "all") -> str:
        """
        Extrai texto de um PDF, com suporte a OCR para PDFs digitalizados.
        
        Args:
            paginas: Intervalo de páginas no formato 'inicio-fim' ou 'all' para todas
            
        Returns:
            str: Texto extraído das páginas especificadas
        """
        paginas_processar = self._parse_paginas(paginas)
        textos = []
        
        for num in paginas_processar:
            try:
                # Tenta extrair texto diretamente primeiro
                texto = self.reader.pages[num-1].extract_text()
                
                # Se não conseguir extrair texto, tenta OCR
                if not texto or len(texto.strip()) < 50:  # Limite arbitrário para considerar como texto inválido
                    texto = self._extrair_texto_com_ocr(num)
                
                if texto:
                    textos.append(f"--- Página {num} ---\n{texto}")
                    
            except Exception as e:
                print(f"Erro ao extrair texto da página {num}: {e}")
        
        self.texto_extraido = "\n\n".join(textos)
        return self.texto_extraido
    
    def _extrair_texto_com_ocr(self, num_pagina: int) -> str:
        """
        Extrai texto de uma página de PDF usando OCR (Tesseract).
        
        Args:
            num_pagina: Número da página (1-based)
            
        Returns:
            str: Texto extraído via OCR
        """
        try:
            # Converte a página PDF para imagem
            images = convert_from_path(
                str(self.pdf_path),
                first_page=num_pagina,
                last_page=num_pagina
            )
            
            if not images:
                return ""
                
            # Extrai texto da imagem usando Tesseract
            return pytesseract.image_to_string(images[0], lang='por')
            
        except Exception as e:
            print(f"Erro no OCR da página {num_pagina}: {e}")
            return ""
    
    def extrair_tabelas(self, paginas: str = "all", usar_camelot: bool = True) -> dict:
        """
        Extrai tabelas do PDF usando Tabula e/ou Camelot.
        
        Args:
            paginas: Intervalo de páginas no formato 'inicio-fim' ou 'all' para todas
            usar_camelot: Se True, usa Camelot como método principal (mais preciso, mas mais lento)
            
        Returns:
            dict: Dicionário com tabelas extraídas por cada método
        """
        paginas_processar = self._parse_paginas(paginas)
        resultado = {
            'tabula': [],
            'camelot': []
        }
        
        # Extrai com Tabula (mais rápido, mas menos preciso)
        try:
            self.tabelas_tabula = tabula.read_pdf_with_template(
                str(self.pdf_path),
                pages=paginas,
                multiple_tables=True,
                stream=True,
                lattice=False,
                pandas_options={'header': None}
            )
            resultado['tabula'] = self.tabelas_tabula
        except Exception as e:
            print(f"Erro ao extrair com Tabula: {e}")
        
        # Extrai com Camelot (mais lento, mas mais preciso)
        if usar_camelot:
            try:
                tables = camelot.read_pdf(
                    str(self.pdf_path),
                    pages=paginas,
                    flavor='lattice',
                    strip_text='\n'
                )
                self.tabelas_camelot = [table.df for table in tables]
                resultado['camelot'] = self.tabelas_camelot
            except Exception as e:
                print(f"Erro ao extrair com Camelot: {e}")
        
        return resultado
    
    def processar_com_powerquery(self, **kwargs):
        """
        Processa os dados extraídos usando a classe MiniPowerQuery.
        
        Args:
            **kwargs: Argumentos adicionais para o MiniPowerQuery
            
        Returns:
            pandas.DataFrame: DataFrame processado
        """
        from ClassPowerQuery import MiniPowerQuery
        
        try:
            mpq = MiniPowerQuery(str(self.pdf_path), **kwargs)
            # Aplica as transformações padrão
            (mpq
             .trim_spaces()
             .drop_nulls()
             .drop_duplicates()
            )
            return mpq.df
        except Exception as e:
            print(f"Erro ao processar com PowerQuery: {e}")
            return pd.DataFrame()
    
    def _parse_paginas(self, paginas: str) -> List[int]:
        """
        Converte uma string de intervalo de páginas em uma lista de números de página.
        
        Args:
            paginas: String no formato 'inicio-fim' ou 'all'
            
        Returns:
            List[int]: Lista de números de página
        """
        if paginas == "all":
            return list(range(1, self.num_paginas + 1))
        
        if '-' in paginas:
            start, end = map(int, paginas.split('-'))
            return list(range(start, end + 1))
            
        return [int(paginas)]
    
    def gerar_metadados(self) -> dict:
        """
        Gera metadados sobre o processamento do PDF.
        
        Returns:
            dict: Dicionário com metadados
        """
        return {
            'arquivo': str(self.pdf_path.name),
            'total_paginas': self.num_paginas,
            'tabelas_encontradas': len(self.tabelas_tabula) + len(self.tabelas_camelot),
            'tamanho_arquivo': f"{os.path.getsize(self.pdf_path) / 1024:.2f} KB"
        }
