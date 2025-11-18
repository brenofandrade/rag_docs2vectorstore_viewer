# 🧹 PDF Cleaner & Visualizer

Sistema completo para limpar, visualizar e preparar PDFs para Vector Stores.

## 🎯 Funcionalidades

### ✨ Limpezas Automáticas
- ✂️ Remove quebras de linha desnecessárias
- 🧹 Normaliza espaçamentos múltiplos
- 🚫 Remove caracteres especiais
- 📏 Corrige espaçamento em pontuação
- 🗑️ Remove cabeçalhos e rodapés
- 🔢 Remove números de página isolados
- 📐 Normaliza quebras de linha excessivas

### 👁️ Visualização
- 📊 Comparação lado a lado (PDF original vs texto limpo)
- 📈 Métricas de limpeza em tempo real
- 🔍 Preview detalhado dos chunks para Vector Store

### 💾 Exportação
- 📄 Download como TXT
- 📋 Cópia fácil do texto
- 🎨 Geração opcional de PDF limpo

## 🚀 Instalação

```bash
# Clone ou baixe os arquivos
# Instale as dependências
pip install -r requirements.txt
```

## 📖 Como Usar

### 1️⃣ Limpar e Visualizar PDF

```bash
streamlit run pdf_cleaner_app.py
```

Depois:
1. Faça upload do seu PDF
2. Visualize o original e o processado lado a lado
3. Analise as métricas de limpeza
4. Baixe como TXT ou gere um novo PDF

### 2️⃣ Integrar com Vector Store

```python
from pdf_cleaner_app import PDFCleaner
from vector_store_integration import VectorStoreIntegration

# 1. Limpar o PDF
cleaner = PDFCleaner()

# Extrair texto
with open("seu_arquivo.pdf", "rb") as f:
    original_text = cleaner.extract_text_from_pdf(f)

# Limpar texto
cleaned_text = cleaner.clean_text(original_text)

# 2. Criar Vector Store
integration = VectorStoreIntegration()

# Criar documentos com chunks
documents = integration.process_cleaned_text(
    cleaned_text,
    metadata={"source": "seu_arquivo.pdf"}
)

# Criar Vector Store
vectorstore = integration.create_vector_store(documents)

# 3. Usar para busca
results = vectorstore.similarity_search("sua query aqui", k=5)
```

## 🏗️ Arquitetura

```
┌─────────────────┐
│   PDF Original  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extração Texto │  (pypdf)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Limpezas     │  (PDFCleaner)
│                 │
│ • Quebras linha │
│ • Espaçamentos  │
│ • Cabeçalhos    │
│ • Caracteres    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Visualização   │  (Streamlit)
│                 │
│ Original | Limpo│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Vector Store   │  (LangChain + FAISS)
│                 │
│ • Text Splitter │
│ • Embeddings    │
│ • Indexação     │
└─────────────────┘
```

## 🧠 Analogia: Linha de Produção

Imagine uma **fábrica de processamento de documentos**:

1. **🏭 Entrada**: PDF "bruto" chega na esteira transportadora
2. **🔍 Inspeção Visual**: Você vê o documento original em uma tela de controle
3. **🧹 Estação de Limpeza**: Texto passa por 7 "filtros" diferentes:
   - Filtro 1: Remove quebras de linha ruins
   - Filtro 2: Normaliza espaços
   - Filtro 3-7: Outras limpezas...
4. **📺 Controle de Qualidade**: Você vê o resultado limpo ao lado do original
5. **📦 Embalagem**: Texto é dividido em "caixas" (chunks) do tamanho certo
6. **🚚 Distribuição**: Chunks vão para o armazém (Vector Store)

## 📊 Exemplo Real

### Antes da Limpeza (Original)
```
RELATÓRIO    ANUAL


Capítulo    1  -  Introdução




Este   é  um  relatório      com
muitos      problemas    de
formatação.

@#$%  Caracteres    inválidos @#$%

                                    Página 1
```

### Depois da Limpeza
```
RELATÓRIO ANUAL

Capítulo 1 - Introdução

Este é um relatório com muitos problemas de formatação.

Caracteres inválidos
```

**Resultado**:
- 📉 Redução de ~35% no tamanho
- ✅ Texto estruturado e limpo
- 🎯 Pronto para embeddings

## 🔧 Personalização

### Ajustar Limpezas

Edite a classe `PDFCleaner` no arquivo `pdf_cleaner_app.py`:

```python
@staticmethod
def clean_text(text):
    # Adicione suas próprias regras aqui
    
    # Exemplo: remover URLs
    text = re.sub(r'http\S+', '', text)
    
    # Exemplo: remover emails
    text = re.sub(r'\S+@\S+', '', text)
    
    return text
```

### Ajustar Chunks

Edite `VectorStoreIntegration` no arquivo `vector_store_integration.py`:

```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # Tamanho menor
    chunk_overlap=100,   # Overlap menor
    # ...
)
```

## 🎓 Conceitos Importantes

### 🧩 Chunks (Pedaços de Texto)

**Por que dividir?**
- Vector Stores funcionam melhor com pedaços menores
- Buscas ficam mais precisas
- Economiza processamento

**Como funciona?**
```
Texto grande (10.000 caracteres)
        ↓
Dividir em chunks de 1.000
        ↓
10 chunks indexados separadamente
        ↓
Busca retorna os chunks mais relevantes
```

### 🎯 Embeddings

**O que são?**
Transformam texto em números (vetores) que representam o significado.

**Analogia**:
- Texto = Endereço completo
- Embedding = Coordenadas GPS
- Vector Store = Mapa com todos os pontos

**Por que limpar antes?**
Texto limpo → Embeddings melhores → Buscas mais precisas

## 🤝 Contribuindo

Sinta-se à vontade para:
- 🐛 Reportar bugs
- 💡 Sugerir melhorias
- 🔧 Adicionar novas limpezas
- 📚 Melhorar documentação

## 📝 Licença

MIT License - Use como quiser!

## 🆘 Problemas Comuns

### PDF não abre
- ✅ Verifique se o arquivo não está corrompido
- ✅ Tente converter o PDF para uma versão mais nova

### Texto mal extraído
- ✅ PDFs escaneados precisam de OCR primeiro
- ✅ Use `pdfplumber` em vez de `pypdf` para PDFs complexos

### Vector Store lento
- ✅ Reduza o `chunk_size`
- ✅ Use embeddings mais leves
- ✅ Considere usar GPU para embeddings

## 📞 Suporte

Dúvidas? Entre em contato ou abra uma issue!

---

**Desenvolvido com ❤️ para facilitar o processamento de PDFs**