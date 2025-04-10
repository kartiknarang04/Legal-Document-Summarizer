import os
import sys
import zipfile
import shutil
import argparse

def setup_model(zip_path=None):
    """
    Extract the model from a zip file or create the model directory structure
    """
    model_dir = r"C:\Users\KNPRO\Desktop\projects\legal_case\model"

    # Create model directory if it doesn't exist
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print(f"Created model directory at {model_dir}")
    
    # If a zip file is provided, extract it
    if zip_path and os.path.exists(zip_path):
        print(f"Extracting model from {zip_path}...")
        
        # Create a temporary directory for extraction
        temp_dir = "./temp_model"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the final_model directory
        final_model_dir = None
        for root, dirs, files in os.walk(temp_dir):
            if "final_model" in dirs:
                final_model_dir = os.path.join(root, "final_model")
                break
        
        if final_model_dir:
            # Copy the contents to the model directory
            final_model_target = os.path.join(model_dir, "final_model")
            if os.path.exists(final_model_target):
                shutil.rmtree(final_model_target)
            shutil.copytree(final_model_dir, final_model_target)
            print(f"Model extracted to {final_model_target}")
        else:
            print("Could not find final_model directory in the zip file")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        print("Temporary files cleaned up")
    else:
        # Create the final_model directory if it doesn't exist
        final_model_dir = os.path.join(model_dir, "final_model")
        if not os.path.exists(final_model_dir):
            os.makedirs(final_model_dir)
            print(f"Created final_model directory at {final_model_dir}")
            print("Please place your model files in this directory")
    
    print("Model setup complete")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup the model directory structure")
    parser.add_argument("--zip", help="Path to the model zip file")
    args = parser.parse_args()
    setup_model(args.zip)
