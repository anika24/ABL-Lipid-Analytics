from flask import Flask, render_template, redirect, url_for, flash, session, request, send_file
import csv
import requests
import googlemaps
import sqlite3
import os
import json
import torch
import config


CURR_LOC = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.secret_key = 'spicytennistechersABL'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods =['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        sqlconnection = sqlite3.connect(CURR_LOC + '/login.db')
        cursor = sqlconnection.cursor()
        query1 = "SELECT username, password FROM users WHERE username = ? AND password = ?"
        rows = cursor.execute(query1, (username, password))
        rows = rows.fetchall()
        if len(rows) == 1: # valid username, password
            session['username'] = username
            return redirect(url_for('userform'))
        else: # invalid
            flash('Invalid username or password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/signup', methods =['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        sqlconnection = sqlite3.connect(CURR_LOC + '/login.db')
        cursor = sqlconnection.cursor()
        query_usernames = "SELECT * FROM users WHERE username = ? or email = ?"
        if len(cursor.execute(query_usernames, (username,email)).fetchall()) > 0:
            flash('Username or email already taken!')
            return redirect(url_for('signup'))
        query1 = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
        cursor.execute(query1, (username, password, email))
        sqlconnection.commit()
        flash('Account created successfully! Please login.')
        return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/logout',methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/location',methods=['GET'])
def location():
    return render_template('location.html')

@app.route('/userform', methods = ['POST', 'GET'])
def userform():
    if request.method == 'POST':
        result = request.form

        fields = ['ldlc', 'apob', 'gender', 'age', 'SBP', 'DBP', 'race', 'userWeight', 'userHeight', 'userEyesight', 'userWaist', 'userHip', 'covid', 'covid_case', 'covid_blood', 'IL-6', 'disease', 
                  'CPR', 'thyroid', 'T3', 'T4', 'TSH', 'chemo', 'iron', 'folate', 'Vitamin B12', 'Red blood cell count', 'White blood cell count', 'lactate dehydrognase', 
                  'bilirubin', 'albumin', 'blood']
        
        float_fields = ['ldlc', 'apob', 'SBP', 'DBP', 'weight', 'height', 'waist', 'hip', 'IL-6', 'CPR', 'T3', 'T4', 'TSH', 'iron', 
                       'folate', 'Vitamin B12', 'Red blood cell count', 'White blood cell count', 'lactate dehydrognase', 'bilirubin', 'albumin']
        
        output_dict = {field: float(result.get(field)) if result.get(field) and field in float_fields 
                       else int(result.get(field)) if result.get(field) and field in ['age'] 
                       else result.get(field) if result.get(field, '') != '' else None for field in fields}
        
        username = session['username']
        user_id = get_user_id(username)

        conn = sqlite3.connect('login.db')
        c = conn.cursor()
        # Delete the existing row with the matching user_id
        c.execute("""
            DELETE FROM user_dataform 
            WHERE user_id = ?
        """, (user_id,))

        # Insert the new row
        c.execute("""
            INSERT INTO user_dataform (user_id, ldlc, apob, sex, age, sbp, dbp, race, weight, height, eyesight, waist, hip, has_covid, covid_symptoms, 
                                       has_covid_blood, IL6, has_disease, CPR, thyroid_test, T3, T4, TSH, had_chemo, blood_test, iron, folate, 
                                       B12, rbc, wbc, LDH, bilirubin, albumin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, output_dict.get('ldlc'), output_dict.get('apob'), output_dict.get('gender'), output_dict.get('age'),
              output_dict.get('SBP'), output_dict.get('DBP'), output_dict.get('race'), output_dict.get('userWeight'),
              output_dict.get('userHeight'), output_dict.get('userEyesight'), output_dict.get('userWaist'),
              output_dict.get('userHip'), output_dict.get('covid'), output_dict.get('covid_case'),
              output_dict.get('covid_blood'), output_dict.get('IL-6'), output_dict.get('disease'),
              output_dict.get('CPR'), output_dict.get('thyroid'), output_dict.get('T3'), output_dict.get('T4'),
              output_dict.get('TSH'), output_dict.get('chemo'), output_dict.get('blood'), output_dict.get('iron'),
              output_dict.get('folate'), output_dict.get('Vitamin B12'), output_dict.get('Red blood cell count'),
              output_dict.get('White blood cell count'), output_dict.get('lactate dehydrognase'),
              output_dict.get('bilirubin'), output_dict.get('albumin')))

        conn.commit()
        conn.close()
        flash('Form submitted successfully!')
        return render_template("userform.html")
    
    return render_template('userform.html')

@app.route('/questionnaire', methods = ['POST', 'GET'])
def questionnaire():
    if request.method == 'POST':
        # Extract form data
        stool = request.form['stool']
        vision = request.form['vision']
        sight = request.form['sight']
        bruise = request.form['bruise']
        muscle = request.form['muscle']
        cuts = request.form['cuts']
        blood = request.form['blood']
        skin = request.form['skin']
        nail = request.form['nail']
        food_sensitivity = request.form['GI']
        jaundice = request.form['jaundice']
        bloat = request.form['bloating']
        weight_gain = request.form['fat']
        reflex = request.form['reflex']
        lipid = request.form['lipid']

        username = session['username']
        user_id = get_user_id(username)

        conn = sqlite3.connect('login.db')
        c = conn.cursor()
        # Delete the existing row with the matching user_id
        c.execute("""
            DELETE FROM questionnaire_responses 
            WHERE user_id = ?
        """, (user_id,))

        # Insert the new row
        c.execute("""
            INSERT INTO questionnaire_responses 
            (user_id, stool, vision, sight, bruise, muscle, cuts, blood, skin, nail, food_sensitivity, jaundice, bloat, weight_gain, reflex, lipid) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, stool, vision, sight, bruise, muscle, cuts, blood, skin, nail, food_sensitivity, jaundice, bloat, weight_gain, reflex, lipid))

        conn.commit()
        conn.close()

        flash('Form submitted successfully!')
        return render_template('questionnaire.html')

    return render_template('questionnaire.html')

@app.route('/prediction', methods = ['POST', 'GET'])
def prediction():
    if request.method == 'POST':
        gender = int(request.form.get('gender'))
        age = int(request.form.get('age'))
        systolic_bp = float(request.form.get('SBP'))
        diastolic_bp = float(request.form.get('DBP'))
        bmi = float(request.form.get('BMI'))
        height = float(request.form.get('ht'))
        waist = float(request.form.get('waist'))
        sag_abdominal = float(request.form.get('sag'))
        sight = float(request.form.get('seeing'))
        walking = float(request.form.get('walking'))
        anemia = float(request.form.get('anemia'))
        jaundice = float(request.form.get('jaundice'))
        liver = float(request.form.get('liver'))
        heart = float(request.form.get('heart'))
        health = float(request.form.get('health'))
        X = [[bmi, systolic_bp, diastolic_bp, gender, age, sag_abdominal/height, waist/height,
              health, sight, walking, anemia, jaundice, liver, heart]]
        input = torch.tensor(X).to(torch.float32)
        model1 = torch.load(CURR_LOC + '/ldl_pred.pth')
        model1.eval()
        output = model1(input).item()
        msg1 = ldl_output(output)
        flash('Projected LDL-c: ' + str(round(output)) + ' mg/dL. ' + msg1)
        model2 = torch.load(CURR_LOC + '/apob_pred.pth')
        model2.eval()
        output = model2(input).item()
        msg2 = ldl_output(output)
        flash('Projected Apo-B: ' + str(round(output)) + ' mg/dL. ' + msg2)
        flash('Consult a lipidologist if you are worried about your levels. You can find one near you using our resources page.')
        return render_template('prediction.html')
    return render_template('prediction.html')

@app.route('/map',methods = ['POST', 'GET'])
def map():
    if request.method == 'POST':
        location = request.form["location"]
        location = location.strip()
        URL = f'https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={config.API_KEY}'
        if(location != ''):
            location_detail = {'address':location}
            r = requests.get(url = URL, params = location_detail)
            data = r.json()
            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            gmaps = googlemaps.Client(key=config.API_KEY)
            places_result = gmaps.places(query=' lipidologist | lipid clinic | lipid testing', location=(latitude, longitude), radius=5000)
            places_json = json.dumps(places_result['results'])
            return render_template("map.html", lat = latitude, long = longitude, places=places_json, API_KEY = config.API_KEY)

        else:
            latitude = "No input given"
            longitude = "No input given"
    return render_template("map.html")

@app.route('/data', methods = ['GET'])
def data():
    return render_template('data.html')


##########
# HELPERS
##########

def ldl_output(val):
    if val < 30:
        return ('Your levels are extremely low.')
    if val < 50:
        return ('Your levels are low.')
    if val < 100:
        return ('Your levels are optimal.')
    if val < 130:
        return ('Your levels are near optimal.')
    if val < 160:
        return ('Your levels are borderline high.')
    if val < 190:
        return ('Your levels are high.')
    return ('Your levels are extremely high.')

def apob_output(val):
    if val < 30:
        return ('Your levels are extremely low.')
    if val < 70:
        return ('Your levels are low.')
    if val < 120:
        return ('Your levels are near optimal.')
    return ('Your levels are high.')


def get_user_id(username):
    conn = sqlite3.connect('login.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    user_id = c.fetchone()[0]
    conn.close()
    return user_id

@app.route('/download/questionnaire_responses', methods=['GET'])
def download_questionnaire_responses():
    # Fetch column names (schema) from SQLite database
    conn = sqlite3.connect('login.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(questionnaire_responses)")
    schema = [row[1] for row in cursor.fetchall()]

    # Fetch data from SQLite database
    cursor.execute("SELECT * FROM questionnaire_responses")
    data = cursor.fetchall()
    conn.close()

    # Generate CSV file
    with open('questionnaire_responses.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(schema)  # Write schema as first row
        writer.writerows(data)

    return send_file('questionnaire_responses.csv', as_attachment=True)

@app.route('/download/user_dataform', methods=['GET'])
def download_user_dataform():
    # Fetch column names (schema) from SQLite database
    conn = sqlite3.connect('login.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user_dataform)")
    schema = [row[1] for row in cursor.fetchall()]

    # Fetch data from SQLite database
    cursor.execute("SELECT * FROM user_dataform")
    data = cursor.fetchall()
    conn.close()

    # Generate CSV file
    with open('user_dataform.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(schema)  # Write schema as first row
        writer.writerows(data)

    return send_file('user_dataform.csv', as_attachment=True)