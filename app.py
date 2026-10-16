import io
from openai import AzureOpenAI
import pypdf
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E ESTILIZAÇÃO (CSS)
# ==========================================
st.set_page_config(
    page_title="ChatBot RAG - Microsoft Foundry",
    page_icon="🤖",
    layout="centered",
)

# Estilização customizada para criar uma borda profissional ao redor do aplicativo
st.markdown(
    """
    <style>
    /* Estilização geral do container principal */
    .stMainBlockContainer {
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 30px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    
    /* Personalização do cabeçalho */
    h1 {
        color: #1e293b;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Ajustes na barra lateral */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# CONFIGURAÇÃO DA API (MICROSOFT FOUNDRY)
# ==========================================
API_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
DEPLOYMENT_NAME = "gpt-4.1-mini"
ENDPOINT = "https://marcelomaffeis-05082026-resource.services.ai.azure.com/"

# Inicialização do cliente Azure OpenAI
try:
  client = AzureOpenAI(
      api_key=API_KEY, api_version="2024-02-01", azure_endpoint=ENDPOINT
  )
except Exception as e:
  st.error(f"Erro ao inicializar o cliente da API: {e}")

# ==========================================
# INTERFACE DA BARRA LATERAL (UPLOAD DE ARQUIVOS)
# ==========================================
st.sidebar.title("📁 Base de Conhecimento (RAG)")
st.sidebar.markdown(
    "Envie um arquivo PDF ou TXT para contextualizar as respostas do assistente."
)

uploaded_file = st.sidebar.file_uploader(
    "Escolha um arquivo", type=["pdf", "txt"]
)

file_text = ""
if uploaded_file is not None:
  try:
    if uploaded_file.type == "application/pdf":
      reader = pypdf.PdfReader(uploaded_file)
      for page_num, page in enumerate(reader.pages):
        extracted = page.extract_text()
        if extracted:
          file_text += extracted + "\n"
    elif uploaded_file.type == "text/plain":
      file_text = uploaded_file.getvalue().decode("utf-8")

    st.sidebar.success(
        f"Arquivo carregado! ({len(file_text)} caracteres extraídos)"
    )
  except Exception as e:
    st.sidebar.error(f"Erro ao processar o arquivo: {e}")

# Botão para limpar histórico
if st.sidebar.button("🧹 Limpar Histórico do Chat"):
  st.session_state.messages = []
  st.rerun()

# ==========================================
# INTERFACE PRINCIPAL E LÓGICA DE CHAT
# ==========================================
st.title("🤖 Assistente Inteligente com RAG")
st.markdown(
    "Faça perguntas gerais ou baseadas no documento enviado na barra"
    " lateral."
)
st.divider()

# Inicialização do histórico no session_state
if "messages" not in st.session_state:
  st.session_state.messages = []

# Exibição do histórico de mensagens
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Captura da entrada do usuário
if prompt := st.chat_input("Digite sua dúvida aqui..."):
  # Adiciona mensagem do usuário ao histórico
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  # Montagem do Contexto RAG para o modelo
  api_messages = []

  if file_text.strip():
    system_prompt = (
        "Você é um assistente de IA especialista. "
        "Utilize o contexto fornecido abaixo extraído de um documento do usuário "
        "para responder à pergunta. Se a resposta não estiver explicitamente no "
        "documento, utilize seu conhecimento geral, mas avise que a informação "
        "veio de fontes externas ao documento.\n\n"
        f"--- CONTEÚDO DO DOCUMENTO ---\n{file_text}\n-----------------------------"
    )
    api_messages.append({"role": "system", "content": system_prompt})
  else:
    api_messages.append({
        "role": "system",
        "content": "Você é um assistente virtual prestativo e educado.",
    })

  # Adiciona o histórico da conversa
  for m in st.session_state.messages:
    api_messages.append({"role": m["role"], "content": m["content"]})

  # Chamada à API da Microsoft Foundry (Azure OpenAI)
  with st.chat_message("assistant"):
    with st.spinner("Gerando resposta..."):
      try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME, messages=api_messages, temperature=0.7
        )
        answer = response.choices[0].message.content
        st.markdown(answer)

        # Salva a resposta no histórico
        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
      except Exception as e:
        error_message = (
            f"Ocorreu um erro ao comunicar com a API do Microsoft Foundry: {e}"
        )
        st.error(error_message)
        st.session_state.messages.append(
            {"role": "assistant", "content": error_message}
        )
