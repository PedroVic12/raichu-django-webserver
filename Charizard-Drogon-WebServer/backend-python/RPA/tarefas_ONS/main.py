import sys
from pathlib import Path
from pdf_processor import PDFProcessor
from excel_handler import ExcelHandler
from ClassPowerQuery import MiniPowerQuery
import pandas as pd
from pathlib import Path

def processar_arquivo(arquivo_entrada, paginas="all"):
    """Processa um arquivo PDF e gera um relatório Excel"""
    # Configuração de caminhos
    arquivo_entrada = Path(arquivo_entrada)
    pasta_saida = arquivo_entrada.parent
    arquivo_saida = pasta_saida / f"relatorio_{arquivo_entrada.stem}.xlsx"
    
    print(f"Processando arquivo: {arquivo_entrada}")
    
    # 1. Processar PDF
    processador = PDFProcessor(str(arquivo_entrada))
    resultado = processador.processar_paginas(paginas)
    
    # 2. Processar com PowerQuery se necessário
    df_powerquery = None
    try:
        print("Processando com PowerQuery...")
        mpq = MiniPowerQuery(str(arquivo_entrada))
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
        print(f"Aviso: Não foi possível processar com PowerQuery: {e}")
    
    # 3. Criar relatório Excel
    print("Criando relatório Excel...")
    excel = ExcelHandler(arquivo_saida)
    
    # Adicionar resumo
    dados_resumo = {
        'nome_arquivo': arquivo_entrada.name,
        'num_paginas': resultado['num_paginas'],
        'num_tabelas_tabula': resultado['num_tabelas_tabula'],
        'num_tabelas_camelot': resultado['num_tabelas_camelot'],
        'paginas_processadas': paginas
    }
    excel.adicionar_resumo(dados_resumo)
    
    # Adicionar tabelas do Tabula
    if processador.tabelas_tabula:
        excel.adicionar_tabelas(processador.tabelas_tabula, "Tabelas_Tabula")
    
    # Adicionar tabelas do Camelot
    if processador.tabelas_camelot:
        excel.adicionar_tabelas(processador.tabelas_camelot, "Tabelas_Camelot")
    
    # Adicionar dados do PowerQuery
    if df_powerquery is not None and not df_powerquery.empty:
        excel.adicionar_tabelas([df_powerquery], "Dados_PowerQuery")
    
    # Adicionar texto extraído
    if resultado['texto_extraido']:
        excel.adicionar_texto(resultado['texto_extraido'], "Texto_Extraido")
    
    # Salvar e retornar caminho do arquivo
    caminho_saida = excel.salvar()
    print(f"Processamento concluído! Arquivo salvo em: {caminho_saida}")
    return caminho_saida

def main():

    
    #arquivo = sys.argv[1]
    #paginas = sys.argv[2] if len(sys.argv) > 2 else "all"

    paginas = "all"
    # Configuração
    path = Path.home() / "Downloads"
    pdf_path = path / "quadro_horarios_telecom.pdf"

    processar_arquivo(pdf_path, paginas)

if __name__ == "__main__":
    main()
