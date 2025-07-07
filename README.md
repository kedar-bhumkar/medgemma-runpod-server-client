# MedGemma Client-Server

A client script for interacting with RunPod endpoints that support both image captioning and text question answering.

## Features

- **Image Captioning**: Process images from a local folder and generate captions
- **Text Questions**: Answer text-only questions from a file
- **Concurrent Processing**: Handle multiple requests simultaneously
- **Synchronous/Asynchronous**: Support for both sync and async API calls
- **Flexible Modes**: Process images only, text only, or both

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Settings**:
   - Update `ENDPOINT_ID` and `API_KEY` in the script
   - Or use command line arguments
   - Or set environment variables: `RUNPOD_ENDPOINT_ID` and `RUNPOD_API_KEY`

3. **Prepare Your Data**:
   - For images: Place images in the specified folder (default: `C:\tmp`)
   - For text questions: Create a text file with one question per line (default: `questions.txt`)

## Usage

### Basic Usage

```bash
# Process images only (default)
python image-captioner.py

# Process text questions only
python image-captioner.py --mode text

# Process both images and text questions
python image-captioner.py --mode both

# Use synchronous requests
python image-captioner.py --sync

# Specify custom folders/files
python image-captioner.py --image_folder /path/to/images --text_file /path/to/questions.txt
```

### Command Line Arguments

- `--image_folder`: Path to folder containing images (default: `C:\tmp`)
- `--text_file`: Path to file containing text questions (default: `questions.txt`)
- `--mode`: Processing mode - `image`, `text`, or `both` (default: `image`)
- `--endpoint_id`: RunPod endpoint ID
- `--api_key`: RunPod API key
- `--concurrent`: Maximum number of concurrent requests (default: 5)
- `--sync`: Use synchronous requests instead of async

### Environment Variables

- `MAX_CONCURRENT`: Maximum concurrent requests
- `POLLING_INTERVAL`: Polling interval for async requests (seconds)
- `RUNPOD_ENDPOINT_ID`: RunPod endpoint ID
- `RUNPOD_API_KEY`: RunPod API key

## Output

### Image Processing
- Captions are saved as `.txt` files with the same name as the original image
- Example: `photo.jpg` → `photo.txt`

### Text Processing
- Answers are saved as `question_1.txt`, `question_2.txt`, etc.
- Each file contains both the question and the answer

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- WebP (.webp)

## Examples

### Process Images
```bash
python image-captioner.py --image_folder ./my_photos
```

### Process Text Questions
```bash
python image-captioner.py --mode text --text_file my_questions.txt
```

### Process Both with Custom Settings
```bash
python image-captioner.py --mode both --concurrent 10 --sync
```

## Error Handling

- Missing files/folders are handled gracefully with warnings
- API errors are logged with details
- Failed requests don't stop the processing of other items
- Network timeouts and retries are handled automatically

## Performance Tips

- Use `--sync` for faster processing when your endpoint supports it
- Adjust `--concurrent` based on your endpoint's capacity
- For large batches, consider processing images and text separately

## Troubleshooting

1. **"No supported image files found"**: Check your image folder path and file formats
2. **"No text questions found"**: Ensure your questions file exists and has content
3. **API errors**: Verify your endpoint ID and API key are correct
4. **Network issues**: Check your internet connection and endpoint availability
