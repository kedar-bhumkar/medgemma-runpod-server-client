#!/usr/bin/env python
# Client script to send local images to RunPod endpoint and save captions
# Also supports text-only questions

import os
import sys
import time
import base64
import argparse
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# ===== USER MODIFIABLE SETTINGS =====
# Your RunPod endpoint ID
ENDPOINT_ID = ""

# Your RunPod API key
API_KEY = ""

# Maximum concurrent requests
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "5"))

# Image folder
IMAGE_FOLDER = "C:\\tmp"

# Text questions file
TEXT_QUESTIONS_FILE = "questions.txt"

# Polling interval in seconds for async requests
POLLING_INTERVAL = int(os.environ.get("POLLING_INTERVAL", "2"))
# =====================================

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='RunPod Image Captioning and Text Question Client')
    parser.add_argument('--image_folder', type=str, default=IMAGE_FOLDER,
                        help='Path to folder containing images')
    parser.add_argument('--text_file', type=str, default=TEXT_QUESTIONS_FILE,
                        help='Path to file containing text questions (one per line)')
    parser.add_argument('--mode', choices=['image', 'text', 'both'], default='image',
                        help='Processing mode: image captioning, text questions, or both')
    parser.add_argument('--endpoint_id', type=str, default=ENDPOINT_ID,
                        help=f'RunPod endpoint ID (default: {ENDPOINT_ID})')
    parser.add_argument('--api_key', type=str, default=API_KEY,
                        help='RunPod API key')
    parser.add_argument('--concurrent', type=int, default=MAX_CONCURRENT,
                        help='Maximum number of concurrent requests')
    parser.add_argument('--sync', action='store_true',
                        help='Use synchronous requests instead of async')
    return parser.parse_args()

def encode_image_to_base64(image_path):
    """Load an image and convert it to base64."""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB mode if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Save to bytes buffer
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            
            # Encode to base64
            encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return encoded_image
    except Exception as e:
        print(f"Error encoding image {image_path}: {str(e)}")
        return None

def load_text_questions(text_file):
    """Load text questions from a file."""
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            questions = [line.strip() for line in f if line.strip()]
        return questions
    except FileNotFoundError:
        print(f"Warning: Text questions file '{text_file}' not found")
        return []
    except Exception as e:
        print(f"Error loading text questions from {text_file}: {str(e)}")
        return []

def send_image_request_sync(image_path, args):
    """Send a synchronous image request to the RunPod API."""
    try:
        image_name = os.path.basename(image_path)
        print(f"Processing image: {image_name}...")
        
        # Encode image
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return
        
        # Prepare API request - only send the image
        url = f"https://api.runpod.ai/v2/{args.endpoint_id}/runsync"
        headers = {
            "Authorization": f"Bearer {args.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "image": base64_image
            }
        }
        
        # Send request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Check for errors
        if "error" in result:
            print(f"Error with {image_name}: {result['error']}")
            return
        
        # Save caption
        image_base = os.path.splitext(image_path)[0]
        output_path = f"{image_base}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['output']['caption'])
        
        print(f"Caption saved to {output_path}")
        
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")

def send_text_request_sync(question, question_index, args):
    """Send a synchronous text request to the RunPod API."""
    try:
        print(f"Processing text question {question_index + 1}: {question[:50]}...")
        
        # Prepare API request - send text question
        url = f"https://api.runpod.ai/v2/{args.endpoint_id}/runsync"
        headers = {
            "Authorization": f"Bearer {args.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "text": question
            }
        }
        
        # Send request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Check for errors
        if "error" in result:
            print(f"Error with question {question_index + 1}: {result['error']}")
            return
        
        # Save answer
        output_path = f"question_{question_index + 1}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Question: {question}\n\nAnswer: {result['output']['answer']}")
        
        print(f"Answer saved to {output_path}")
        
    except Exception as e:
        print(f"Error processing question {question_index + 1}: {str(e)}")

def send_image_request_async(image_path, args):
    """Send an asynchronous image request to the RunPod API and poll for results."""
    try:
        image_name = os.path.basename(image_path)
        print(f"Processing image: {image_name}...")
        
        # Encode image
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return
        
        # Prepare API request for async operation - only send the image
        url = f"https://api.runpod.ai/v2/{args.endpoint_id}/run"
        headers = {
            "Authorization": f"Bearer {args.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "image": base64_image
            }
        }
        
        # Send request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        job_id = result.get('id')
        if not job_id:
            print(f"Error: No job ID returned for {image_name}")
            return
        
        # Poll for results
        status_url = f"https://api.runpod.ai/v2/{args.endpoint_id}/status/{job_id}"
        
        while True:
            time.sleep(POLLING_INTERVAL)
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data.get('status')
            
            if status == 'COMPLETED':
                # Save caption
                image_base = os.path.splitext(image_path)[0]
                output_path = f"{image_base}.txt"
                
                caption = status_data.get('output', {}).get('caption')
                if caption:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(caption)
                    print(f"Caption saved to {output_path}")
                else:
                    print(f"No caption received for {image_name}")
                break
            
            elif status == 'FAILED':
                print(f"Job failed for {image_name}: {status_data.get('error')}")
                break
            
            elif status == 'CANCELLED':
                print(f"Job cancelled for {image_name}")
                break
            
            elif status == 'IN_QUEUE' or status == 'IN_PROGRESS':
                print(f"Job status for {image_name}: {status}")
            
            else:
                print(f"Unknown status for {image_name}: {status}")
        
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")

def send_text_request_async(question, question_index, args):
    """Send an asynchronous text request to the RunPod API and poll for results."""
    try:
        print(f"Processing text question {question_index + 1}: {question[:50]}...")
        
        # Prepare API request for async operation - send text question
        url = f"https://api.runpod.ai/v2/{args.endpoint_id}/run"
        headers = {
            "Authorization": f"Bearer {args.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "text": question
            }
        }
        
        # Send request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        job_id = result.get('id')
        if not job_id:
            print(f"Error: No job ID returned for question {question_index + 1}")
            return
        
        # Poll for results
        status_url = f"https://api.runpod.ai/v2/{args.endpoint_id}/status/{job_id}"
        
        while True:
            time.sleep(POLLING_INTERVAL)
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data.get('status')
            
            if status == 'COMPLETED':
                # Save answer
                output_path = f"question_{question_index + 1}.txt"
                
                answer = status_data.get('output', {}).get('answer')
                if answer:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(f"Question: {question}\n\nAnswer: {answer}")
                    print(f"Answer saved to {output_path}")
                else:
                    print(f"No answer received for question {question_index + 1}")
                break
            
            elif status == 'FAILED':
                print(f"Job failed for question {question_index + 1}: {status_data.get('error')}")
                break
            
            elif status == 'CANCELLED':
                print(f"Job cancelled for question {question_index + 1}")
                break
            
            elif status == 'IN_QUEUE' or status == 'IN_PROGRESS':
                print(f"Job status for question {question_index + 1}: {status}")
            
            else:
                print(f"Unknown status for question {question_index + 1}: {status}")
        
    except Exception as e:
        print(f"Error processing question {question_index + 1}: {str(e)}")

def main():
    """Main function to run the client."""
    args = parse_arguments()
    
    # Print configuration
    print(f"Using endpoint ID: {args.endpoint_id}")
    print(f"Max concurrent requests: {args.concurrent}")
    print(f"Processing mode: {args.mode}")
    
    # Validate arguments
    if args.endpoint_id == "your-endpoint-id-here" or args.api_key == "your-runpod-api-key-here":
        print("ERROR: You must set your RunPod endpoint ID and API key")
        print("You can do this in the script, via command line arguments, or environment variables:")
        print("  RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY")
        sys.exit(1)
    
    # Process based on mode
    if args.mode in ['image', 'both']:
        # Get list of image files
        supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        image_files = [
            os.path.join(args.image_folder, f) for f in os.listdir(args.image_folder)
            if os.path.splitext(f.lower())[1] in supported_formats
        ]
        
        if not image_files:
            print(f"No supported image files found in {args.image_folder}")
            if args.mode == 'image':
                sys.exit(1)
        else:
            print(f"Found {len(image_files)} images to process")
    
    if args.mode in ['text', 'both']:
        # Load text questions
        text_questions = load_text_questions(args.text_file)
        
        if not text_questions:
            print(f"No text questions found in {args.text_file}")
            if args.mode == 'text':
                sys.exit(1)
        else:
            print(f"Found {len(text_questions)} text questions to process")
    
    # Process requests
    request_fn = send_image_request_sync if args.sync else send_image_request_async
    text_request_fn = send_text_request_sync if args.sync else send_text_request_async
    
    with ThreadPoolExecutor(max_workers=args.concurrent) as executor:
        futures = []
        
        # Add image processing tasks
        if args.mode in ['image', 'both'] and image_files:
            for image_path in image_files:
                futures.append(executor.submit(request_fn, image_path, args))
        
        # Add text processing tasks
        if args.mode in ['text', 'both'] and text_questions:
            for i, question in enumerate(text_questions):
                futures.append(executor.submit(text_request_fn, question, i, args))
        
        # Wait for all requests to complete
        for future in futures:
            future.result()
    
    if args.mode == 'image':
        print("All image captions generated successfully")
    elif args.mode == 'text':
        print("All text questions answered successfully")
    else:
        print("All processing completed successfully")

if __name__ == "__main__":
    t1 = time.time()
    main()
    t2 = time.time()
    print(f"Time taken: {t2 - t1} seconds")
