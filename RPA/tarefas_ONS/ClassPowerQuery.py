import pandas as pd
import camelot

class MiniPowerQuery:
    def __init__(self, file_path: str, sheet_name: str = 0):
        """
        Inicializa a classe carregando um arquivo Excel, CSV ou PDF.
        """
        if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            self.df = pd.read_excel(file_path, sheet_name=sheet_name)
        elif file_path.endswith(".csv"):
            self.df = pd.read_csv(file_path)
        elif file_path.endswith(".pdf"):
            tables = camelot.read_pdf(file_path, pages="all", flavor="lattice")
            if len(tables) == 0:
                raise ValueError("Nenhuma tabela encontrada no PDF.")
            self.df = tables[0].df
        else:
            raise ValueError("Formato de arquivo não suportado!")
        
        print(f"Arquivo {file_path} carregado com sucesso! Linhas: {len(self.df)}")

    # --- NOVOS MÉTODOS ESPECIAIS PARA REPLICAR SEU SCRIPT ---
    def use_first_rows_as_header(self, n=2):
        """
        Usa as primeiras `n` linhas como header concatenado.
        """
        headers = []
        for i in range(len(self.df.columns)):
            parts = [str(self.df.iloc[j, i]).strip() for j in range(n)]
            header = " ".join([p for p in parts if p not in [None, "nan", "_", ""]]).strip()
            if not header:
                header = f"Coluna{i+1}"
            headers.append(header)
        self.df.columns = headers
        self.df = self.df.iloc[n:].reset_index(drop=True)
        return self

    def split_columns_by_delimiter(self, delimiter="^"):
        """
        Divide colunas que possuem um delimitador específico.
        Exemplo: "Ponta^Obs" -> duas colunas: "Ponta Valor", "Ponta Anotacao".
        """
        for col in list(self.df.columns):
            if self.df[col].astype(str).str.contains(delimiter).any():
                new_cols = [f"{col} Valor", f"{col} Anotacao"]
                self.df[new_cols] = self.df[col].astype(str).str.split(delimiter, n=1, expand=True)
                self.df = self.df.drop(columns=[col])
        return self

    def standardize_columns(self, mapping: dict):
        """
        Renomeia colunas para nomes padronizados, similar ao PowerQuery.
        """
        self.df = self.df.rename(columns=mapping)
        return self

    # --- MÉTODOS BÁSICOS ---
    def rename_columns(self, mapping: dict):
        self.df = self.df.rename(columns=mapping)
        return self

    def add_column(self, col_name: str, func):
        self.df[col_name] = func(self.df)
        return self

    def filter_rows(self, condition):
        self.df = self.df[condition(self.df)]
        return self

    def group_by(self, cols, agg_map: dict):
        self.df = self.df.groupby(cols).agg(agg_map).reset_index()
        return self

    def drop_nulls(self, cols=None):
        self.df = self.df.dropna(subset=cols)
        return self

    def drop_duplicates(self, cols=None):
        self.df = self.df.drop_duplicates(subset=cols)
        return self

    def trim_spaces(self):
        self.df = self.df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        return self

    def export(self, output_path: str):
        if output_path.endswith(".xlsx"):
            self.df.to_excel(output_path, index=False)
        elif output_path.endswith(".csv"):
            self.df.to_csv(output_path, index=False)
        else:
            raise ValueError("Formato de exportação não suportado!")
        print(f"Arquivo exportado para {output_path}")
        return self

    def preview(self, n=5):
        print(self.df.head(n))
        return self
