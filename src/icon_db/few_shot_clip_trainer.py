import os
import clip
import torch
import numpy as np
from sklearn.linear_model import LogisticRegression
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import ImageFolder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from tqdm import tqdm
from sklearn.preprocessing import OneHotEncoder
import pickle



# Define custom dataset class
class CustomDataset(Dataset):
    def __init__(self, folder_path, transform):
        self.data = ImageFolder(root=folder_path, transform=transform)

        labels = [img_path.split(os.path.sep)[3].upper() for img_path, _ in self.data.samples]
        print(labels)
        str_to_index = {string: idx for idx, string in enumerate(labels)}
        self.labels = [str_to_index[string] for string in labels]
        with open('str_to_index.pkl', 'wb') as f:
            pickle.dump(str_to_index, f)

        # One-hot encode labels
        # onehot_encoder = OneHotEncoder(sparse=False)
        # self.labels= onehot_encoder.fit_transform(np.array(self.labels).reshape(-1, 1))
        # print(self.labels)


    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

# Function to get features from a dataset
def get_features(dataset, model, device):
    all_features = []

    with torch.no_grad():
        for images, _ in tqdm(DataLoader(dataset, batch_size=100)):
            features = model.encode_image(images.to(device))
            all_features.append(features)

    return torch.cat(all_features).cpu().numpy()

# Define your own data
folder_path = "../feature_db/icon_simplified/"
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load('ViT-B/32', device)

# Create a custom dataset
custom_dataset = CustomDataset(folder_path, transform=preprocess)

# Split data into train and test sets
train_dataset, test_dataset, train_labels, test_labels = train_test_split(
    custom_dataset, custom_dataset.labels, test_size=0.1, random_state=42
)

# Get features for the train and test datasets
train_features = get_features(train_dataset, model, device)
test_features = get_features(test_dataset, model, device)

# Perform logistic regression
classifier = LogisticRegression(random_state=0, C=0.316, max_iter=10000, verbose=1)
classifier.fit(train_features, train_labels)

# Save the trained model
torch.save(classifier, 'logistic_regression_model.pth')

# Evaluate using the logistic regression classifier
predictions = classifier.predict(test_features)
accuracy = accuracy_score(test_labels, predictions)
precision = precision_score(test_labels, predictions, average='weighted')
recall = recall_score(test_labels, predictions, average='weighted')
f1 = f1_score(test_labels, predictions, average='weighted')

print(f"Accuracy = {accuracy:.3f}")
print(f"Precision = {precision:.3f}")
print(f"Recall = {recall:.3f}")
print(f"F1 Score = {f1:.3f}")

# Additional detailed classification report
print("Classification Report:")
print(classification_report(test_labels, predictions))

