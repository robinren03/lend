import os
from PIL import Image
from PIL import ImageFile
import pickle
import faiss
import numpy as np
import clip
import torch
from sklearn.linear_model import LogisticRegression


ImageFile.LOAD_TRUNCATED_IMAGES = True
    
def load_clip_model(device):
    model, preprocess = clip.load('ViT-B/32', device)
    return model, preprocess

def build_index(embedding_list):
    index = faiss.index_factory(embedding_list.shape[1], "Flat", faiss.METRIC_INNER_PRODUCT)
    index.add(embedding_list)
    return index

def search_index(index, embedding_query, num_search):
    D, I = index.search(embedding_query, num_search)
    return I[0]


class ClipSearchTool:
    def __init__(self, db_dir, device="cuda"):
        self.device = device
        self.model, self.preprocess = load_clip_model(device)
        with open(os.path.join(db_dir, 'img_path_list.pkl'), 'rb') as f:
            self.img_path_list = pickle.load(f)
        with open(os.path.join(db_dir, "embedding_list.pkl"), "rb") as f:
            self.embedding_list = pickle.load(f)
        with open(os.path.join(db_dir, "class_list.pkl"), "rb") as f:
            self.class_list = pickle.load(f)
        self.index = build_index(self.embedding_list)
        loaded_classifier = torch.load(os.path.join(db_dir, 'logistic_regression_model.pth'), map_location="cpu")  # Specify the correct device

        # Create a new instance of LogisticRegression and load the trained model's state into it
        self.classifier = LogisticRegression(random_state=0, C=0.316, max_iter=10000, verbose=1)
        self.classifier.__dict__ = loaded_classifier.__dict__
        # Load str_to_index from the pickle file
        with open(os.path.join(db_dir, 'str_to_index.pkl'), 'rb') as f:
            self.str_to_index = pickle.load(f)
        

    def search_by_image(self, image = None, image_path = None, zero_shot=False, a_reg=0.7):
        num_search = 5
        if image is None and image_path is None:
            return None
        if image is None:
            image = Image.open(image_path)
        image = image.convert('RGB')
        img_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            raw_features = self.model.encode_image(img_tensor.to(self.device))

        features = raw_features / raw_features.norm(dim=-1, keepdim=True)
        embedding_query = features.detach().cpu().numpy().astype(np.float32)

        match_indices = search_index(self.index, embedding_query, num_search)
        match_path_list = [self.img_path_list[i] for i in match_indices]

        short_embedding = self.embedding_list[match_indices]
        score = np.inner(embedding_query, short_embedding)[0]
        score = np.exp(score)
        sum_score = np.sum(score, axis=-1)
        expected_type = [(path, score[idx] / sum_score) for idx, path in enumerate(match_path_list)]

        label = None

        raw_features = raw_features.detach().cpu().numpy()
        # Make predictions using the loaded model
        predictions = self.classifier.predict(raw_features)
        # Convert predictions back to original string labels
        index_to_str = {idx: string for string, idx in self.str_to_index.items()}
        original_labels = [index_to_str[prediction] for prediction in predictions]
        label = original_labels[0]

        if label == "OTHER_DEVICE": label = "DEVICE"       
        type_by_text = [(cls, ((a_reg if cls==label else 0) + np.max(np.dot(embedding_query, np.transpose(self.class_list[cls]))))) for cls in self.class_list]
        type_by_text = sorted(type_by_text, key=lambda x: x[1], reverse=True)

        return expected_type, type_by_text

    
if "DB_DIR" in os.environ: db_dir = os.environ["DB_DIR"]
else: db_dir = os.path.join(os.environ["PROJECT_DIR"], "models")
clip_search_tool = ClipSearchTool(db_dir)
