import os
import uuid
import openai
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

class QdrantVectorStore:
    def __init__(self):
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME")
        self.qdrant_client = self._get_qdrant_client()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def _get_qdrant_client(self):
        """Initialize and maintain Qdrant connection"""
        try:
            client = QdrantClient(url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))
            
            if not client.collection_exists(self.collection_name):
                client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                    shard_number=2
                )
            
            return client
        except Exception as e:
            print(f"Error connecting to Qdrant: {str(e)}")
            return None

    def _generate_embeddings(self, texts):
        """Generate OpenAI embeddings for given texts"""
        try:
            openai.api_key = self.openai_api_key
            response = openai.embeddings.create(input=texts, model="text-embedding-3-small")
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return []

    def _load_pdf_text(self, pdf_path):
        """Load and split PDF text into pages"""
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            return [page.page_content for page in pages]
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            return []

    def put_vector_db(self, user_id, pdf_path):
        """Process a PDF, generate embeddings, and store them in Qdrant, replacing old entries"""
        try:
            if self.qdrant_client is None:
                print("Qdrant client initialization failed.")
                return

            # Ensure the collection exists
            if not self.qdrant_client.collection_exists(self.collection_name):
                print(f"Collection {self.collection_name} does not exist. Creating it...")
                self.qdrant_client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )

            # Check if user exists and delete old entries
            user_filter = Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))])
            existing_vectors = self.qdrant_client.scroll(
                collection_name=self.collection_name, scroll_filter=user_filter, limit=1
            )[0]

            if existing_vectors:
                self.qdrant_client.delete(collection_name=self.collection_name, points_selector=user_filter)
                print(f"Deleted existing vectors for user: {user_id}")

            # Process new PDF text
            text_chunks = self._load_pdf_text(pdf_path)
            if not text_chunks:
                print(f"No text found in PDF: {pdf_path}")
                return

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=350, chunk_overlap=50)
            split_docs = text_splitter.create_documents(text_chunks)
            text_chunks = [doc.page_content for doc in split_docs]
            print(text_chunks)

            # Generate embeddings
            embeddings = self._generate_embeddings(text_chunks)
            if not embeddings or len(embeddings) != len(text_chunks):
                print("Embedding generation failed. Check OpenAI API or embedding function.")
                return

            # Insert vectors in batches
            BATCH_SIZE = 50
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={"user_id": user_id, "text": chunk, "chunk_id": idx}
                )
                for idx, (chunk, embedding) in enumerate(zip(text_chunks, embeddings))
            ]

            for i in range(0, len(points), BATCH_SIZE):
                batch = points[i:i+BATCH_SIZE]
                self.qdrant_client.upsert(collection_name=self.collection_name, points=batch)
                print(f"Inserted {len(batch)} vectors for user: {user_id}")

            print(f"Successfully uploaded {len(points)} vectors for user: {user_id}")

        except Exception as e:
            print(f"Error processing {pdf_path} for user {user_id}: {str(e)}")


    def get_vector_db(self, user_id, query, top_k=12):
        """Query the vector database and retrieve relevant document chunks"""
        try:
            if self.qdrant_client is None:
                print("Qdrant client initialization failed.")
                return []

            query_embedding = self._generate_embeddings([query])[0]
            if not query_embedding:
                print("Failed to generate query embedding.")
                return []

            user_filter = Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))])

            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=user_filter,
                limit=top_k
            )

            return [result.payload for result in results]
        
        except Exception as e:
            print(f"Error retrieving data for user {user_id}: {str(e)}")
            return []
