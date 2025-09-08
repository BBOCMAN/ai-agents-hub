from pathlib import Path
from typing import List, Dict, Tuple
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    A class to handle loading, processing, and searching documents
    using vector embeddings with automatic file discovery.
    """
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 50):
        """
        Initialize the DocumentProcessor.
        
        Args:
            chunk_size: Size of text chunks for processing (smaller for better relevance)
            chunk_overlap: Overlap between chunks (smaller to reduce noise)
        """

        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            logger.info("✅ Google embeddings initialized successfully")
        except Exception as e:
            logger.error("❌ Error initializing embeddings. Make sure your GOOGLE_API_KEY is set correctly.")
            logger.error(f"Error details: {e}")
            self.embeddings = None
        
        self.vector_store = None
        self.documents = []
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.file_metadata = {}

    def discover_files(self, docs_dir: str = "docs") -> List[str]:
        """
        Automatically discover all .txt files in docs directory.
        
        Args:
            docs_dir: Directory containing documentation files
            
        Returns:
            List of file paths to load
        """
        file_paths = []
        
        docs_path = Path(docs_dir)
        if docs_path.exists():
            txt_files = list(docs_path.glob("*.txt"))
            file_paths.extend([str(f) for f in txt_files])
            logger.info(f"📄 Found {len(txt_files)} documentation files in {docs_dir}/")
        else:
            logger.warning(f"⚠️ Documentation directory {docs_dir}/ not found")
        
        logger.info(f"📁 Total files discovered: {len(file_paths)}")
        return file_paths

    def _load_text_file(self, path: str) -> Document:
        """Load a text documentation file."""
        try:
            for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode file {path} with any common encoding")
            
            return Document(
                page_content=content,
                metadata={
                    "source": path,
                    "type": "documentation",
                    "filename": Path(path).name,
                    "directory": str(Path(path).parent),
                    "file_size": len(content)
                }
            )
        except Exception as e:
            logger.error(f"❌ Error loading text file {path}: {e}")
            raise

    def load_documents(self, doc_paths: List[str] = None) -> List[Document]:
        """
        Load and process documents from the given paths or auto-discover files.
        
        Args:
            doc_paths: Optional list of specific file paths. If None, auto-discover files.
            
        Returns:
            List of processed document chunks
        """
        if doc_paths is None:
            doc_paths = self.discover_files()
        
        if not doc_paths:
            logger.warning("⚠️ No documents found to load")
            return []

        documents = []
        self.file_metadata = {}

        for path in doc_paths:
            try:
                if path.endswith('.txt'):
                    doc = self._load_text_file(path)
                    documents.append(doc)
                    self.file_metadata[path] = doc.metadata
                    logger.info(f"✅ Loaded: {Path(path).name}")
                else:
                    logger.warning(f"⚠️ Skipping unsupported file type: {path}")
                    continue
                
            except Exception as e:
                logger.error(f"❌ Failed to load {path}: {e}")
                continue

        # Split documents into chunks with better separators for code and documentation
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\n## ",      
                "\n\n### ",       
                "\n\n```",      
                "\n\n",         
                "\n```",        
                "\n",           
                " ",            
                ""              
            ]
        )

        self.documents = text_splitter.split_documents(documents)
        logger.info(f"✅ Processed {len(documents)} files into {len(self.documents)} chunks")
        return self.documents

    def create_vector_store(self, save_path: str = "vector_store") -> FAISS:
        """
        Create a FAISS vector store from the loaded documents.
        
        Args:
            save_path: Path to save the vector store (default: "vector_store")
            
        Returns:
            FAISS vector store
        """
        if not self.documents:
            raise ValueError("No documents loaded. Call load_documents first.")
        if not self.embeddings:
            raise ValueError("Embeddings are not initialized. Check your GOOGLE_API_KEY.")

        try:
            logger.info("🔄 Creating vector store from documents...")
            self.vector_store = FAISS.from_documents(self.documents, self.embeddings)
            
            # Always save to disk for persistence
            self.vector_store.save_local(save_path)
            logger.info(f"💾 Vector store saved to: {save_path}")
            
            logger.info("✅ Vector store created successfully!")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"❌ Error creating vector store: {e}")
            raise

    def load_vector_store(self, load_path: str = "vector_store") -> FAISS:
        """
        Load an existing FAISS vector store from disk.
        
        Args:
            load_path: Path to load the vector store from
            
        Returns:
            FAISS vector store
        """
        if not self.embeddings:
            raise ValueError("Embeddings are not initialized. Check your GOOGLE_API_KEY.")
        
        try:
            logger.info(f"📂 Loading existing vector store from: {load_path}")
            self.vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
            logger.info("✅ Vector store loaded successfully!")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"❌ Error loading vector store: {e}")
            raise

    def get_or_create_vector_store(self, save_path: str = "vector_store") -> FAISS:
        """
        Load existing vector store if available, otherwise create a new one.
        
        Args:
            save_path: Path for the vector store
            
        Returns:
            FAISS vector store
        """
        vector_store_path = Path(save_path)
        
        # Check if vector store files exist
        if (vector_store_path / "index.faiss").exists() and (vector_store_path / "index.pkl").exists():
            try:
                return self.load_vector_store(save_path)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load existing vector store: {e}")
                logger.info("🔄 Creating new vector store...")
        
        return self.create_vector_store(save_path)

    def search_relevant_docs(self, query: str, k: int = 4, filter_by_type: str = None) -> Tuple[str, List[Document]]:
        """
        Search for relevant documents based on a query.
        
        Args:
            query: Search query
            k: Number of documents to return
            filter_by_type: Optional filter by document type ('documentation', 'code')
            
        Returns:
            Tuple of (formatted_context, relevant_documents)
        """
        if not self.vector_store:
            raise ValueError("Vector store not created. Call create_vector_store first.")

        try:
            # Perform similarity search - use raw results for better coverage
            relevant_docs = self.vector_store.similarity_search(query, k=k)
            
            # Apply type filtering if specified
            if filter_by_type:
                relevant_docs = [
                    doc for doc in relevant_docs 
                    if doc.metadata.get('type') == filter_by_type
                ]
            
            # Format context
            context = self._format_search_results(query, relevant_docs)
            
            logger.info(f"🔍 Search completed: Found {len(relevant_docs)} relevant documents for '{query}'")
            return context, relevant_docs
            
        except Exception as e:
            logger.error(f"❌ Error during search: {e}")
            raise

    def _format_search_results(self, query: str, docs: List[Document]) -> str:
        """Format search results into a readable context string."""
        if not docs:
            return f"\n\n---NO RELEVANT DOCUMENTATION FOUND---\nQuery: {query}\n"
        
        context = f"\n\n---RELEVANT DOCUMENTATION FOR: '{query}'---\n"
        context += f"Found {len(docs)} relevant document(s)\n"
        context += "="*60 + "\n"
        
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            doc_type = doc.metadata.get('type', 'unknown')
            filename = doc.metadata.get('filename', 'Unknown')
            
            context += f"\n📄 Document {i} - {filename}\n"
            context += f"   Type: {doc_type.title()}\n"
            context += f"   Source: {source}\n"
            context += "   Content Preview:\n"
            context += "-" * 40 + "\n"
            # Show a more focused preview
            content_preview = doc.page_content[:300].strip()
            if len(doc.page_content) > 300:
                content_preview += "..."
            context += content_preview
            context += "\n" + "="*60 + "\n"
        
        return context

    def get_document_stats(self) -> Dict:
        """Get statistics about loaded documents."""
        if not self.documents:
            return {"message": "No documents loaded"}
        
        stats = {
            "total_chunks": len(self.documents),
            "total_files": len(self.file_metadata),
            "file_types": {},
            "total_content_length": 0,
            "files_by_directory": {}
        }
        
        # Analyze document types and content
        for doc in self.documents:
            doc_type = doc.metadata.get('type', 'unknown')
            stats["file_types"][doc_type] = stats["file_types"].get(doc_type, 0) + 1
            stats["total_content_length"] += len(doc.page_content)
            
            directory = doc.metadata.get('directory', 'unknown')
            stats["files_by_directory"][directory] = stats["files_by_directory"].get(directory, 0) + 1
        
        stats["average_chunk_size"] = stats["total_content_length"] / len(self.documents)
        
        return stats

if __name__ == "__main__":
    """Test the DocumentProcessor with enhanced documentation files."""
    print("🚀 Starting Document Processor Test...")
    
    processor = DocumentProcessor(
        chunk_size=600,
        chunk_overlap=50
    )

    if processor.embeddings:
        print("\n📂 Loading documentation files...")
        
        # Load all available documents
        docs = processor.load_documents()
        
        if docs:
            print(f"✅ Successfully loaded {len(docs)} document chunks from {len(processor.file_metadata)} files")
            
            # Create or load vector store (automatically saves/loads from disk)
            print("\n🔄 Creating/Loading vector store...")
            vector_store = processor.get_or_create_vector_store("vector_store")
            
            # Display document statistics
            print("\n📊 Document Statistics:")
            stats = processor.get_document_stats()
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {sub_value}")
                else:
                    print(f"  {key}: {value}")
            
            # Test search functionality
            test_queries = [
                "how to read a CSV file with pandas",
                "create visualizations with matplotlib",
                "make HTTP requests with error handling", 
                "train a machine learning model with scikit-learn",
                "python class inheritance and polymorphism",
                "async web scraping with aiohttp"
            ]
            
            print("\n" + "="*60)
            print("🔍 TESTING DOCUMENT SEARCH FUNCTIONALITY")
            print("="*60)
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n📋 Test {i}: Searching for '{query}'")
                try:
                    context, results = processor.search_relevant_docs(query, k=3)
                    print(f"✅ Found {len(results)} relevant documents")
                    
                    for j, doc in enumerate(results, 1):
                        filename = doc.metadata.get('filename', 'Unknown')
                        doc_type = doc.metadata.get('type', 'unknown')
                        
                        content = doc.page_content.lower()
                        query_words = query.lower().split()
                        snippet = ""
                        
                        for line in doc.page_content.split('\n'):
                            if any(word in line.lower() for word in query_words if len(word) > 3):
                                snippet = line.strip()[:100]
                                break
                        
                        if not snippet:
                            snippet = doc.page_content[:100].replace('\n', ' ')
                            
                        print(f"   {j}. {filename} ({doc_type})")
                        print(f"      📝 {snippet}...")
                        
                except Exception as e:
                    print(f"❌ Error during search: {e}")
                print("-" * 50)
            
            print("\n🎉 Document processor test completed successfully!")
            print("\n💡 Usage Example:")
            print("```python")
            print("from document_loader import DocumentProcessor")
            print("processor = DocumentProcessor()")
            print("docs = processor.load_documents()")
            print("vector_store = processor.create_vector_store()")
            print("context, results = processor.search_relevant_docs('your query here')")
            print("```")
        else:
            print("❌ No documents were loaded. Please check if documentation files exist.")
    else:
        print("\nSkipping tests because embeddings could not be initialized.")
        print("Please ensure your GOOGLE_API_KEY environment variable is set.")
        print("\nTo set up your API key:")
        print("1. Get your API key from Google AI Studio (https://aistudio.google.com/)")
        print("2. Set environment variable: GOOGLE_API_KEY=your_api_key_here")
        print("3. Restart the script")
