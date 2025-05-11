"""
Explainable AI utilities for fish disease prediction.
This module provides functions for training a machine learning model
and generating explanations for predictions using various XAI techniques.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
import google.generativeai as genai
import warnings
import eli5
from eli5.sklearn import PermutationImportance
from lime import lime_tabular
from pdpbox import pdp
import io
from contextlib import redirect_stdout
import base64
import os
import json
from datetime import datetime

# Suppress warnings
warnings.filterwarnings('ignore')

# Create directories for saving plots
PLOTS_DIR = './static/plots'
os.makedirs(PLOTS_DIR, exist_ok=True)

def clean_data(df):
    """Clean and preprocess the dataset."""
    unnecessary_columns = ['id', 'uuid', 'user_id', 'status', 'image_url', 'created_at', 'updated_at']
    df = df.drop(columns=[col for col in unnecessary_columns if col in df.columns], errors='ignore')
    
    # Fill missing values
    numerical_cols = df.select_dtypes(include=['float64', 'int64']).columns
    df[numerical_cols] = df[numerical_cols].fillna(df[numerical_cols].mean())
    
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    df[categorical_cols] = df[categorical_cols].apply(lambda col: col.fillna(col.mode()[0]))

    df = df.drop_duplicates()
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    return df

def train_model():
    """Train a machine learning model for disease prediction and return the model and related objects."""
    # Load and clean data
    df = pd.read_csv("data/data.csv")
    df_cleaned = clean_data(df)

    # Define features and target
    target_column = 'disease_type'
    feature_columns = [col for col in df_cleaned.columns if col != target_column]
    numerical_features = df_cleaned[feature_columns].select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_features = df_cleaned[feature_columns].select_dtypes(include=['object', 'category']).columns.tolist()

    X = df_cleaned[numerical_features + categorical_features]
    y = df_cleaned[target_column]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Pipeline
    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), numerical_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ], remainder='passthrough')

    # Separate pipeline for preprocessing
    preprocess_pipeline = Pipeline([
        ('preprocessor', preprocessor)
    ])

    # Process training and test data - convert sparse to dense immediately
    X_train_processed = preprocess_pipeline.fit_transform(X_train)
    if hasattr(X_train_processed, "toarray"):  # Check if sparse and convert if needed
        X_train_processed = X_train_processed.toarray()

    X_test_processed = preprocess_pipeline.transform(X_test)
    if hasattr(X_test_processed, "toarray"):  # Convert test data too
        X_test_processed = X_test_processed.toarray()

    # Get feature names after preprocessing
    feature_names = []
    for name, _, cols in preprocessor.transformers_:
        if name == 'num':
            feature_names.extend(cols)
        elif name == 'cat':
            for col in cols:
                col_idx = preprocessor.transformers_[1][2].index(col)
                categories = preprocessor.named_transformers_['cat'].categories_[col_idx]
                for cat in categories:
                    feature_names.append(f"{col}_{cat}")

    # Train classifier separately after preprocessing
    classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    classifier.fit(X_train_processed, y_train)

    return {
        'classifier': classifier,
        'preprocessor': preprocessor,
        'preprocess_pipeline': preprocess_pipeline,
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'X_test_processed': X_test_processed,
        'feature_names': feature_names,
        'numerical_features': numerical_features,
        'categorical_features': categorical_features
    }

def validate_input_features(features, X_reference):
    """Validate and clean input features to ensure they match expected types.
    
    Args:
        features (dict): Raw input features
        X_reference (DataFrame): Reference DataFrame for feature validation
    
    Returns:
        dict: Validated features with correct types
    """
    validated = {}
    numerical_features = X_reference.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Ensure all expected columns are present
    for col in X_reference.columns:
        if col not in features:
            if col in numerical_features:
                validated[col] = X_reference[col].mean()
                print(f"Warning: Missing numerical feature '{col}'. Using mean value.")
            else:
                validated[col] = X_reference[col].mode()[0]
                print(f"Warning: Missing categorical feature '{col}'. Using most common value.")
        else:
            # Present but needs validation
            if col in numerical_features:
                try:
                    validated[col] = float(features[col])
                except (ValueError, TypeError):
                    print(f"Warning: Non-numeric value '{features[col]}' for numerical feature '{col}'. Using mean value.")
                    validated[col] = X_reference[col].mean()
            else:
                # For categorical, we'll keep as is and let OneHotEncoder handle unknown values
                validated[col] = features[col]
    
    return validated

def predict_and_explain(features, model_data=None, gemini_api_key=None):
    """
    Predict the disease type using a trained model and explain it using XAI methods.
    
    Args:
        features (dict): Input features as key-value pairs.
        model_data (dict, optional): Pre-trained model data. If None, a new model will be trained.
        gemini_api_key (str, optional): API key for Gemini AI. If None, will use environment variable.
        
    Returns:
        dict: Prediction results and explanations.
    """
    # Generate a unique ID for this prediction
    prediction_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create a plots directory for this prediction
    prediction_plots_dir = os.path.join(PLOTS_DIR, prediction_id)
    os.makedirs(prediction_plots_dir, exist_ok=True)
    
    # Train model if not provided
    if model_data is None:
        model_data = train_model()
    
    # Extract model components
    classifier = model_data['classifier']
    preprocess_pipeline = model_data['preprocess_pipeline']
    X_train = model_data['X_train']
    X_test = model_data['X_test']
    y_test = model_data['y_test']
    X_test_processed = model_data['X_test_processed']
    feature_names = model_data['feature_names']
    numerical_features = model_data['numerical_features']
    categorical_features = model_data['categorical_features']
    
    # Validate input features
    features = validate_input_features(features, X_train)
    
    # Convert features into a DataFrame
    input_df = pd.DataFrame([features])
    
    # Ensure column order matches training data
    input_df = input_df[X_train.columns]

    # Preprocess the input
    try:
        input_transformed = preprocess_pipeline.transform(input_df)
        if hasattr(input_transformed, "toarray"):
            input_transformed = input_transformed.toarray()  # Convert sparse to dense
    except Exception as e:
        return {"error": f"Error in preprocessing input: {str(e)}"}

    # Predict
    try:
        prediction = classifier.predict(input_transformed)[0]
        prediction_proba = classifier.predict_proba(input_transformed)[0]
        class_labels = classifier.classes_
        proba_dict = {label: float(prob) for label, prob in zip(class_labels, prediction_proba)}
    except Exception as e:
        return {"error": f"Error in making prediction: {str(e)}"}
    
    # Initialize results dictionary
    results = {
        "prediction_id": prediction_id,
        "prediction": prediction,
        "probabilities": proba_dict,
        "input_features": features,
        "plots": {},
        "xai_results": {}
    }
    
    # Generate explanations using different XAI methods
    try:
        # Method 1: Permutation Importance (ELI5)
        try:
            perm = PermutationImportance(classifier, random_state=42).fit(X_test_processed, y_test)
            
            # Capture ELI5 output
            with io.StringIO() as buf, redirect_stdout(None):
                eli5_explanation = eli5.format_as_text(
                    eli5.explain_weights(perm, feature_names=feature_names, top=20)
                )
            
            # Save permutation importance plot
            plt.figure(figsize=(12, 10))
            feature_importances = pd.Series(perm.feature_importances_, index=feature_names)
            top_features = feature_importances.abs().sort_values(ascending=False).head(15)
            top_features.plot.barh()
            plt.title('Permutation Feature Importance')
            plt.xlabel('Feature Importance (decrease in model performance)')
            plt.tight_layout()
            
            perm_importance_path = os.path.join(prediction_plots_dir, "permutation_importance.png")
            plt.savefig(perm_importance_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            results["plots"]["permutation_importance"] = f"/static/plots/{prediction_id}/permutation_importance.png"
            results["xai_results"]["permutation_importance"] = {
                "top_features": top_features.to_dict(),
                "full_text": eli5_explanation
            }
        except Exception as e:
            results["errors"] = results.get("errors", {})
            results["errors"]["permutation_importance"] = str(e)
        
        # Method 2: Random Forest Feature Importance
        try:
            rf_importances = classifier.feature_importances_
            
            plt.figure(figsize=(12, 10))
            rf_feature_importances = pd.Series(rf_importances, index=feature_names)
            top_rf_features = rf_feature_importances.sort_values(ascending=False).head(15)
            top_rf_features.plot.barh()
            plt.title('Random Forest Feature Importance')
            plt.xlabel('Feature Importance')
            plt.tight_layout()
            
            rf_importance_path = os.path.join(prediction_plots_dir, "rf_feature_importance.png")
            plt.savefig(rf_importance_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            results["plots"]["rf_importance"] = f"/static/plots/{prediction_id}/rf_feature_importance.png"
            results["xai_results"]["rf_importance"] = {
                "top_features": top_rf_features.to_dict()
            }
        except Exception as e:
            results["errors"] = results.get("errors", {})
            results["errors"]["rf_importance"] = str(e)
        
        # Method 3: LIME explanation
        try:
            categorical_names = {}
            for i, col in enumerate(categorical_features):
                col_idx = model_data['preprocessor'].transformers_[1][2].index(col)
                categories = model_data['preprocessor'].named_transformers_['cat'].categories_[col_idx]
                categorical_names[X_train.columns.get_loc(col)] = list(categories)
            
            explainer = lime_tabular.LimeTabularExplainer(
                X_train.values, 
                feature_names=X_train.columns.tolist(),
                class_names=list(classifier.classes_),
                categorical_features=[X_train.columns.get_loc(col) for col in categorical_features],
                categorical_names=categorical_names,
                mode="classification"
            )
            
            # Create the LIME explanation
            # Define a prediction function that properly converts to dense array and handles string values
            def classifier_predict_proba(x):
                try:
                    # Create DataFrame to ensure proper column ordering
                    processed_x = preprocess_pipeline.transform(pd.DataFrame(x, columns=X_train.columns))
                    if hasattr(processed_x, "toarray"):
                        processed_x = processed_x.toarray()
                    return classifier.predict_proba(processed_x)
                except ValueError as e:
                    print(f"Error in classifier_predict_proba: {e}")
                    # Return a default probability distribution matching the number of classes
                    # This ensures the LIME explainer doesn't crash even if there's an issue
                    return np.ones((x.shape[0], len(classifier.classes_))) / len(classifier.classes_)
            
            exp = explainer.explain_instance(
                input_df.values[0], 
                classifier_predict_proba,
                num_features=10
            )
            
            # Save LIME plot
            fig = exp.as_pyplot_figure(label=prediction)
            plt.title(f'LIME Explanation for {prediction}')
            plt.tight_layout()
            
            lime_path = os.path.join(prediction_plots_dir, "lime_explanation.png")
            plt.savefig(lime_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            results["plots"]["lime"] = f"/static/plots/{prediction_id}/lime_explanation.png"
            
            # Get LIME explanation as dict
            lime_explanation = exp.as_list()
            results["xai_results"]["lime"] = {
                "explanation": {str(feature): float(impact) for feature, impact in lime_explanation}
            }
        except Exception as e:
            results["errors"] = results.get("errors", {})
            results["errors"]["lime"] = str(e)
        
        # Method 4: PDP plots for top numerical features
        try:
            if "rf_importance" in results["xai_results"]:
                top_num_features = [f for f in numerical_features if f in top_rf_features.index[:5]]
                pdp_results = {}
                
                for feature in top_num_features[:3]:  # Limit to top 3 for simplicity
                    # Create PDP plot
                    pdp_isolate = pdp.pdp_isolate(
                        model=classifier, 
                        dataset=X_test,
                        model_features=X_train.columns.tolist(),
                        feature=feature,
                        num_grid_points=20,
                        pipeline=preprocess_pipeline
                    )
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    pdp.pdp_plot(pdp_isolate, feature, plot_lines=True, frac_to_plot=0.5, ax=ax)
                    plt.title(f'PDP Plot for {feature}')
                    plt.tight_layout()
                    
                    pdp_path = os.path.join(prediction_plots_dir, f"pdp_{feature}.png")
                    plt.savefig(pdp_path, dpi=150, bbox_inches='tight')
                    plt.close()
                    
                    results["plots"][f"pdp_{feature}"] = f"/static/plots/{prediction_id}/pdp_{feature}.png"
                    
                    # Save PDP data
                    pdp_results[feature] = {
                        "feature_values": pdp_isolate.feature_grids[0].tolist(),
                        "pdp_values": pdp_isolate.pdp[0].tolist()
                    }
                
                results["xai_results"]["pdp"] = pdp_results
        except Exception as e:
            results["errors"] = results.get("errors", {})
            results["errors"]["pdp"] = str(e)
        
        # Extract top features from all methods for analysis
        combined_top_features = set()
        
        if "permutation_importance" in results["xai_results"]:
            for f in list(results["xai_results"]["permutation_importance"]["top_features"].keys())[:10]:
                combined_top_features.add(f)
                
        if "rf_importance" in results["xai_results"]:
            for f in list(results["xai_results"]["rf_importance"]["top_features"].keys())[:10]:
                combined_top_features.add(f)
                
        if "lime" in results["xai_results"] and "explanation" in results["xai_results"]["lime"]:
            for f in list(results["xai_results"]["lime"]["explanation"].keys())[:10]:
                combined_top_features.add(f)
            
        results["top_features"] = list(combined_top_features)[:10]
                
    except Exception as e:
        results["errors"] = results.get("errors", {})
        results["errors"]["general"] = str(e)
    
    # Gemini Explanation with XAI insights
    try:
        # Configure Gemini
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        
        # Create a chat session with the Gemini model
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        chat = gemini_model.start_chat()
        
        # Prepare XAI insights for Gemini
        xai_info = ""
        
        if "permutation_importance" in results["xai_results"]:
            xai_info += "Feature importance from Permutation method:\n"
            for feature, importance in list(results["xai_results"]["permutation_importance"]["top_features"].items())[:5]:
                xai_info += f"- {feature}: {importance:.4f}\n"
            xai_info += "\n"
            
        if "rf_importance" in results["xai_results"]:
            xai_info += "Feature importance from Random Forest model:\n"
            for feature, importance in list(results["xai_results"]["rf_importance"]["top_features"].items())[:5]:
                xai_info += f"- {feature}: {importance:.4f}\n"
            xai_info += "\n"
            
        if "lime" in results["xai_results"] and "explanation" in results["xai_results"]["lime"]:
            xai_info += "LIME explanation for this specific case:\n"
            for feature, impact in list(results["xai_results"]["lime"]["explanation"].items())[:5]:
                direction = "increases" if impact > 0 else "decreases"
                xai_info += f"- {feature}: {direction} probability by {abs(impact):.4f}\n"
            xai_info += "\n"
            
        if "pdp" in results["xai_results"]:
            xai_info += "PDP analysis shows how these features affect prediction:\n"
            for feature in results["xai_results"]["pdp"]:
                xai_info += f"- {feature}: Has non-linear relationship with prediction outcome\n"
            xai_info += "\n"
        
        # Map feature values from input
        feature_values = ""
        for col in X_train.columns:
            if col in features:
                feature_values += f"- {col}: {features[col]}\n"
        
        prompt = (
            f"The model predicted the fish disease as '{prediction}' with {proba_dict[prediction]:.2f} probability. "
            f"Here are the input features:\n{feature_values}\n\n"
            f"The prediction probabilities across all classes are:\n{proba_dict}\n\n"
            f"Here are the results from multiple explainable AI methods:\n{xai_info}\n"
            "Based on this data, please provide a detailed analysis:\n"
            "1. Interpret how each of the top features influenced this prediction according to the XAI results\n"
            "2. Explain the biological/environmental mechanisms connecting these features to the disease\n"
            "3. Describe the typical symptoms of this fish disease\n"
            "4. Recommend appropriate treatments\n"
            "5. Suggest preventive measures for fish farmers\n\n"
            "Focus especially on explaining the relationship between the feature values and disease development."
        )
        
        response = chat.send_message(prompt)
        results["gemini_explanation"] = response.text.strip()
    except Exception as e:
        results["errors"] = results.get("errors", {})
        results["errors"]["gemini"] = str(e)

    return results
