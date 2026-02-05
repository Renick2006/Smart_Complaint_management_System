import pandas as pd
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

# Load data
df = pd.read_csv("complaints.csv")

# Clean text
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

df["clean_text"] = df["complaint"].apply(clean_text)

# Encode labels
category_encoder = LabelEncoder()
urgency_encoder = LabelEncoder()

df["category_label"] = category_encoder.fit_transform(df["category"])
df["urgency_label"] = urgency_encoder.fit_transform(df["urgency"])

# Vectorization
tfidf = TfidfVectorizer(max_features=3000)
X = tfidf.fit_transform(df["clean_text"])

y_cat = df["category_label"]
y_urg = df["urgency_label"]

# Train models
category_model = LinearSVC()
urgency_model = LinearSVC()

category_model.fit(X, y_cat)
urgency_model.fit(X, y_urg)

# Save models
joblib.dump(tfidf, "tfidf.pkl")
joblib.dump(category_model, "category_model.pkl")
joblib.dump(urgency_model, "urgency_model.pkl")
joblib.dump(category_encoder, "category_encoder.pkl")
joblib.dump(urgency_encoder, "urgency_encoder.pkl")

print("✅ Models trained and saved")
