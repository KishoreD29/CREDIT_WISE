from flask import Flask, render_template, jsonify
import pandas as pd
import joblib
import sqlite3
import time
import win32clipboard
import win32con
import pyautogui
import subprocess
from PIL import Image
import io

app = Flask(__name__)

# Load Machine Learning Model & Scaler
model = joblib.load(r"C:\Users\kishore giri\Downloads\creditwise\credit_tier_model.pkl")
scaler = joblib.load(r"C:\Users\kishore giri\Downloads\creditwise\scaler.pkl")

# Define feature columns
features = ['age', 'income', 'credit_score', 'credit_utilization', 'years_in_job']

# CSV File Path
INPUT_CSV = r"C:\Users\kishore giri\Downloads\creditwise\creditwise\csc.csv"

# Database Initialization
def init_db():
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phone TEXT,
                        age INTEGER,
                        income REAL,
                        credit_score INTEGER,
                        credit_utilization REAL,
                        years_in_job INTEGER,
                        current_tier TEXT,
                        predicted_tier TEXT
                    )''')
    conn.commit()
    conn.close()

# Process CSV & Update Predictions
def process_csv():
    df = pd.read_csv(INPUT_CSV)

    # Ensure required columns exist
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing features in CSV: {missing_features}")

    # Scale & Predict
    df_scaled = scaler.transform(df[features])
    df['predicted_tier'] = model.predict(df_scaled)

    # Update Database
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions")  # Clear old data

    for _, row in df.iterrows():
        cursor.execute('''INSERT INTO predictions (phone, age, income, credit_score, credit_utilization, years_in_job, current_tier, predicted_tier) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (row['phone'], row['age'], row['income'], row['credit_score'], row['credit_utilization'], row['years_in_job'], row.get('card_tier', None), row['predicted_tier']))
    
    conn.commit()
    conn.close()
    print("Database updated with new predictions.")

# Fetch Updated Predictions
def get_predictions():
    conn = sqlite3.connect('predictions.db')
    df = pd.read_sql_query("SELECT phone, current_tier, predicted_tier FROM predictions WHERE current_tier != predicted_tier", conn)
    conn.close()
    return df.to_dict(orient='records')

# Copy Image to Clipboard using PyWin32
def copy_image_to_clipboard(image_path):
    """Copies an image to the clipboard for pasting in WhatsApp."""
    image = Image.open(image_path)
    output = io.BytesIO()
    image.save(output, format="BMP")
    data = output.getvalue()[14:]  # Remove BMP header
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    win32clipboard.CloseClipboard()

# Send WhatsApp Message Automatically via WhatsApp Desktop
def send_whatsapp_message(phone_number, message, image_path=None):
    try:
        # Open WhatsApp Desktop Chat
        subprocess.run(["cmd", "/c", f"start whatsapp://send?phone={phone_number}"], shell=True)
        time.sleep(5)  # Wait for chat to load

        # Type and Send Message
        pyautogui.typewrite(message)
        pyautogui.press('enter')

        if image_path:
            # Copy image to clipboard
            copy_image_to_clipboard(image_path)
            time.sleep(2)

            # Paste & Send Image
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            pyautogui.press('enter')  # Automatically send the image

        print(f"Message and image sent to {phone_number}")

    except Exception as e:
        print(f"Error sending message/image to {phone_number}: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/fetch', methods=['GET'])
def fetch_data():
    process_csv()
    data = get_predictions()  
    return render_template('table.html', data=data)

@app.route('/send_messages', methods=['POST'])
def send_messages():
    conn = sqlite3.connect('predictions.db')
    df = pd.read_sql_query("SELECT phone, current_tier, predicted_tier FROM predictions WHERE current_tier != predicted_tier", conn)
    conn.close()
    tiers = ["Bronze", "Silver", "Gold", "Platinum"]
    image_path = r"C:\Users\kishore giri\Downloads\creditwise\creditwise\static\images\scheme1.jpeg"
    for _, row in df.iterrows():
        phone_number = row['phone']
        if tiers.index(row['current_tier']) > tiers.index(row['predicted_tier']):
            message = "Dear Customer, your credit tier has been downgraded. Contact the bank for assistance."
        else:
            message = "Dear Customer, you are now eligible for our ‘Smart Savings Plan’ and ‘Flexible Credit Scheme.’ Contact the bank for details."

        if not phone_number.startswith("+"):
            phone_number = "+91" + phone_number  

        print(f"Sending message to {phone_number}: {message}")
        send_whatsapp_message(phone_number, message, image_path)

    return jsonify({"status": "Messages sent successfully"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)