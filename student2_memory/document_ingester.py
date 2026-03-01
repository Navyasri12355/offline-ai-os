import os
from onnx_embedder import ONNXEmbedder
from chroma_store import add_documents

embedder = ONNXEmbedder()

def ingest(folder):
    texts = []

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        if file.endswith(".txt"):
            with open(path) as f:
                texts.append(f.read())

    embeddings = [embedder.embed(t)[0] for t in texts]

    add_documents(texts, embeddings)

if __name__ == "__main__":
    ingest("data")