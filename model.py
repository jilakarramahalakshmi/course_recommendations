import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
file_path = 'static/courses.xlsx'  # Adjust the path to your local file
df = pd.read_excel(file_path)

df.rename(columns={
    'COURSES': 'Course',
    'TOPIC': 'Topics',
    'TOPIC GOOGLE LINK': 'Google Link',
    'TOPIC YOUTUBE LINK': 'YouTube Link',
    'TOPIC ONLINE LINK': 'Online Link'
}, inplace=True)

# Ensure required columns exist
required_columns = ['Course', 'Topics', 'Google Link', 'YouTube Link', 'Online Link']
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# Remove rows with missing data
df = df.dropna(subset=['Course', 'Topics'])

# Vectorization and similarity calculation
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df['Topics'].astype(str))
similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

def get_course_data():
    return df, similarity_matrix



