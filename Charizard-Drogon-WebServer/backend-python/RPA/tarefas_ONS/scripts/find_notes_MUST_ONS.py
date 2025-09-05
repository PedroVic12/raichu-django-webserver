import re
import pandas as pd

class PDFTextProcessor:
    def __init__(self, file_path: str):
        """
        Inicializa a classe lendo o conteúdo do arquivo .txt.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            self.texto = f.read()
        print(f"Arquivo {file_path} carregado com sucesso! Tamanho: {len(self.texto)} caracteres.")

    def extrair_letras_enumeradas(self):
        """
        Extrai seções enumeradas no formato (A), (B), (C)... do texto.
        Retorna DataFrame com Letra e Conteudo.
        """
        padrao = r"\(([A-Z])\)\s*(.*?)(?=\([A-Z]\)|$)"
        matches = re.findall(padrao, self.texto, re.DOTALL)
        df = pd.DataFrame([{"Letra": m[0], "Conteudo": m[1].strip()} for m in matches])
        return df

    def extrair_empresa(self, ):
        """
        Busca bruta por nomes da empresa no texto.
        """
        nome_empresa=["JAGUARI", "ELETROPAULO", "NEOENERGIA ELEKTRO", "CPFL PAULISTA", "PIRATINGA"]

        for empresa in nome_empresa:
            padrao = rf"\b{empresa}\b"
            match = re.search(padrao, self.texto, re.IGNORECASE)
            if match:
                return empresa
            else:
                continue
        return None

    def extrair_tabela_bruta(self):
        """
        Heurística simples para detectar linhas de tabela (muitos números).
        """
        linhas = self.texto.splitlines()
        tabela = [linha for linha in linhas if re.search(r"\d", linha) and ("MW" in linha or "kV" in linha)]
        return pd.DataFrame({"Linha_Tabela": tabela}) if tabela else pd.DataFrame()

    def processar(self):
        """
        Processa tudo e retorna dois DataFrames:
        - df_letras (Empresa, Letra, Conteudo)
        - df_tabela (linhas cruas da tabela)
        """
        empresa = self.extrair_empresa()
        df_letras = self.extrair_letras_enumeradas()
        if not df_letras.empty:
            df_letras["Empresa"] = empresa

        df_tabela = self.extrair_tabela_bruta()
        return df_letras, df_tabela


# ------------------ USO ------------------ #
if __name__ == "__main__":
    # ------------------ TESTE ------------------ #
    texto = """CUST-2002-132-41 – JAGUARI 
    Contrato assinado digitalmente  
    (C) - O atendimento ao MUST fica condicionado...
    (D) - Para o ponto de conexão Casa Branca 5 138 kV...
    (E) - O atendimento ao MUST fica condicionado...
    """

    arquivo_texto = "/home/pedrov12/Documentos/GitHub/raichu-django-webserver/RPA/tarefas_ONS/assets/must_Eletropaulo_extract_text.txt"

    processor = PDFTextProcessor(arquivo_texto)

    df_letras, df_tabela = processor.processar()

    print("=== Seções com letras ===")
    print(df_letras)

    print("\n=== Possível tabela detectada ===")
    print(df_tabela)

    # mescla um df final

    final_df = pd.concat([df_letras, df_tabela], ignore_index=True)
    print("\n=== DataFrame Final ===")
    print(final_df)

    final_df.to_excel("./output.xlsx", index=False)


