# File Compression and Upload Utility

This module provides functions to compress files and upload them in chunks to Supabase storage.

## Functions:
* `compress_and_upload_file`: Compresses a file using LZMA, splits it into 50MB chunks, and uploads each chunk to Supabase storage.
* `start_compression_thread`: Initiates a background thread to compress and upload a file without blocking the main process.

## Key Features:
* LZMA compression for efficient file size reduction
* Chunking of large files into 50MB segments
* Background processing for non-blocking operation
* Direct upload to Supabase storage
* Unique file ID generation for organized storage

## Usage:
The compression process runs asynchronously, allowing the agent to perform other tasks while the file is being compressed and uploaded.