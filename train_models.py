import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import pickle
import os
from dataset_generation import generate_synthetic_data
import dataset_generation

def train_and_save_models():
    print("Generating data...")
    df = generate_synthetic_data(10000)
    
    print("Training Category Model...")
    cat_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english')),
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    cat_pipeline.fit(df['description'], df['category'])
    
    print("Training Priority Model...")
    pri_pipeline = Pipeline([  #kjkssflfdlass kdffksjf slksdj lkss
        ('tfidf', TfidfVectorizer(stop_words='english')),
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    pri_pipeline.fit(df['description'], df['priority'])
    
    os.makedirs('models', exist_ok=True)
    with open('models/category_model.pkl', 'wb') as f:
        pickle.dump(cat_pipeline, f)
        
    with open('models/priority_model.pkl', 'wb') as f:
        pickle.dump(pri_pipeline, f)
        
    print("Models saved successfully in 'models/' directory.")

if __name__ == "__main__":
    train_and_save_models()
