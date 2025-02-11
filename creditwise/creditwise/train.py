import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split



# Load training data
training_data = pd.read_csv(r"C:\Users\kishore giri\Downloads\tsxdrdo (2)\tsxdrdo\your_training_data.csv")

# Define features and target
features = ['age', 'income', 'credit_score', 'credit_utilization', 'years_in_job']
X = training_data[features]
y = training_data['card_tier']

# Split data for training
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Save the trained model and scaler
joblib.dump(model, 'credit_tier_model.pkl')
joblib.dump(scaler, 'scaler.pkl')

print("Model training complete. Checkpoints saved.")
