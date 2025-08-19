import pandas as pd
import re
import camelot
import tabula
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract


class MiniPowerQuery:
    def __init__(self, file_path: str = None):
        self.df = pd.DataFrame()
        self.file_path = file_path

    # -------------------- ETAPA DE EXTRACÃO --------------------
    def from_excel(self, file_path: str, sheet_name=0):
        self.df = pd.read_excel(file_path, sheet_name=sheet_name)
        return self

    def from_csv(self, file_path: str):
        self.df = pd.read_csv(file_path)
        return self

    def from_pdf_tabula(self, file_path: str, pages="all"):
        """Extrai tabelas de PDF usando Tabula (precisa de Java)."""
        try:
            tabelas = tabula.read_pdf(file_path, pages=pages, multiple_tables=True, stream=True)
            if tabelas:
                self.df = tabelas[0]
        except Exception as e:
            print(f"Erro Tabula: {e}")
        return self

    def from_pdf_camelot(self, file_path: str, pages="all"):
        """Extrai tabelas de PDF usando Camelot (melhor para tabelas delimitadas)."""
        tables = camelot.read_pdf(file_path, pages=pages, flavor="lattice")
        if len(tables) > 0:
            self.df = tables[0].df
        return self

    def from_pdf_text(self, file_path: str, pages="all"):
        """Extrai texto de PDF usando PyPDF2."""
        texto = ""
        reader = PdfReader(file_path)
        if pages == "all":
            paginas = range(len(reader.pages))
        else:
            paginas = [int(p) - 1 for p in pages.split(",")]
        for p in paginas:
            texto += reader.pages[p].extract_text() or ""
        self.df = pd.DataFrame({"texto": [texto]})
        return self

    def from_pdf_ocr(self, file_path: str, page: int = 1):
        """Fallback: OCR com Tesseract."""
        imagens = convert_from_path(file_path, first_page=page, last_page=page)
        if imagens:
            texto = pytesseract.image_to_string(imagens[0], lang="por")
            self.df = pd.DataFrame({"texto": [texto]})
        return self

    # -------------------- ETAPA DE TRANSFORMAÇÃO --------------------
    def use_first_rows_as_header(self, n=2):
        """Usa as primeiras n linhas como cabeçalho concatenado."""
        headers = []
        for i in range(len(self.df.columns)):
            parts = [str(self.df.iloc[j, i]).strip() for j in range(n)]
            header = " ".join([p for p in parts if p not in ["None", "nan", "_", ""]]).strip()
            if not header:
                header = f"Coluna{i+1}"
            headers.append(header)
        self.df.columns = headers
        self.df = self.df.iloc[n:].reset_index(drop=True)
        return self

    def split_columns_by_delimiter(self, delimiter="^"):
        """Divide colunas que possuem delimitador."""
        for col in list(self.df.columns):
            if self.df[col].astype(str).str.contains(delimiter).any():
                new_cols = [f"{col} Valor", f"{col} Anotacao"]
                self.df[new_cols] = self.df[col].astype(str).str.split(delimiter, n=1, expand=True)
                self.df = self.df.drop(columns=[col])
        return self

    def standardize_columns(self, mapping: dict):
        """Renomeia colunas de acordo com mapping (como PowerQuery)."""
        self.df = self.df.rename(columns=mapping)
        return self

    def aplicar_regex(self, padroes: dict):
        """Aplica regex sobre colunas de texto únicas."""
        if "texto" not in self.df.columns:
            return self
        texto = " ".join(self.df["texto"].tolist())
        dados = {}
        for nome, padrao in padroes.items():
            m = re.search(padrao, texto, re.DOTALL)
            dados[nome] = m.group(1).strip() if m else None
        self.df = pd.DataFrame([dados])
        return self

    # -------------------- OPERAÇÕES AUXILIARES --------------------
    def drop_nulls(self, cols=None):
        self.df = self.df.dropna(subset=cols)
        return self

    def drop_duplicates(self, cols=None):
        self.df = self.df.drop_duplicates(subset=cols)
        return self

    def trim_spaces(self):
        self.df = self.df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        return self

    # -------------------- EXPORTAÇÃO --------------------
    def export_excel(self, output_path: str):
        self.df.to_excel(output_path, index=False)
        print(f"Arquivo exportado para {output_path}")
        return self

    def export_csv(self, output_path: str):
        self.df.to_csv(output_path, index=False)
        print(f"Arquivo exportado para {output_path}")
        return self

    def preview(self, n=5):
        print(self.df.head(n))
        return self


mpq = MiniPowerQuery()
path = "/home/pedrov12/Downloads"

(mpq
    .from_pdf_camelot(rf"{path}/CUST-2002-123-41 - JAGUARI - RECON 2025-2028.pdf")
    .use_first_rows_as_header(n=2)
    .split_columns_by_delimiter("^")
    # .standardize_columns({
    #     "Ponto de Conexão Cód ONS¹": "Cód ONS",
    #     "Ponto de Conexão Instalação": "Instalação",
    #     "Ponto de Conexão Tensão (kV)": "Tensão (kV)",
    #     "Período de Contratação De": "De",
    #     "Período de Contratação Até": "Até",
    #     "MUST - 2025 Ponta (MW) Valor": "Ponta 2025 Valor",
    #     "MUST - 2025 Ponta (MW) Anotacao": "Ponta 2025 Anotacao",
    #     "MUST - 2025 Fora Ponta (MW) Valor": "Fora Ponta 2025 Valor",
    #     "MUST - 2025 Fora Ponta (MW) Anotacao": "Fora Ponta 2025 Anotacao",
    # })
    .trim_spaces()
    .drop_duplicates()
    .export_excel("saida_final.xlsx")
)
