from openpyxl_guide import ExcelOpenPyXLGuide
import pandas as pd
from pathlib import Path

class ExcelHandler:
    def __init__(self, output_path):
        self.output_path = Path(output_path)
        self.excel = ExcelOpenPyXLGuide(str(output_path))
        self.excel.criar_arquivo()
    
    def adicionar_resumo(self, dados):
        """Adiciona uma aba de resumo com os dados da extração"""
        self.excel.adicionar_planilha("Resumo")
        self.excel.selecionar_planilha("Resumo")
        
        resumo = [
            ("Item", "Valor"),
            ("Arquivo", dados.get('nome_arquivo', 'N/A')),
            ("Total de Páginas", dados.get('num_paginas', 0)),
            ("Tabelas (Tabula)", dados.get('num_tabelas_tabula', 0)),
            ("Tabelas (Camelot)", dados.get('num_tabelas_camelot', 0)),
            ("Páginas Processadas", dados.get('paginas_processadas', 'N/A'))
        ]
        
        for i, (chave, valor) in enumerate(resumo, 1):
            self.excel.escrever_celula(f"A{i}", chave)
            self.excel.escrever_celula(f"B{i}", valor)
    
    def adicionar_tabelas(self, tabelas, nome_aba="Tabelas"):
        """Adiciona tabelas a uma aba do Excel"""
        if not tabelas:
            return
            
        self.excel.adicionar_planilha(nome_aba)
        self.excel.selecionar_planilha(nome_aba)
        
        linha_atual = 1
        for i, tabela in enumerate(tabelas, 1):
            # Adiciona cabeçalho da tabela
            self.excel.escrever_celula(f"A{linha_atual}", f"Tabela {i}")
            linha_atual += 1
            
            # Escreve cabeçalhos
            for col, valor in enumerate(tabela.columns, 1):
                self.excel.escrever_celula(
                    f"{chr(64+col)}{linha_atual}",
                    str(valor)
                )
            linha_atual += 1
            
            # Escreve dados
            for _, linha in tabela.iterrows():
                for col, valor in enumerate(linha, 1):
                    self.excel.escrever_celula(
                        f"{chr(64+col)}{linha_atual}",
                        str(valor) if pd.notna(valor) else ""
                    )
                linha_atual += 1
            
            linha_atual += 2  # Espaço entre tabelas
    
    def adicionar_texto(self, texto, nome_aba="Texto"):
        """Adiciona texto extraído a uma aba do Excel"""
        if not texto:
            return
            
        self.excel.adicionar_planilha(nome_aba)
        self.excel.selecionar_planilha(nome_aba)
        
        # Divide o texto em linhas e escreve cada uma
        for i, linha in enumerate(texto.split('\n'), 1):
            self.excel.escrever_celula(f"A{i}", linha)
    
    def salvar(self):
        """Salva o arquivo Excel"""
        self.excel.salvar()
        print(f"Arquivo salvo em: {self.output_path.absolute()}")
        return str(self.output_path.absolute())
