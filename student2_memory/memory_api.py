from onnx_embedder import ONNXEmbedder
from chroma_store import query_documents

embedder = ONNXEmbedder()

def search_memory(query: str):
    emb = embedder.embed(query)[0]
    results = query_documents(emb)
    return results["documents"]

if __name__ == "__main__":
    print(search_memory("test"))