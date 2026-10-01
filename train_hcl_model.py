import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def train_and_export():
    print("=" * 60)
    print("🎬 HCL MOVIE RECOMMENDATION SYSTEM — MODEL TRAINING & EXPORT")
    print("=" * 60)

    csv_path = "HCL_Movie_Recommendation_Project/movies_10k.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing {csv_path}. Run prepare_hcl_dataset.py first.")

    movies_df = pd.read_csv(csv_path)
    movies_df['overview'] = movies_df['overview'].fillna('')
    movies_df['title'] = movies_df['title'].fillna('')
    movies_df['clean_title'] = movies_df['clean_title'].fillna('')

    print(f"1. Dataset Loaded: {len(movies_df):,} movies.")

    # 2. Feature Engineering with TF-IDF
    print("2. Transforming textual features with TF-IDF Vectorizer...")
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    tfidf_matrix = tfidf.fit_transform(movies_df['overview'])
    print(f"   TF-IDF Matrix Shape: {tfidf_matrix.shape}")

    # 3. Fit Nearest Neighbors (KNN) Model using Cosine Distance
    print("3. Training NearestNeighbors (KNN) model with Cosine Distance...")
    knn_model = NearestNeighbors(n_neighbors=10, metric='cosine', algorithm='brute')
    knn_model.fit(tfidf_matrix)

    # 4. Compute Cosine Similarity Matrix (subset/dense or sparse for fast lookup)
    print("4. Computing Cosine Similarity Matrix...")
    similarity_matrix = cosine_similarity(tfidf_matrix)
    print(f"   Similarity Matrix Shape: {similarity_matrix.shape}")

    # 5. Recommendation Helper function
    def recommend(movie_title, top_n=5):
        # Case-insensitive title match
        match = movies_df[movies_df['clean_title'].str.contains(movie_title, case=False, na=False)]
        if match.empty:
            match = movies_df[movies_df['title'].str.contains(movie_title, case=False, na=False)]
            
        if match.empty:
            print(f"❌ Movie '{movie_title}' not found.")
            return []

        idx = match.index[0]
        matched_title = movies_df.iloc[idx]['title']
        print(f"🎯 Query Matched: '{matched_title}'")

        # Query KNN
        distances, indices = knn_model.kneighbors(tfidf_matrix[idx], n_neighbors=top_n+1)
        
        recs = []
        for i in range(1, len(indices[0])):
            m_idx = indices[0][i]
            dist = distances[0][i]
            score = round(1 - dist, 4)
            recs.append({
                'title': movies_df.iloc[m_idx]['title'],
                'genres': movies_df.iloc[m_idx]['genres'],
                'similarity': score
            })
        return recs

    # 6. Test with yesterday's test movie: "Electric Heart"
    print("\n--- 🧪 TEST 1: Query 'Electric Heart' ---")
    test_recs = recommend("Electric Heart", top_n=5)
    for r in test_recs:
        print(f"   * {r['title']} [{r['genres']}] - Score: {r['similarity']}")

    print("\n--- 🧪 TEST 2: Query 'Toy Story' ---")
    test_recs_2 = recommend("Toy Story", top_n=5)
    for r in test_recs_2:
        print(f"   * {r['title']} [{r['genres']}] - Score: {r['similarity']}")

    # 7. Save .pkl artifacts for Flask backend
    out_dir = "HCL_Movie_Recommendation_Project"
    
    print("\n7. Saving model artifacts as .pkl files for Flask backend...")
    pickle.dump(movies_df.to_dict(), open(os.path.join(out_dir, "movies_dict.pkl"), "wb"))
    pickle.dump(movies_df, open(os.path.join(out_dir, "movies_list.pkl"), "wb"))
    pickle.dump(knn_model, open(os.path.join(out_dir, "knn_model.pkl"), "wb"))
    pickle.dump(similarity_matrix, open(os.path.join(out_dir, "similarity.pkl"), "wb"))
    pickle.dump(tfidf, open(os.path.join(out_dir, "tfidf_vectorizer.pkl"), "wb"))
    pickle.dump(tfidf_matrix, open(os.path.join(out_dir, "tfidf_matrix.pkl"), "wb"))

    print("   [+] movies_dict.pkl saved")
    print("   [+] movies_list.pkl saved")
    print("   [+] knn_model.pkl saved")
    print("   [+] similarity.pkl saved")
    print("   [+] tfidf_vectorizer.pkl saved")
    print("   [+] tfidf_matrix.pkl saved")
    print("\n✅ Training complete! Artifacts are ready for Flask!")

if __name__ == "__main__":
    train_and_export()
