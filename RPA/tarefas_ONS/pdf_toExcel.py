from models.Dragonite_PDF import Dragonite
from models.Palkia_Excel import Palkia
import pandas as pd

#from models.Dragonite_PDF import Dragonite


#constantes
pdf_path = r'C:\Users\PedroVictorRodrigues\Documents\GitHub\elon-musk\Tecnologia e Inovação\Automações\assets\PDF\SJ - SAGITARIUS 2023-07-21.pdf'
linux_path = r'/home/pedrov12/Documentos/GitHub/elon-musk/Tecnologia e Inovação/Automações/assets/PDF/SJ - SAGITARIUS 2023-07-21.pdf'

#Pegando o nome do arquivo
fileName = pdf_path.find('SJ')
fileName = pdf_path[fileName:]
print(fileName)

#! Incovando o Dragonite
dragonite = Dragonite(linux_path)

total_paginas = int(dragonite.number_of_pages)
print('\nTotal de Paginas:',total_paginas)



for pagina in range(66, total_paginas+1):

    print('\n\nPagina: ', pagina)


    #!Lendo pdf
    texto = dragonite.ler_pagina(pagina)

    #Pegando o nome do equipamento para cada DF
    titulo_df = dragonite.find_start_P(texto)

    equipamento_array = dragonite.find_end_P(texto)

    if not equipamento_array:
        equipamento_array = ['coluna equipamento']

    print(equipamento_array)

    try:
        df_test = dragonite.mostrar_matches(texto)
        df_test
    except:
        print('Não foi encontrado nenhum match')



    #! Extraindo os dados
    colunas = ['Ações de manutenção','Medidas de segurança']

    array_df = []
    periodicidade_array = []

    # Create the dataframe
    df1 = dragonite.criar_dataframeManutencao(texto)
    array_df.append(df1)

    df2 = dragonite.criar_dataframeSeguranca(texto)
    array_df.append(df2)

    try:
        df3 = dragonite.extrair_periodicidade(texto)

        # se df3 for vazio
        if isinstance(df3, dict):
            if not df3:
                df_test = dragonite.mostrar_matches(texto)
                periodicidade_array.append(df_test)
        else:
            try:
                if df3.empty:
                    df_test = dragonite.mostrar_matches(texto)
                    periodicidade_array.append(df_test)
            except Exception:
                pass

        # Verifique se df3 contém as chaves necessárias (quando for dict)
        if isinstance(df3, dict) and all(key in df3 for key in ['Inspection', 'Drydock', 'Sampling']):
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
            # Quando não tiver as chaves esperadas apenas segue sem periodicidade
            raise ValueError("Chaves necessárias não encontradas em df3")

    except Exception as e:  # Capturar a exceção para obter informações adicionais
        print(f"Erro: {e}")


    try:
        df_test = dragonite.mostrar_matches(texto)

        # Separando o DataFrame em dois DataFrames menores
        _df1 = df_test.iloc[:2]
        _df2 = df_test.iloc[2:]

        periodicidade_df = dragonite.combinar_periodicidade(_df1, _df2)
        # print(periodicidade_df)  # display é específico de notebook

        periodicidade_array.append(_df1)
        periodicidade_array.append(_df2)
    except Exception as e:  # Capturar a exceção para obter informações adicionais
        print(f"Erro: {e}")

    result_df = dragonite.concatenate_dataframes(array_df, axis=1)
 
    #! Resultados obtidos
    print('Lista de Equipamentos da Pagina:',equipamento_array)
    print('Titulos: ',titulo_df)

    # Displaying the dataframe
    #display(result_df)
    print(result_df)

    # Displaying the dataframe
    try:
        print(periodicidade_array[0])
    except:
        print('Não foi encontrado nenhuma periodicidade na página')

    #!Invocando o Palkia
    caminho_output = "/home/pedrov12/Documentos/GitHub/elon-musk/Tecnologia e Inovação/Automações/Manipulando PDF e Word/output/Excel/models/"
    p = Palkia(nome_arquivo=f'{caminho_output}template_model_{pagina}.xlsx',
            sheet_name=equipamento_array[0])

    #! Primeira tabela
    try:
        p.clear_worksheet(equipamento_array[0])
        p.merge_cells_range(equipamento_array[0], 'A1:F1')
    except:
        print('Nao consigo mesclar as celulas')
        
    # Adicionar título
    if titulo_df:
        p.add_title(equipamento_array[0], 'A1', titulo_df[0], font_size=16)
    else:
        print('Sem título na página, pulando título da primeira tabela')

    # Primeira Coluna
    try:
        lastRow = p.get_last_row(equipamento_array[0], 'A')
        print(lastRow)
        if 'Ações de manutenção 1' in result_df.columns:
            p.add_dataframe(equipamento_array[0], result_df[['Ações de manutenção 1']], lastRow+1, 1, color_option='verde_claro')
        else:
            print('Coluna ausente: Ações de manutenção 1')
    except:
        print('ERRO na primeira coluna')

    # Segunda Coluna
    try:
        lastRow = p.get_last_row(equipamento_array[0], 'A')
        print(lastRow)
        if 'Medidas de segurança 1' in result_df.columns:
            p.add_dataframe(equipamento_array[0], result_df[['Medidas de segurança 1']], lastRow + 2, 1, color_option='azul_claro')
        else:
            print('Coluna ausente: Medidas de segurança 1')
    except:
        print('ERRO na segunda coluna')

    #Terceira Coluna
    try:
        lastRow = p.get_last_row(equipamento_array[0], 'B')
        print(lastRow)
        if len(periodicidade_array) > 0:
            p.add_dataframe(equipamento_array[0], periodicidade_array[0], lastRow+2, 2, color_option='laranja_claro')
        else:
            print('Sem periodicidade para a primeira tabela')


    except Exception as e:
        print('ERRO na periodicidade', e)

    # Salvar o arquivo Excelzs
    #p.colorir_colunasTabelas(equipamento_array[0],1)
    p.format_columns(equipamento_array[0], 'A', width= 25)
    p.format_columns(equipamento_array[0], 'B', 'F', 15)
    p.save()




    #! Segunda Tabela
    # Mesclar células para o título

    try:
        # Apenas se houver um segundo título
        if len(titulo_df) > 1:
            p.merge_cells_range(equipamento_array[0], 'H1:M1')
            p.add_title(equipamento_array[0], 'H1', titulo_df[1], font_size=16)
        else:
            raise IndexError('Somente um título nesta página')

    except Exception:
        print('So possui um titulo nessa pagina')

    # Primeira Coluna
    try:
        lastRow = p.get_last_row(equipamento_array[0], 'H')
        print(lastRow)
        if 'Ações de manutenção 2' in result_df.columns:
            p.add_dataframe(equipamento_array[0], result_df[['Ações de manutenção 2']], lastRow+1, 8, color_option='verde_claro')
        else:
            print('Nao encontro coluna: Ações de manutenção 2')
    except:
        print('Nao consigo adicionar a primeira coluna')

    # Segunda Coluna
    try:
        lastRow = p.get_last_row(equipamento_array[0], 'H')
        print(lastRow)
        if 'Medidas de segurança 2' in result_df.columns:
            p.add_dataframe(equipamento_array[0], result_df[['Medidas de segurança 2']], lastRow + 1 , 8, color_option='azul_claro')
        else:
            print('Nao encontro coluna: Medidas de segurança 2')
    except:
        print('Nao consigo adicionar a segunda coluna')

    #Terceira Colunadx    
    try:
        lastRow = p.get_last_row(equipamento_array[0], 'I')
        print(lastRow)
        if len(periodicidade_array) > 1:
            p.add_dataframe(equipamento_array[0], periodicidade_array[1], lastRow+2, 9, color_option='laranja_claro')
        else:
            print('Sem periodicidade para a segunda tabela')

    except Exception as e:
        print('Erro na periodicidade', e)


    # Salvar o arquivo Excelzs
    #p.colorir_colunasTabelas(equipamento_array[0],1)
    p.format_columns(equipamento_array[0], 'H', width= 25)
    p.format_columns(equipamento_array[0], 'I', 'L', 15)


    p.save()




