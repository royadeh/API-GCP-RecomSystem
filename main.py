from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load data
students_df = pd.read_excel("university_data.xlsx", sheet_name='Students')
professor_df = pd.read_excel("university_data.xlsx", sheet_name='Professors')

# Preprocess data: combine fields, lowercase, remove spaces
students_df['Research Interests'] = (students_df['Research Interests'] + ", " + students_df['University Field']).str.replace(' ', '').str.lower()
professor_df['Research Interests'] = (professor_df['Research Interests'] + ", " + professor_df['University Field']).str.replace(' ', '').str.lower()

# Concatenate interests for students and professors
all_interests = pd.concat([students_df['Research Interests'], professor_df['Research Interests']], ignore_index=True)

# Get unique research interests
unique_interests = set(','.join(all_interests).split(','))

# Create one-hot encoding for research interests
for interest in unique_interests:
    students_df[interest] = students_df['Research Interests'].apply(lambda x: 1 if interest in x else 0)
    professor_df[interest] = professor_df['Research Interests'].apply(lambda x: 1 if interest in x else 0)

# Calculate cosine similarity matrix
student_vectors = students_df.iloc[:, 5:].values
professor_vectors = professor_df.iloc[:, 5:].values
cos_sim_matrix = cosine_similarity(student_vectors, professor_vectors)

# Recommendation function
@app.route('/recommend/<user_id>')
def recommend(user_id):
    if user_id in students_df['Student GUID'].values:
        user_index = students_df[students_df['Student GUID'] == user_id].index[0]
        similarity_row = cos_sim_matrix[user_index]
        users = professor_df
    elif user_id in professor_df['Professor GUID'].values:
        user_index = professor_df[professor_df['Professor GUID'] == user_id].index[0]
        similarity_row = cos_sim_matrix[:, user_index]
        users = students_df
    else:
        return jsonify({"error": "User not found."}), 404
    
    matched_users_indices = np.where(similarity_row > 0.5)[0]
    matched_user_ids = users.iloc[matched_users_indices]['Professor GUID' if user_id in students_df['Student GUID'].values else 'Student GUID'].tolist()
    
    return jsonify(matched_user_ids)

if __name__ == '__main__':
    app.run(debug=True)
