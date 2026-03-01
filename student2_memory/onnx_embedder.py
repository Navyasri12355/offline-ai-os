import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np

MODEL_PATH = "models/model.onnx"


class ONNXEmbedder:
    def __init__(self):
        print("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        print("Using AMD CPU Execution")
        self.session = ort.InferenceSession(
            MODEL_PATH,
            providers=["CPUExecutionProvider"]
        )

    def embed(self, text):
        tokens = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            return_tensors="np"
        )

        # Only pass inputs expected by ONNX model
        inputs = {}
        for inp in self.session.get_inputs():
            inputs[inp.name] = tokens[inp.name]

        outputs = self.session.run(None, inputs)

        embeddings = outputs[0]
        return embeddings.mean(axis=1)