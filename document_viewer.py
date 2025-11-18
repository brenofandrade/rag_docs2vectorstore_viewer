import streamlit as st
import base64
import re
from io import BytesIO
from pathlib import Path
import tempfile

# Bibliotecas para PDF
try:
    import pypdf
except ImportError:
    import PyPDF2 as pypdf

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class PDFCleaner:
    """Classe para processar e limpar texto de PDFs."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_file):
        """Extrai texto de um arquivo PDF."""
        try:
            pdf_reader = pypdf.PdfReader(pdf_file)
            text = []
            for page in pdf_reader.pages:
                text.append(page.extract_text())
            return "\n\n".join(text)
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {e}")
            return None
    
    @staticmethod
    def clean_text(text):
        """Aplica todas as limpezas no texto."""
        if not text:
            return ""
        
        # 1. Remover quebras de linha desnecessárias
        # Mantém quebras duplas (parágrafos), remove simples
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 2. Remover múltiplos espaços
        text = re.sub(r' +', ' ', text)
        
        # 3. Remover caracteres especiais (mantém pontuação básica)
        # Mantém: letras, números, pontuação comum, espaços e quebras de linha
        text = re.sub(r'[^\w\s.,!?;:()\-—–""\'`\n]', '', text, flags=re.UNICODE)
        
        # 4. Normalizar espaçamentos ao redor de pontuação
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
        
        # 5. Remover linhas muito curtas (possíveis cabeçalhos/rodapés)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Remove linhas com menos de 20 caracteres ou apenas números (páginas)
            if len(line) > 20 and not line.isdigit():
                cleaned_lines.append(line)
        
        text = '\n\n'.join(cleaned_lines)
        
        # 6. Remover múltiplas quebras de linha
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 7. Limpar espaços no início e fim
        text = text.strip()
        
        return text
    
    @staticmethod
    def create_pdf_from_text(text, output_path=None):
        """Gera um novo PDF a partir do texto limpo."""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Estilo customizado para o texto
        custom_style = ParagraphStyle(
            'CustomStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=12,
        )
        
        # Divide o texto em parágrafos e cria elementos
        story = []
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                # Escapa caracteres especiais para reportlab
                para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                p = Paragraph(para, custom_style)
                story.append(p)
                story.append(Spacer(1, 0.1 * inch))
        
        doc.build(story)
        return output_path


def display_pdf(pdf_file, key):
    """Exibe o PDF no Streamlit usando base64 encoding."""
    try:
        # Lê o conteúdo do arquivo
        if isinstance(pdf_file, str):
            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()
        else:
            pdf_bytes = pdf_file.getvalue()
        
        # Converte para base64
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Embed do PDF
        pdf_display = f'''
            <iframe 
                src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="800" 
                type="application/pdf"
                style="border: 1px solid #ccc;"
            ></iframe>
        '''
        
        st.markdown(pdf_display, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao exibir PDF: {e}")


def main():
    st.set_page_config(page_title="PDF Cleaner & Visualizer", layout="wide")
    
    st.title("🧹 PDF Cleaner & Visualizer")
    st.markdown("### Limpe e visualize seus PDFs antes de inserir no Vector Store")
    
    col_1, col_2, col_3 = st.columns([1,1,1])

    with st.sidebar:
        # Upload do arquivo
        uploaded_file = st.file_uploader(
            "📄 Faça upload do seu PDF", 
            type=['pdf'],
            help="Selecione um arquivo PDF para processar"
        )
    
    if uploaded_file is not None:
        st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
        
        # Extrair texto
        with st.spinner("Extraindo texto do PDF..."):
            original_text = PDFCleaner.extract_text_from_pdf(uploaded_file)
        
        if original_text:
            # Processar texto
            with st.spinner("Aplicando limpezas no texto..."):
                cleaned_text = PDFCleaner.clean_text(original_text)
            
            # Métricas de limpeza
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📝 Caracteres Original", f"{len(original_text):,}")
            with col2:
                st.metric("✨ Caracteres Limpo", f"{len(cleaned_text):,}")
            with col3:
                reduction = ((len(original_text) - len(cleaned_text)) / len(original_text) * 100)
                st.metric("📉 Redução", f"{reduction:.1f}%")
            with col4:
                words = len(cleaned_text.split())
                st.metric("💬 Palavras", f"{words:,}")
            
            st.markdown("---")
            
            # Abas para diferentes visualizações
            tab1, tab2, tab3 = st.tabs(["📊 Comparação Visual", "📄 Texto Original", "✨ Texto Limpo"])
            
            with tab1:
                st.markdown("### Comparação Lado a Lado")
                
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("#### 📄 PDF Original")
                    display_pdf(uploaded_file, "original")
                
                with col_right:
                    st.markdown("#### ✨ Texto Processado")
                    st.text_area(
                        "Visualização do texto limpo",
                        cleaned_text,
                        height=800,
                        key="cleaned_preview"
                    )
            
            with tab2:
                st.markdown("### 📄 Texto Extraído (Original)")
                st.text_area(
                    "Texto original extraído do PDF",
                    original_text,
                    height=600,
                    key="original_text"
                )
            
            with tab3:
                st.markdown("### ✨ Texto Limpo (Processado)")
                st.text_area(
                    "Texto após todas as limpezas",
                    cleaned_text,
                    height=600,
                    key="cleaned_text"
                )
            
            # Seção de ações
            st.markdown("---")
            st.markdown("### 🎯 Ações")
            
            col_a, col_b, col_c = st.columns([2, 2, 2])
            
            with col_a:
                # Botão para copiar texto limpo
                if st.button("📋 Copiar Texto Limpo", use_container_width=True):
                    st.code(cleaned_text, language=None)
                    st.info("💡 Use Ctrl+A e Ctrl+C para copiar o texto acima")
            
            with col_b:
                # Download do texto como .txt
                st.download_button(
                    label="💾 Baixar como TXT",
                    data=cleaned_text,
                    file_name=f"{Path(uploaded_file.name).stem}_limpo.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_c:
                # Gerar e baixar PDF limpo (opcional)
                if st.button("📄 Gerar PDF Limpo", use_container_width=True):
                    with st.spinner("Gerando PDF..."):
                        try:
                            pdf_path = PDFCleaner.create_pdf_from_text(cleaned_text)
                            
                            with open(pdf_path, 'rb') as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="⬇️ Baixar PDF Limpo",
                                data=pdf_bytes,
                                file_name=f"{Path(uploaded_file.name).stem}_limpo.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ PDF gerado com sucesso!")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar PDF: {e}")
            
            # Preview das limpezas aplicadas
            with st.expander("🔍 Ver detalhes das limpezas aplicadas"):
                st.markdown("""
                **Limpezas aplicadas automaticamente:**
                
                1. ✂️ **Quebras de linha desnecessárias** - Remove quebras simples, mantém parágrafos
                2. 🧹 **Espaços múltiplos** - Normaliza para espaços simples
                3. 🚫 **Caracteres especiais** - Remove símbolos inválidos
                4. 📏 **Espaçamento** - Normaliza espaços ao redor de pontuação
                5. 🗑️ **Cabeçalhos/Rodapés** - Remove linhas muito curtas (< 20 caracteres)
                6. 🔢 **Números de página** - Remove linhas que são apenas números
                7. 📐 **Quebras excessivas** - Reduz múltiplas quebras para duplas
                """)
    
    else:
        st.info("👆 Faça upload de um arquivo PDF para começar")
        
        # Instruções
        with st.expander("ℹ️ Como usar"):
            st.markdown("""
            ### Passo a passo:
            
            1. **Upload**: Carregue seu arquivo PDF usando o botão acima
            2. **Visualize**: Compare o PDF original com o texto processado
            3. **Analise**: Veja as métricas de redução e limpeza
            4. **Exporte**: Baixe como TXT ou gere um novo PDF limpo
            5. **Use**: Utilize o texto limpo para seu Vector Store
            
            ### Benefícios da limpeza:
            
            - 🎯 **Melhor indexação** no Vector Store
            - 🚀 **Buscas mais precisas** com menos ruído
            - 💰 **Economia de tokens** ao usar embeddings
            - 📊 **Dados mais estruturados** para processamento
            """)


if __name__ == "__main__":
    main()