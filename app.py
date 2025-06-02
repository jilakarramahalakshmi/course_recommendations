from flask import Flask, render_template, request, abort
import webbrowser
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Local MongoDB
db = client['local']  # Replace with your desired database name
signup_collection = db['signup']  # For signup details
login_collection = db['login']    # For login details
profile_collection = db['profile']  # For profile details


app = Flask(__name__)

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

required_columns = ['Course', 'Topics', 'Google Link', 'YouTube Link', 'Online Link']
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

df = df.dropna(subset=['Course', 'Topics'])

vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df['Topics'].astype(str))
similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        # Check if passwords match
        if password != confirm_password:
            return "Passwords do not match!"

        # Insert into MongoDB
        signup_collection.insert_one({
            "name": name,
            "email": email,
            "password": password  # Ideally, hash the password before storing it
        })

        return "Signup successful!"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if user exists
        user = signup_collection.find_one({"email": email})
        if user and user['password'] == password:
            # Store login attempt
            login_collection.insert_one({"email": email, "status": "Success"})
            return "Login successful!"
        else:
            # Track failed login
            login_collection.insert_one({"email": email, "status": "Failed"})
            return "Invalid email or password!"
    return render_template('login.html')




@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form['username']
    email = request.form['email']
    mobile = request.form['mobile']
    designation = request.form['designation']
    graduation = request.form['graduation']
    branch = request.form['branch']

    # Profile image handling
    profile_image = request.files.get('profileImage')
    profile_image_name = None
    if profile_image and profile_image.filename:
        profile_image_name = profile_image.filename
        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        profile_image.save(os.path.join(upload_folder, profile_image_name))

    # Check if profile exists, update or insert
    profile_collection.update_one(
        {"email": email},
        {"$set": {
            "username": username,
            "mobile": mobile,
            "designation": designation,
            "graduation": graduation,
            "branch": branch,
            "profileImage": profile_image_name
        }},
        upsert=True
    )

    return "Profile updated successfully!"


@app.route('/course', methods=['GET', 'POST'])
def courses():
    courses = df['Course'].unique()
    selected_course = request.form.get('course')
    topics = []
    selected_topic = request.form.get('topic')
    links = {}

    if selected_course:
        topics = df[df['Course'] == selected_course]['Topics'].unique()

    if selected_topic:
        selected_row = df[(df['Course'] == selected_course) & (df['Topics'] == selected_topic)]
        if not selected_row.empty:
            links = {
                'Google Link': selected_row.iloc[0]['Google Link'],
                'YouTube Link': selected_row.iloc[0]['YouTube Link'],
                'Online Link': selected_row.iloc[0]['Online Link'],
            }
    
    return render_template('course.html', courses=courses, topics=topics, selected_course=selected_course, selected_topic=selected_topic, links=links)

if __name__ == '__main__':
    port = 5000
    webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(debug=True, port=port)
