import streamlit as st
from streamlit_option_menu import option_menu
import time
import os
from langchain.tools.base import StructuredTool
from langchain_community.document_loaders import PyPDFLoader
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents import initialize_agent, AgentType
from fin_utilities.data_extractor import extract_raw_data, extract_transaction_data#, DetailedStreamlitCallbackHandler
from fin_agents.data_extractor_agent import chat_bank, chat
from fin_utilities.db_connection import UserDocumentDB
# Streamlit UI Callback
from fin_utilities.promptSchema import kyc_system_prompt, loan_system_prompt, kyc_human, kyc_human1, bank_human, bank_system_message



 # Set the page layout to wide
st.set_page_config(layout="wide")

def stream_data(str):
        for word in str.split(" "):
            yield word + " "
            time.sleep(0.1)

if 'kyc_message' not in st.session_state:
        st.session_state.kyc_message = False
    
if 'kyc_m' not in st.session_state:
    st.session_state.kyc_m = ""

if 'kyc_b' not in st.session_state:
    st.session_state.kyc_b = False

if 'kyc_i' not in st.session_state:
    st.session_state.kyc_i = False

if 'transaction_data' not in st.session_state:
    st.session_state.transaction_data = []

if 'kyc_t' not in st.session_state:
    st.session_state.kyc_t = False

if 'bank_raw' not in st.session_state:
    st.session_state.bank_raw = None

if 'db' not in st.session_state:
    st.session_state.db = UserDocumentDB()


def gather_data(doc_type: str) -> dict:
    """
    Extracts data from various financial documents based on document type.
    Uses global file objects (pan_file, aadhar_file, itr_file, form16_file, bank_file)
    that are set through Streamlit's file_uploader.

    Args:
        doc_type (str): Type of document to process. Valid values:
            - 'pan': PAN card
            - 'aadhar': Aadhar card
            - 'itr': Income Tax Return
            - 'form16': Form 16
            - 'bankstatement': Bank statement (when bank holder name and address is required.)

    Returns:
        dict: Extracted data in JSON format specific to each document type, or empty dict if file not present
    """
    try:
        if doc_type == 'pan':
            pan_info = st.session_state.db.get_user(st.session_state.user_id, {"pan": 1, "_id": 0})
            return pan_info['pan']
        elif doc_type == 'aadhar':
            aadhar_info = st.session_state.db.get_user(st.session_state.user_id, {"aadhar": 1, "_id": 0})
            return aadhar_info['aadhar']
        elif doc_type == 'itr':
            itr_info = st.session_state.db.get_user(st.session_state.user_id, {"itr": 1, "_id": 0})
            return itr_info['itr']
        elif doc_type == 'form16':
            form16_info = st.session_state.db.get_user(st.session_state.user_id, {"form16": 1, "_id": 0})
            return form16_info['form16']
        elif doc_type == 'bankstatement':
            bank_info = st.session_state.db.get_user(st.session_state.user_id, {"bankstatement": 1, "_id": 0})
            return bank_info['bankstatement']
        else:
            st.warning(f"Document not available: {doc_type}")
            return {}
            
    except ValueError as e:
        st.error(f"Error processing {doc_type}: {str(e)}")
        return {}


def gather_bank_transaction(doc_type: str) -> dict:
    """
    Extracts bank transaction data from the uploaded bank statement.
    Args:
        doc_type (str): Should be 'transaction_data'.
    Returns:
        dict: Extracted transaction data in JSON format or empty dict if file not present.
    """
    try:
        if doc_type == 'transaction_data' and st.session_state.bank is not None:
            return extract_transaction_data(st.session_state.bank)
        else:
            st.warning("Bank statement not available for transaction data.")
            return {}
    except ValueError as e:
        st.error(f"Error processing transaction data: {str(e)}")
        return {}



#Preparing the agent's tool
data_extraction_tool = StructuredTool.from_function(gather_data)
income_transaction_tool = StructuredTool.from_function(gather_bank_transaction)

tools = [data_extraction_tool, income_transaction_tool]

#Initialize Agents
agent_chain = initialize_agent(tools, 
                            chat,
                            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                            verbose=True)

kyc_check_message = [
                        {
                            "role": "system",
                            "content": kyc_system_prompt.content
                        },
                        {
                            "role": "user",
                            "content": kyc_human.content
                        }
                    ]

income_check_message = [
                        {
                            "role": "system",
                            "content": loan_system_prompt.content
                        },
                
                        {
                            "role": "user",
                            "content": kyc_human1.content
                        }
                    ]


bank_check_message = [
                        {
                            "role": "system",
                            "content": bank_system_message.content
                        },
                        {
                            "role": "system",
                            "content": bank_human.content
                        }
]

def kyc_check():

    with st.chat_message("assistant"):
        st.write('Welcome! Pls upload the following documents to proceed:\n1. PAN Card\n2. Aadhar Card\n3. Bank Statement')
    
        col1, col2, col3 = st.columns([1,1,1])
        # PAN Card Section
        pan = col1.file_uploader("Upload PAN Card Image", 
            type=["jpg", "jpeg", "png", "pdf"], 
            key="pan1")

        # Aadhar Card Section
        aadhar = col2.file_uploader("Upload Aadhar Card Image", 
            type=["jpg", "jpeg", "png", "pdf"], 
            key="aadhar1")
        
        # Bank Statement Section
        bank = col3.file_uploader("Upload Bank Statement", 
            type=["pdf"], 
            key="bank1")
        if bank:
            st.session_state.bank_raw = bank
    
        if st.button('Submit & Analyze'):
            if pan and aadhar and bank:
                st.session_state.kyc_b = True
                p = extract_raw_data(pan, 'pan')
                a = extract_raw_data(aadhar, 'aadhar')
                b = extract_raw_data(bank, 'bankstatement')
                user_data = {
                    "pan": p,
                    "aadhar": a,
                    "bankstatement": b
                }              
                # Create user in the database
                if st.session_state.db.get_user(st.session_state.user_id) is None:
                    st.session_state.db.create_user(st.session_state.user_id, user_data)
                else:
                    st.session_state.db.update_document_section(st.session_state.user_id, "pan", p)
                    st.session_state.db.update_document_section(st.session_state.user_id, "aadhar", a)
                    st.session_state.db.update_document_section(st.session_state.user_id, "bankstatement", b)
                st.success('Data Saved in DB Successfully!')
            else:
                st.warning("Please upload your PAN and AADHAAR for KYC Verification!")

    if st.session_state.kyc_b:
        with st.chat_message('human'):          
                        
            callback_handler1 = StreamlitCallbackHandler(st.container())
            
            response = agent_chain(kyc_check_message,callbacks=[callback_handler1])
            
            st.write(stream_data(response["output"]))
            st.session_state.kyc_m = response["output"]
            if "KYC Successful" in response["output"]:
                st.success("KYC verification successful!")
                st.session_state.kyc_message = True
                st.session_state.kyc_b = False
                #st.session_state.KYC_doc = True

            else:
                st.error("KYC verification failed. Please re-upload corrected PAN and Aadhaar documents.")
                st.session_state.kyc_b = False


def income_check():

    with st.chat_message("assistant"):
        st.write('Congrats! Your KYC verification was Successful!\n Pls upload the following documents to proceed with income and employment verification:\n1. Income Tax Return file\n2. Form 16 (provided by the employer)')
        
        col1, col2 = st.columns([1,1])
        # ITR Card Section
        itr = col1.file_uploader("Upload ITR", 
            type=["jpg", "jpeg", "png", "pdf"], 
            key="itr1")

        # Form 16 Section
        form16 = col2.file_uploader("Upload Form 16", 
            type=["jpg", "jpeg", "png", "pdf"], 
            key="form161")
    
        if st.button('Submit & Analyze'):
            if itr and form16:
                form16_data = extract_raw_data(form16, 'form16')
                itr_data = extract_raw_data(itr, 'itr')
                st.session_state.db.update_document_section(st.session_state.user_id, "form16", form16_data)
                st.session_state.db.update_document_section(st.session_state.user_id, "itr", itr_data)
                st.success('Data Saved in DB Successfully!')
                st.session_state.kyc_i = True
            else:
                st.warning("Please upload your PAN and AADHAAR for KYC Verification!")

    if st.session_state.kyc_i:
        with st.chat_message('human'):

            st.session_state.kyc_message = False        
                        
            callback_handler = StreamlitCallbackHandler(st.container())
            
            response1 = agent_chain(income_check_message,callbacks=[callback_handler])
            
            st.write(stream_data(response1["output"]))

            st.session_state.kyc_i = False
            #st.session_state.kyc_m = response["output"]
            # if "KYC Successful" in response["output"]:
            #     st.success("Income and Employment verification successful!")
                #st.session_state.kyc_message = True



def salary_check():
    with st.chat_message('assistant'):
        st.write('Congrats! Your ITR and Form 16 is verified! We are verifying your salary credit now.')
        if st.button('Analyze'):
            # callback_handler2 = StreamlitCallbackHandler(st.container())
            
            # response2 = agent_chain(bank_check_message,callbacks=[callback_handler2])
            
            # st.write(stream_data(response2["output"]))
        

            # Define your query
            user_query = """from the given data, will you find transaction from employer if yes then print date, employer name and transaction amount.
                            Note: if you find more than one transaction then then show all.
                         """
            
            save_dir = "temp_files"  # or any directory path you prefer
            os.makedirs(save_dir, exist_ok=True)

            # Save the PDF file from session state
            pdf_path = os.path.join(save_dir, "bank_statement.pdf")
            with open(pdf_path, "wb") as f:
                f.write(st.session_state.bank.read())

            loader = PyPDFLoader(pdf_path)
            pages = []
            for page in loader.load():
                pages.append(page)
            
            # Create a template for the prompt
            prompt_template = f"""
            Please analyze the following page content and answer this query: {user_query}

            Page Content:
            {{page_content}}

            Please provide your analysis based on the above content.
            """

            # Process each page
            for page in pages:
                # Create the full prompt with the page content
                current_prompt = prompt_template.format(page_content=page.page_content)
                
                # Get response from ChatGPT
                response = chat_bank.invoke([{"role": "user", "content": current_prompt}])
                #breakpoint()
                # Store response with page number
                st.session_state.transaction_data.append({
                    "page_number": page.metadata.get('page', 'Unknown'),
                    "response": response.content
                })

            st.session_state.kyc_t = True
    if st.session_state.kyc_t:
        with st.chat_message('human'):
            # Print results
            for result in st.session_state.transaction_data:
                st.write(stream_data((f"\nPage {result['page_number']+1}:")))
                st.write(stream_data((result['response'])))
                st.write(("-" * 50))

            st.session_state.transaction_data = []
            st.session_state.kyc_t = False


@st.dialog("Enter your Email ID")
def email_input():
    email = st.text_input("Enter your Email ID")
    if st.button("Submit"):
        st.session_state.user_id = email
        st.rerun()

def main():

    if 'user_id' not in st.session_state:
        email_input()

    st.title("Smart Document Analyzer")
    #with st.sidebar:
    selected_main = option_menu(
        menu_title="P1 - L1 Verification",  # Title of the sidebar
        options=["KYC Verification", "ITR & Form 16 Verification", "Income & Employment Verification"],  # Options
        icons=["clipboard-data-fill", "database-fill-check"],  # Icons from https://icons.getbootstrap.com/
        menu_icon="",
        orientation="horizontal",  # The icon for the menu title
        default_index=0,  # Default selected option
    )

    if selected_main == "KYC Verification":
        kyc_check()
    elif selected_main == "ITR & Form 16 Verification":
        if st.session_state.kyc_message:
            income_check()
        else:
            st.warning("First verify your KYC!")
    elif selected_main == "Income & Employment Verification":
        salary_check()


if __name__ == "__main__":
    main()

