# utils/weight_predictor.py
import joblib
import pandas as pd

model = joblib.load("app/models/weight/fish_weight_predictor.joblib")

def predict_weight(length_cm, species):
    df = pd.DataFrame({"species": [species], "length": [length_cm]})
    return model.predict(df)[0]/10 
