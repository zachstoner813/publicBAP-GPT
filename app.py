import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# Function to convert dictionary to string
def dict_to_string(d):
    items = [f'{k}: {v}' for k, v in d.items()]
    return '{ ' + ', '.join(items) + ' }'

# Function to generate PDF
def generate_pdf(data, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Define a title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 40, "Updated Schedule")

    # Add data to PDF
    y = height - 70
    c.setFont("Helvetica", 10)
    for entry in data:
        entry_str = dict_to_string(entry)
        c.drawString(30, y, entry_str)
        y -= 15  # Move to next line
        if y < 40:  # Check if the current page is full
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40

    c.save()

# Function to extract text from PDFs
def get_pdf_text(pdf_paths):
    text = ""
    for pdf_path in pdf_paths:
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

# Function to split text into chunks
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Function to create vector store from text chunks
def get_vectorstore(text_chunks):
    openai_api_key = st.secrets["openai"]["api_key"]
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

# Function to create conversation chain
def get_conversation_chain(vectorstore):
    openai_api_key = st.secrets["openai"]["api_key"]
    llm = ChatOpenAI(api_key=openai_api_key)
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True
    )
    
    # Add a personality to the bot by setting an initial system message
    initial_message = {
        "role": "system",
        "content": "You are BAP-GPT, an expert on national and chapter-specific policies with a friendly and helpful personality. Always provide clear, concise, and accurate information using only the information in the provided texts to answer questions. If the text does not provide answers to my questions then state -Apologies, I'm not trained on that information just yet-. Never make up any information and never give information on anything harmful or not business appropriate."
    }
    memory.chat_memory.add_user_message(initial_message["content"])
    
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

# Function to handle user input
def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    # Skip the first message (system message)
    skip_first_message = True

    for i, message in enumerate(st.session_state.chat_history):
        if skip_first_message:
            skip_first_message = False
            continue
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)

# Function to process PDFs
def process_pdfs(pdf_paths):
    # get pdf text
    raw_text = get_pdf_text(pdf_paths)

    # get the text chunks
    text_chunks = get_text_chunks(raw_text)

    # create vector store
    vectorstore = get_vectorstore(text_chunks)

    # create conversation chain
    st.session_state.conversation = get_conversation_chain(vectorstore)

def main():
    load_dotenv()
    st.set_page_config(page_title="BAP-GPT", page_icon=":mag:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    # Generate PDF from Google Sheets data
    credentials = st.secrets["google_credentials"]
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(credentials, scopes=scopes)
    client = gspread.authorize(creds)

    # Enter Sheet ID here!!!
    sheet_id = "1NOwujCh8UxQMNFr3jgscZu-AwoJyFHj9Qb7iFxMwHj8"
    sheet = client.open_by_key(sheet_id)
    worksheetSchedule = sheet.get_worksheet(0)
    schedulelist = worksheetSchedule.get_all_records()

    # Ensure the 'documents' directory exists
    if not os.path.exists("documents"):
        os.makedirs("documents")

    # Generate PDF in the 'documents' folder, overwriting any existing file
    output_path = os.path.join("documents", "schedule_list_report.pdf")
    generate_pdf(schedulelist, output_path)

    st.write(f"PDF generated and saved to {output_path}")

    # Automatically process PDFs in 'documents' folder on page load
    documents_folder = 'documents'
    pdf_paths = [os.path.join(documents_folder, filename) for filename in os.listdir(documents_folder) if filename.endswith('.pdf')]
    
    if pdf_paths and st.session_state.conversation is None:
        with st.spinner("Processing"):
            process_pdfs(pdf_paths)

    st.header("Chat with BAP-GPT :mag:")
    user_question = st.text_input("Ask a question about national or chapter specific policies")
    if user_question:
        handle_userinput(user_question)

if __name__ == '__main__':
    main()
