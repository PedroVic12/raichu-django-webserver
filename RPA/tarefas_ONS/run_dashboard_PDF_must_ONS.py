import os
import re
import json
import pandas as pd
import tabula
import streamlit as st
import tempfile
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
#from tabula.errors import JavaNotFoundError
import camelot
from typing import List, Dict, Union, Tuple, Optional

class ONSPDFProcessor:
    def __init__(self):
        self.text_processor = PDFTextProcessor()
        self.table_processor = PDFTableProcessor()
        
    def process_pdf(self, 
                   file_path: str, 
                   page_config: Dict[int, bool],  # {page_num: is_table}
                   **kwargs) -> Dict[str, Union[pd.DataFrame, str]]:
        """
        Process PDF pages according to configuration.
        
        Args:
            file_path: Path to PDF file
            page_config: Dictionary mapping page numbers to boolean (True for table, False for text)
            **kwargs: Additional arguments for table/text extraction
            
        Returns:
            Dictionary with 'tables' and 'texts' keys containing extracted data
        """
        results = {'tables': [], 'texts': []}
        
        for page_num, is_table in page_config.items():
            try:
                if is_table:
                    # Try Camelot first, fall back to Tabula if needed
                    try:
                        table = self.table_processor.extract_with_camelot(
                            file_path, 
                            pages=str(page_num),
                            **kwargs.get('table_kwargs', {})
                        )
                        if not table.empty:
                            results['tables'].append((page_num, table))
                            continue
                    except Exception as e:
                        st.warning(f"Erro ao extrair tabela da página {page_num} com Camelot: {e}")
                    
                    try:
                        table = self.table_processor.extract_with_tabula(
                            file_path,
                            pages=str(page_num),
                            **kwargs.get('table_kwargs', {})
                        )
                        if not table.empty:
                            results['tables'].append((page_num, table))
                    except Exception as e:
                        st.error(f"Erro ao extrair tabela da página {page_num} com Tabula: {e}")
                else:
                    # Extract text
                    text = self.text_processor.extract_text(
                        file_path,
                        pages=str(page_num),
                        use_ocr=kwargs.get('use_ocr', False),
                        **kwargs.get('text_kwargs', {})
                    )
                    if text.strip():
                        results['texts'].append((page_num, text))
                        
            except Exception as e:
                st.error(f"Erro ao processar página {page_num}: {str(e)}")
                
        return results

    def process_all_pages(self, 
                         file_path: str, 
                         **kwargs) -> Dict[str, Union[pd.DataFrame, str]]:
        """
        Process all pages in a PDF, automatically detecting tables vs text.
        """
        # First, try to extract all tables
        tables = self.table_processor.extract_all_tables(file_path, **kwargs)
        
        # Then extract text from remaining pages
        reader = PdfReader(file_path)
        all_pages = set(range(1, len(reader.pages) + 1))
        table_pages = {t[0] for t in tables}
        text_pages = all_pages - table_pages
        
        texts = []
        for page_num in text_pages:
            try:
                text = self.text_processor.extract_text(
                    file_path,
                    pages=str(page_num),
                    use_ocr=kwargs.get('use_ocr', False),
                    **kwargs.get('text_kwargs', {})
                )
                if text.strip():
                    texts.append((page_num, text))
            except Exception as e:
                st.error(f"Erro ao extrair texto da página {page_num}: {str(e)}")
                
        return {'tables': tables, 'texts': texts}

class PDFTextProcessor:
    """Handles text extraction from PDFs using multiple methods."""
    
    def extract_text(self, 
                    file_path: str, 
                    pages: str = "1", 
                    use_ocr: bool = False,
                    **kwargs) -> str:
        """
        Extract text from PDF using the specified method.
        
        Args:
            file_path: Path to PDF file
            pages: Pages to extract (e.g., "1", "1-3", "1,3,5")
            use_ocr: Whether to use OCR for text extraction
            **kwargs: Additional arguments for text extraction
            
        Returns:
            Extracted text as string
        """
        if use_ocr:
            return self._extract_with_ocr(file_path, pages, **kwargs)
        return self._extract_with_pypdf2(file_path, pages, **kwargs)
    
    def _extract_with_pypdf2(self, file_path: str, pages: str, **kwargs) -> str:
        """Extract text using PyPDF2 (faster but less accurate for scanned docs)."""
        reader = PdfReader(file_path)
        page_nums = self._parse_pages(pages, len(reader.pages))
        text = ""
        
        for page_num in page_nums:
            try:
                text += reader.pages[page_num - 1].extract_text() or ""
            except Exception as e:
                st.warning(f"Erro ao extrair texto da página {page_num}: {str(e)}")
                
        return text
    
    def _extract_with_ocr(self, file_path: str, pages: str, **kwargs) -> str:
        """Extract text using OCR (slower but works for scanned docs)."""
        page_nums = self._parse_pages(pages, 9999)  # Large number to get all pages
        text = ""
        
        try:
            images = convert_from_path(file_path, first_page=page_nums[0], last_page=page_nums[-1])
            for i, img in enumerate(images, start=page_nums[0]):
                text += pytesseract.image_to_string(img, lang='por') + "\n\n"
        except Exception as e:
            st.error(f"Erro no OCR: {str(e)}")
            
        return text
    
    def _parse_pages(self, pages_str: str, max_pages: int) -> List[int]:
        """Parse pages string into list of page numbers (1-based)."""
        if not pages_str or pages_str.lower() == 'all':
            return list(range(1, max_pages + 1))
            
        pages = set()
        for part in pages_str.replace(' ', '').split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.update(range(start, end + 1))
            else:
                pages.add(int(part))
                
        return [p for p in sorted(pages) if 1 <= p <= max_pages]

class PDFTableProcessor:
    """Handles table extraction from PDFs using multiple methods."""
    
    def extract_all_tables(self, 
                         file_path: str,
                         **kwargs) -> List[Tuple[int, pd.DataFrame]]:
        """
        Extract all tables from PDF using best available method.
        
        Returns:
            List of (page_number, dataframe) tuples
        """
        # Try Camelot first as it's generally more accurate for well-structured tables
        try:
            return self.extract_with_camelot(file_path, **kwargs)
        except Exception as e:
            st.warning(f"Falha ao extrair tabelas com Camelot: {str(e)}")
            
        # Fall back to Tabula
        try:
            return self.extract_with_tabula(file_path, **kwargs)
        except Exception as e:
            st.error(f"Falha ao extrair tabelas com Tabula: {str(e)}")
            
        return []
    
    def extract_with_camelot(self, 
                           file_path: str,
                           pages: str = "1",
                           **kwargs) -> List[Tuple[int, pd.DataFrame]]:
        """Extract tables using Camelot."""
        tables = camelot.read_pdf(
            file_path,
            pages=pages,
            flavor='lattice',
            **kwargs
        )
        
        results = []
        for i, table in enumerate(tables):
            if not table.df.empty:
                results.append((table.page, table.df))
                
        return results
    
    def extract_with_tabula(self,
                          file_path: str,
                          pages: str = "1",
                          **kwargs) -> List[Tuple[int, pd.DataFrame]]:
        """Extract tables using Tabula."""
        try:
            tables = tabula.read_pdf(
                file_path,
                pages=pages,
                multiple_tables=True,
                stream=True,
                **kwargs
            )
            
            results = []
            for i, table in enumerate(tables):
                if not table.empty:
                    # Try to determine page number (Tabula doesn't always provide this)
                    page_num = i + 1  # Default to sequential
                    results.append((page_num, table))
                    
            return results
            
        except JavaNotFoundError:
            st.error("Erro: Java não encontrado! O Tabula precisa do Java para funcionar.")
            return []
        except Exception as e:
            st.error(f"Erro ao extrair tabelas com Tabula: {str(e)}")
            return []

# --- Streamlit Interface ---

def main():
    st.set_page_config(layout="wide")
    st.title("📄 Processador de PDFs do ONS")
    
    # Initialize processor
    processor = ONSPDFProcessor()
    
    # File upload
    uploaded_file = st.file_uploader("Carregar arquivo PDF", type="pdf")
    
    if uploaded_file:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            file_path = tmp_file.name
        
        try:
            # Get PDF info
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            
            # Page selection and configuration
            st.sidebar.subheader("Configuração das Páginas")
            selected_pages = st.sidebar.text_input(
                "Páginas para processar (ex: 1-3,5,7-9 ou 'all')",
                value="all"
            )
            
            # Auto-detect or manual configuration
            process_mode = st.sidebar.radio(
                "Modo de Processamento",
                ["Detecção Automática", "Configuração Manual por Página"]
            )
            
            page_config = {}
            
            if process_mode == "Configuração Manual por Página":
                st.sidebar.subheader("Configuração por Página")
                for i in range(1, total_pages + 1):
                    page_config[i] = st.sidebar.checkbox(
                        f"Página {i} - Tabela (desmarque para texto)",
                        value=True,
                        key=f"page_{i}"
                    )
            else:
                # Auto-detect mode - just process all pages
                page_nums = processor.text_processor._parse_pages(selected_pages, total_pages)
                page_config = {i: True for i in page_nums}  # Default to table extraction
                
            # Processing options
            st.sidebar.subheader("Opções de Processamento")
            use_ocr = st.sidebar.checkbox("Usar OCR para extração de texto", value=False)
            show_text = st.sidebar.checkbox("Mostrar texto extraído", value=True)
            
            # Process button
            if st.sidebar.button("Processar PDF", type="primary"):
                with st.spinner("Processando PDF..."):
                    if process_mode == "Configuração Manual por Página":
                        # Process with manual configuration
                        results = processor.process_pdf(
                            file_path,
                            page_config,
                            use_ocr=use_ocr
                        )
                    else:
                        # Auto-detect mode
                        results = processor.process_all_pages(
                            file_path,
                            use_ocr=use_ocr
                        )
                    
                    # Display results
                    st.subheader("Resultados")
                    
                    # Show tables
                    if results['tables']:
                        st.subheader("📊 Tabelas Extraídas")
                        for page_num, table in results['tables']:
                            with st.expander(f"Tabela da Página {page_num}"):
                                st.dataframe(table)
                                
                                # Download button
                                csv = table.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    f"Baixar Tabela Página {page_num}",
                                    csv,
                                    f"tabela_pg{page_num}.csv",
                                    "text/csv",
                                    key=f"table_{page_num}"
                                )
                    
                    # Show extracted text
                    if results['texts'] and show_text:
                        st.subheader("📝 Texto Extraído")
                        for page_num, text in results['texts']:
                            with st.expander(f"Texto da Página {page_num}"):
                                st.text_area(
                                    f"Texto Página {page_num}",
                                    text,
                                    height=200,
                                    key=f"text_{page_num}"
                                )
                                
                                # Download button
                                st.download_button(
                                    f"Baixar Texto Página {page_num}",
                                    text,
                                    f"texto_pg{page_num}.txt",
                                    "text/plain",
                                    key=f"text_dl_{page_num}"
                                )
                                
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")
            st.exception(e)
            
        finally:
            # Clean up temp file
            try:
                os.unlink(file_path)
            except:
                pass

if __name__ == '__main__':
    main()