from onnx_embedder import ONNXEmbedder
import time

embedder = ONNXEmbedder()

start = time.time()
emb = embedder.embed("AMD Ryzen offline AI benchmark")
end = time.time()

print("Embedding shape:", emb.shape)
print(f"Inference Time: {(end-start)*1000:.2f} ms")