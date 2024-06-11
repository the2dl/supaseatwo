import os
import lzma
import shutil

CHUNK_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_OUTPUT_DIR = r"C:\ProgramData\chunk"
FINAL_OUTPUT_DIR = r"C:\ProgramData"

def ensure_output_directory():
    if not os.path.exists(CHUNK_OUTPUT_DIR):
        os.makedirs(CHUNK_OUTPUT_DIR)

def chunk_file(file_path, chunk_size=CHUNK_SIZE):
    """Chunks a file into smaller pieces."""
    chunks = []
    with open(file_path, 'rb') as f:
        chunk_number = 0
        while True:
            chunk_data = f.read(chunk_size)
            if not chunk_data:
                break
            chunk_filename = os.path.join(CHUNK_OUTPUT_DIR, f"{os.path.basename(file_path)}.chunk{chunk_number}")
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            chunks.append(chunk_filename)
            chunk_number += 1
    return chunks

def merge_chunks(chunks, output_file):
    """Merges chunk files into a single file."""
    with open(output_file, 'wb') as merged_file:
        for chunk in chunks:
            with open(chunk, 'rb') as chunk_file:
                shutil.copyfileobj(chunk_file, merged_file)

def compress_file(file_path):
    ensure_output_directory()
    
    compressed_file_path = os.path.join(CHUNK_OUTPUT_DIR, f"{os.path.basename(file_path)}.xz")
    
    # Compress the file
    with open(file_path, 'rb') as input_file:
        with lzma.open(compressed_file_path, 'wb') as compressed_file:
            shutil.copyfileobj(input_file, compressed_file)
    
    # Chunk the compressed file
    chunks = chunk_file(compressed_file_path)
    
    # If only one chunk, the file is already fully compressed
    if len(chunks) == 1:
        final_compressed_file_path = os.path.join(FINAL_OUTPUT_DIR, os.path.basename(compressed_file_path))
        shutil.move(compressed_file_path, final_compressed_file_path)
        if os.path.exists(final_compressed_file_path):
            shutil.rmtree(CHUNK_OUTPUT_DIR)
        return final_compressed_file_path
    
    # Merge chunks if they exist
    final_compressed_file_path = os.path.join(FINAL_OUTPUT_DIR, f"{os.path.basename(file_path)}_final.xz")
    merge_chunks(chunks, final_compressed_file_path)
    
    # Remove chunk files if the merge is successful
    if os.path.exists(final_compressed_file_path):
        for chunk in chunks:
            os.remove(chunk)
        shutil.rmtree(CHUNK_OUTPUT_DIR)
    
    return final_compressed_file_path
