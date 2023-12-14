from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_caching import Cache
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem-based session storage
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 180 
Session(app)

# Configure Flask-Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

db = SQLAlchemy(app)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    bone_loss_percentage = db.Column(db.Float, nullable=False)
    cbct_image = db.Column(db.String, nullable=True) 

@app.route('/')
def index():

    
    referer = request.headers.get('Referer')
    if not referer or '/submit' not in referer:
        return redirect('/')
    session['counter'] = session.get('counter', 0) + 1
    return render_template('index.html', counter=session['counter'])

@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve patient information
    patient_name = request.form.get('patient_name')
    patient_age = request.form.get('patient_age')
    bone_loss_percentage = request.form.get('bone_loss_percentage')

    # Process CBCT image (upload handling logic goes here)
    cbct_image = request.files['cbct_image'].read()

    # Encode the image data as base64
    encoded_image = base64.b64encode(cbct_image).decode('utf-8')

    # Save data to the database
    with app.app_context():
        patient_data = Patient(
            name=patient_name,
            age=patient_age,
            bone_loss_percentage=bone_loss_percentage,
            cbct_image=encoded_image
        )
        db.session.add(patient_data)
        db.session.commit()

    # Determine prognosis based on bone loss percentage
    bone_loss_percentage = int(bone_loss_percentage)
    if bone_loss_percentage <= 15:
        prognosis = 'Good'
    elif 15 < bone_loss_percentage <= 50:
        prognosis = 'Moderate'
    elif 50 < bone_loss_percentage <= 80:
        prognosis = 'Bad'
    else:
        prognosis = 'Worst'

    # Define image paths based on bone loss percentage
    if bone_loss_percentage < 15:
        m = 'data:image/png;base64,{{ decoded_image }}'
        after_5_years_image_path = 'm'
        after_10_years_image_path = '/static/peritonitis/27.jpg'
        after_15_years_image_path = '/static/peritonitis/36.jpg'
    elif 15 <= bone_loss_percentage <= 35:
        after_5_years_image_path = '/static/peritonitis/31.5.jpg'
        after_10_years_image_path = '/static/peritonitis/36.jpg'
        after_15_years_image_path = '/static/peritonitis/40.51.jpg'
    elif 35 < bone_loss_percentage <= 50:
        after_5_years_image_path = '/static/peritonitis/51.jpg'
        after_10_years_image_path = '/static/peritonitis/56.jpg'
        after_15_years_image_path = '/static/peritonitis/62.jpg'
    elif 50 < bone_loss_percentage <= 80:
        after_5_years_image_path = '/static/peritonitis/66.jpg'
        after_10_years_image_path = '/static/peritonitis/72.jpg'
        after_15_years_image_path = '/static/peritonitis/78.jpg'
    else:
        after_5_years_image_path = '/static/peritonitis/dht.png'
        after_10_years_image_path = '/static/peritonitis/dht.png'
        after_15_years_image_path = '/static/peritonitis/dht.png'

    # Using Flask-Caching to cache the result view
    result_html = cache.get(f'result_{patient_name}_{patient_age}_{bone_loss_percentage}')
    if result_html is None:
        # Render the template
        result_html = render_template('result.html', 
                               patient_name=patient_name,
                               patient_age=patient_age,
                               bone_loss_percentage=bone_loss_percentage,
                               decoded_image=encoded_image,
                               prognosis=prognosis,
                               after_5_years_image_path=after_5_years_image_path,
                               after_10_years_image_path=after_10_years_image_path,
                               after_15_years_image_path=after_15_years_image_path)
        # Cache the result for future requests
        cache.set(f'result_{patient_name}_{patient_age}_{bone_loss_percentage}', result_html, timeout=60)

    return result_html

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the necessary tables
    app.run(debug=True)
