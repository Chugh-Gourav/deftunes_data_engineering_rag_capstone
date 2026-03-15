import os
import glob
import yaml
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Configure your Gemini API Key in the environment before running
# export GOOGLE_API_KEY="your-api-key"

def load_odcs_contracts(directory: str) -> list[Document]:
    """
    PM CONTEXT: DATA PREPARATION LAYER
    Transforms raw YAML contracts into AI-readable 'Knowledge Chunks'.
    
    Why this matters: LLMs perform best when context is highly structured. 
    By explicitly parsing YAML fields, we increase the 'Signal-to-Noise Ratio' 
    compared to just sending raw text files.
    """
    documents = []
    yaml_files = glob.glob(os.path.join(directory, "*.yaml"))
    
    for file_path in yaml_files:
        with open(file_path, "r") as f:
            try:
                data = yaml.safe_load(f)
                
                # Extract high level info
                title = data.get("info", {}).get("title", "Unknown Title")
                desc = data.get("info", {}).get("description", "")
                owner = data.get("info", {}).get("owner", "Unknown Owner")
                version = data.get("info", {}).get("version", "")
                
                # Document 1: Overview of the Data Contract
                overview_text = f"Data Contract: {title}\nVersion: {version}\nDescription: {desc}\nOwner: {owner}\n"
                
                if "servers" in data:
                    for server_name, server_info in data["servers"].items():
                        overview_text += f"Server: {server_name} | Type: {server_info.get('type')} | Project: {server_info.get('project')} | Dataset: {server_info.get('dataset')}\n"
                
                if "servicelevels" in data:
                    slas = data["servicelevels"]
                    sla_text = f"SLA: Availability: {slas.get('availability', {}).get('percentage')}% | "
                    sla_text += f"Freshness: Max delay of {slas.get('freshness', {}).get('maxDelay')} based on field {slas.get('freshness', {}).get('timestampField')}."
                    overview_text += sla_text
                    
                documents.append(Document(page_content=overview_text, metadata={"source": os.path.basename(file_path), "type": "overview"}))
                
                # Document(s) 2: Model-specific information
                models = data.get("models", {})
                for model_name, model_details in models.items():
                    model_desc = model_details.get("description", "")
                    model_type = model_details.get("type", "table")
                    fields = model_details.get("fields", {})
                    
                    schema_text = f"Table/Model Name: {model_name}\nType: {model_type}\nDescription: {model_desc}\nSchema:\n"
                    for field_name, field_info in fields.items():
                        req = "Required" if field_info.get("required") else "Optional"
                        pk = " [PRIMARY KEY]" if field_info.get("primary") else ""
                        field_quality = field_info.get("quality", [])
                        quality_str = ""
                        if field_quality:
                            quality_str = f" [Quality: {', '.join(str(q) for q in field_quality)}]"
                        schema_text += f"- {field_name} ({field_info.get('type')}): {field_info.get('description')} [{req}]{pk}{quality_str}\n"
                        
                    documents.append(Document(page_content=schema_text, metadata={"source": os.path.basename(file_path), "type": "schema", "model": model_name}))
                
                # Document 3: Quality rules (Table-level + Field-level)
                quality_text = f"Quality Rules for {title}:\n"
                has_rules = False
                
                # Global rules
                if "quality" in data:
                    rules = data["quality"].get("rules", [])
                    for rule in rules:
                        quality_text += f"- [Global] {rule}\n"
                        has_rules = True
                
                # Scour fields for rules
                for model_name, model_details in models.items():
                    fields = model_details.get("fields", {})
                    for field_name, field_info in fields.items():
                        if "quality" in field_info:
                            field_rules = field_info.get("quality", [])
                            for f_rule in field_rules:
                                quality_text += f"- [{model_name}.{field_name}] {f_rule}\n"
                                has_rules = True
                
                if has_rules:
                    documents.append(Document(page_content=quality_text, metadata={"source": os.path.basename(file_path), "type": "quality"}))
                    
            except yaml.YAMLError as exc:
                print(f"Error parsing YAML file {file_path}: {exc}")
                
    return documents

def load_dbt_schemas(directory: str) -> list[Document]:
    """Reads dbt schema.yml files and returns LangChain Documents."""
    documents = []
    yaml_files = glob.glob(os.path.join(directory, "**", "schema.yml"), recursive=True)
    
    for file_path in yaml_files:
        with open(file_path, "r") as f:
            try:
                data = yaml.safe_load(f)
                models = data.get("models", [])
                
                for model in models:
                    name = model.get("name", "")
                    desc = model.get("description", "")
                    columns = model.get("columns", [])
                    
                    schema_text = f"dbt Model: {name}\nDescription: {desc}\nColumns:\n"
                    for col in columns:
                        col_desc = col.get("description", "")
                        tests = col.get("data_tests", [])
                        test_str = f" [Tests: {', '.join(str(t) for t in tests)}]" if tests else ""
                        schema_text += f"- {col.get('name')}: {col_desc}{test_str}\n"
                    
                    documents.append(Document(page_content=schema_text, metadata={"source": os.path.basename(file_path), "type": "dbt_schema", "model": name}))
                    
            except yaml.YAMLError as exc:
                print(f"Error parsing dbt schema {file_path}: {exc}")
    
    return documents

def build_vector_db():
    """
    PM CONTEXT: THE KNOWLEDGE INFRASTRUCTURE
    This function creates our persistent 'Long-Term Memory' (ChromaDB).
    
    Trade-off: We use Local ChromaDB for zero-cost and sub-100ms latency.
    For production scale, a PM would evaluate enterprise alternatives like 
    Pinecone or BigQuery Vector Search for high-concurrency access.
    """
    print("Loading ODCS data contracts...")
    contracts_path = os.path.join("..", "odcs_contracts")
    docs = load_odcs_contracts(contracts_path)
    print(f"  → {len(docs)} chunks from ODCS contracts")
    
    print("Loading dbt schema files...")
    dbt_path = os.path.join("..", "dbt_modeling", "models")
    dbt_docs = load_dbt_schemas(dbt_path)
    docs.extend(dbt_docs)
    print(f"  → {len(dbt_docs)} chunks from dbt schemas")
    
    print(f"Total: {len(docs)} document chunks")
    
    print("Initializing Gemini Embeddings (requires GOOGLE_API_KEY in env)...")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        
        # Remove old DB if it exists
        import shutil
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
            
        print("Building ChromaDB locally at ./chroma_db...")
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        print(f"Vector database built successfully with {len(docs)} chunks!")
    except Exception as e:
        print(f"Failed to build vector DB: {e}\nPlease ensure GOOGLE_API_KEY is exported.")

if __name__ == "__main__":
    build_vector_db()
