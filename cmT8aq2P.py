import torch
from transformers import AutoModel, AutoTokenizer
import numpy as np
from tqdm import tqdm


class SentenceBertTransformer:
    def __init__(self, model_name='setu4993/LaBSE', device='cpu', max_len=512):
        self.model_name = model_name
        self.device = device
        self.max_len = max_len
        
    def load_model(self):
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model = self.model.to(self.device)
        self.model = self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
    def transform(self, text):
        inputs = self.tokenizer(
            [text], return_tensors="pt", padding=True, max_length=self.max_len, verbose=False, truncation=True
        )
        inputs = inputs.to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        return outputs[1][0].detach().cpu().numpy()
    
    def transform_batch(self, texts, bs=32):
        batch_count = len(texts) // bs + int(len(texts) % bs != 0)
        results = []
        for i in tqdm(range(batch_count)):
            batch = texts[i * bs: (i + 1) * bs]
            inputs = self.tokenizer(
                batch, return_tensors='pt', padding=True, max_length=self.max_len, verbose=False, truncation=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
            
            results.append(outputs[1].detach().cpu().numpy())

        torch.cuda.empty_cache()
        return np.vstack(results)

trf = SentenceBertTransformer(device="cuda")
trf.load_model()

def cosin_distance(word, sentense):
    word_embeding = trf.transform(word)
    sentense_embeding = trf.transform(sentense)
    return np.dot(word_embeding, sentense_embeding) / (sum(sentense_embeding ** 2) * sum(word_embeding ** 2))
print(cosin_distance("Я иду по лесу", "я иду"))