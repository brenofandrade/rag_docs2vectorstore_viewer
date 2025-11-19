import streamlit as st
import base64
import re
from io import BytesIO
from pathlib import Path
import tempfile
from typing import List, Tuple

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
    def clean_text(text, remove_line_breaks=True, remove_headers=True):
        """Aplica limpezas configuráveis no texto.

        Args:
            text: Texto a ser limpo
            remove_line_breaks: Se True, remove quebras de linha desnecessárias
            remove_headers: Se True, remove cabeçalhos/rodapés
        """
        if not text:
            return ""

        # 1. Remover quebras de linha desnecessárias (opcional)
        if remove_line_breaks:
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

        # 5. Remover linhas muito curtas (possíveis cabeçalhos/rodapés) - opcional
        if remove_headers:
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
    def chunk_text(text, chunk_size=500, chunk_overlap=50) -> List[Tuple[str, int, int]]:
        """Divide o texto em chunks com sobreposição.

        Args:
            text: Texto a ser dividido
            chunk_size: Tamanho de cada chunk em caracteres
            chunk_overlap: Sobreposição entre chunks em caracteres

        Returns:
            Lista de tuplas (chunk_text, start_pos, end_pos)
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append((chunk, start, end))

            # Move start com consideração de overlap
            start = end - chunk_overlap

            # Evita loop infinito
            if start <= chunks[-1][1]:
                start = end

        return chunks

    @staticmethod
    def highlight_chunks_html(text, chunk_size=500, chunk_overlap=50) -> str:
        """Gera HTML com chunks destacados com cores alternadas.

        Args:
            text: Texto com chunks
            chunk_size: Tamanho de cada chunk
            chunk_overlap: Sobreposição entre chunks

        Returns:
            HTML com chunks destacados
        """
        chunks = PDFCleaner.chunk_text(text, chunk_size, chunk_overlap)

        if not chunks:
            return text

        # Cores para alternância dos chunks
        colors = ['#FFF59D', '#B3E5FC', '#C8E6C9', '#F8BBD0', '#D1C4E9', '#FFCCBC']

        # Criar mapa de posições para destacar
        html_parts = []
        last_end = 0

        for idx, (chunk_text, start, end) in enumerate(chunks):
            color = colors[idx % len(colors)]

            # Adiciona texto anterior ao chunk (sem destaque)
            if start > last_end:
                html_parts.append(text[last_end:start])

            # Escapa HTML e adiciona chunk com destaque
            escaped_chunk = text[start:end].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            html_parts.append(f'<span style="background-color: {color}; padding: 2px 4px; border-radius: 3px;">{escaped_chunk}</span>')

            last_end = end

        # Adiciona texto restante
        if last_end < len(text):
            html_parts.append(text[last_end:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>'))

        return ''.join(html_parts)
    
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
        st.markdown("## ⚙️ Configurações")

        # Upload do arquivo
        uploaded_file = st.file_uploader(
            "📄 Faça upload do seu PDF",
            type=['pdf'],
            help="Selecione um arquivo PDF para processar"
        )

        st.markdown("---")

        # Controles de Chunking
        st.markdown("### 📦 Configurações de Chunks")
        chunk_size = st.slider(
            "Tamanho do Chunk (caracteres)",
            min_value=100,
            max_value=10000,
            value=500,
            step=50,
            help="Quanto maior, menos chunks serão criados"
        )

        chunk_overlap = st.slider(
            "Sobreposição entre Chunks (caracteres)",
            min_value=0,
            max_value=500,
            value=50,
            step=10,
            help="Caracteres compartilhados entre chunks consecutivos"
        )

        st.markdown("---")

        # Opções de Limpeza
        st.markdown("### 🧹 Opções de Limpeza")
        remove_headers = st.checkbox(
            "🗑️ Remover cabeçalhos/rodapés",
            value=True,
            help="Remove linhas muito curtas e números de página"
        )

        remove_line_breaks = st.checkbox(
            "✂️ Remover quebras de linha",
            value=True,
            help="Remove quebras simples, mantém parágrafos"
        )

        st.markdown("---")

        # Opções de Visualização
        st.markdown("### 👁️ Opções de Visualização")
        show_chunks = st.checkbox(
            "🎯 Destacar chunks no texto",
            value=True,
            help="Mostra os chunks com cores diferentes"
        )
    
    if uploaded_file is not None:
        st.success(f"✅ Arquivo carregado: {uploaded_file.name}")

        # Extrair texto
        with st.spinner("Extraindo texto do PDF..."):
            original_text = PDFCleaner.extract_text_from_pdf(uploaded_file)

        if original_text:
            # Processar texto com opções dinâmicas
            with st.spinner("Aplicando limpezas no texto..."):
                cleaned_text = PDFCleaner.clean_text(
                    original_text,
                    remove_line_breaks=remove_line_breaks,
                    remove_headers=remove_headers
                )

            # Calcular chunks
            chunks = PDFCleaner.chunk_text(cleaned_text, chunk_size, chunk_overlap)

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
                st.metric("📦 Total de Chunks", f"{len(chunks)}")

            # Métricas de Chunks
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📏 Tamanho do Chunk", f"{chunk_size} chars")
            with col2:
                st.metric("🔗 Sobreposição", f"{chunk_overlap} chars")
            with col3:
                avg_chunk_size = sum(len(c[0]) for c in chunks) // len(chunks) if chunks else 0
                st.metric("📊 Tamanho Médio", f"{avg_chunk_size} chars")
            with col4:
                words = len(cleaned_text.split())
                st.metric("💬 Palavras", f"{words:,}")

            st.markdown("---")
            
            # Abas para diferentes visualizações
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparação Visual", "📄 Texto Original", "✨ Texto Limpo", "🎯 Chunks Destacados"])

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

            with tab4:
                st.markdown("### 🎯 Chunks Destacados")

                if show_chunks:
                    # Gerar HTML com chunks destacados
                    highlighted_html = PDFCleaner.highlight_chunks_html(
                        cleaned_text,
                        chunk_size,
                        chunk_overlap
                    )

                    # Exibir HTML
                    st.markdown(
                        f'<div style="border: 1px solid #ddd; padding: 20px; border-radius: 5px; overflow-y: auto; height: 600px; font-family: monospace; font-size: 14px; line-height: 1.6;">{highlighted_html}</div>',
                        unsafe_allow_html=True
                    )

                    # Informações dos chunks
                    st.markdown("---")
                    st.markdown("#### 📊 Informações dos Chunks")

                    chunk_info = []
                    for idx, (chunk_text, start, end) in enumerate(chunks):
                        chunk_info.append({
                            "Chunk": idx + 1,
                            "Tamanho": len(chunk_text),
                            "Início": start,
                            "Fim": end,
                            "Palavras": len(chunk_text.split())
                        })

                    st.dataframe(chunk_info, width='stretch')

                else:
                    st.info("👆 Habilite 'Destacar chunks no texto' na sidebar para ver os chunks destacados")

            # Seção de ações
            st.markdown("---")
            st.markdown("### 🎯 Ações")
            
            col_a, col_b, col_c = st.columns([2, 2, 2])
            
            with col_a:
                # Botão para copiar texto limpo
                if st.button("📋 Copiar Texto Limpo", width='stretch'):
                    st.code(cleaned_text, language=None)
                    st.info("💡 Use Ctrl+A e Ctrl+C para copiar o texto acima")
            
            with col_b:
                # Download do texto como .txt
                st.download_button(
                    label="💾 Baixar como TXT",
                    data=cleaned_text,
                    file_name=f"{Path(uploaded_file.name).stem}_limpo.txt",
                    mime="text/plain",
                    width='stretch'
                )
            
            with col_c:
                # Gerar e baixar PDF limpo (opcional)
                if st.button("📄 Gerar PDF Limpo", width='stretch'):
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
                                width='stretch'
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