from models.Dragonite_PDF import Dragonite
from models.Palkia_Excel import Palkia
import pandas as pd

# Constantes globais
pdf_path = r'C:\Users\PedroVictorRodrigues\Documents\GitHub\elon-musk\Tecnologia e Inovação\Automações\assets\PDF\SJ - SAGITARIUS 2023-07-21.pdf'
NUMERO_PAGINA = 65
PAGINAS_SEPARADAS = [53, 54, 64]

def obter_nome_arquivo(pdf_path):
    """Obtém o nome do arquivo PDF."""
    file_name = pdf_path[pdf_path.find('SJ'):-4]
    return file_name

def processar_pagina(dragonite, pagina):
    """Processa uma página específica do PDF e retorna o texto processado."""
    print(f'\n\nPagina: {pagina}')

    # Ler o PDF
    texto = dragonite.ler_pagina(pagina)
    texto = dragonite.traduzirTexto(texto)

    return texto

def criar_dataframes_e_periodicidade(dragonite, texto):
    """Cria DataFrames a partir do texto da página e extrai periodicidade."""
    colunas = ['Ações de manutenção', 'Medidas de segurança']

    array_df = []
    periodicidade_array = []

    df1 = dragonite.criar_dataframeManutencao(texto)
    array_df.append(df1)

    df2 = dragonite.criar_dataframeSeguranca(texto)
    array_df.append(df2)

    try:
        df3 = dragonite.extrair_periodicidade(texto)

        if df3.empty:
            df_test = dragonite.mostrar_matches(texto)
            periodicidade_array.append(df_test)

        if all(key in df3 for key in ['Inspection', 'Drydock', 'Sampling']):
            df_inspection = df3['Inspection']
            df_drydock = df3['Drydock']
            df_sampling = df3['Sampling']

            periodicidade_df = dragonite.combinar_periodicidade(df_inspection, df_drydock)
            
            if periodicidade_df is not None:
                array_df.append(periodicidade_df)
                print(periodicidade_df)
            else:
                print('Não foi possível extrair a periodicidade 2')
        else:
            raise ValueError("Chaves necessárias não encontradas em df3")

    except Exception as e:
        print(f"Erro: {e}")

    try:
        df_test = dragonite.mostrar_matches(texto)
        _df1 = df_test.iloc[:2]
        _df2 = df_test.iloc[2:]

        periodicidade_df = dragonite.combinar_periodicidade(_df1, _df2)
        display(periodicidade_df)

        periodicidade_array.append(_df1)
        periodicidade_array.append(_df2)
    except Exception as e:
        print(f"Erro: {e}")

    result_df = dragonite.concatenate_dataframes(array_df, axis=1)
    return result_df, periodicidade_array

def criar_e_salvar_planilha(pdf_path, pagina, dragonite):
    """Cria e salva uma planilha Excel com base em uma página do PDF."""
    # Processar a página
    texto = processar_pagina(dragonite, pagina)

    # Criar DataFrames e extrair periodicidade
    result_df, periodicidade_array = criar_dataframes_e_periodicidade(dragonite, texto)

    # Obter nome do arquivo
    file_name = obter_nome_arquivo(pdf_path)

    # ... Outras tarefas para criar e salvar a planilha ...


def main():
    # Nome do arquivo
    file_name = obter_nome_arquivo(pdf_path)
    print(file_name)

  
    # Instanciar Dragonite
    dragonite = Dragonite(pdf_path)

    # Total de páginas
    total_paginas = int(dragonite.number_of_pages)
    print('\nTotal de Paginas:', total_paginas)

    for pagina in range(66, total_paginas + 1):
        criar_e_salvar_planilha(pdf_path, pagina, dragonite)

if __name__ == "__main__":
    main()
