import chromadb

client = chromadb.Client()

collection = client.get_or_create_collection(
    name="offline_memory"
)

def add_documents(texts, embeddings):
    for i, text in enumerate(texts):
        collection.add(
            documents=[text],
            embeddings=[embeddings[i]],
            ids=[str(i)]
        )

def query_documents(query_embedding):
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )