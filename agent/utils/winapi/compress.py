import os
import lzma
import uuid
import threading
from ..file_operations import supabase, bucket_name, with_retries, get_public_url

CHUNK_SIZE = 50 * 1024 * 1024  # 50MB

def compress_and_upload_file(file_path, command_id):
    base_name = os.path.basename(file_path)
    chunk_number = 0
    chunk_urls = []
    file_id = str(uuid.uuid4())  # Generate a unique ID for this file

    # Create an initial entry in the database
    with_retries(lambda: supabase.table("file_chunks").insert({
        "file_id": file_id,
        "file_name": base_name,
        "chunk_urls": [],
        "total_chunks": 0,
        "status": "in_progress"
    }).execute())

    with open(file_path, 'rb') as input_file:
        lzc = lzma.LZMACompressor()
        file_size = os.path.getsize(file_path)
        bytes_processed = 0
        
        while True:
            chunk_data = input_file.read(CHUNK_SIZE)
            if not chunk_data:
                break
            
            compressed_chunk = lzc.compress(chunk_data)
            if compressed_chunk:
                chunk_name = f"chunks/{file_id}/{base_name}_chunk{chunk_number}.xz"
                
                # Upload the compressed chunk to Supabase
                response = with_retries(lambda: supabase.storage.from_(bucket_name).upload(
                    chunk_name, compressed_chunk, file_options={"content_type": "application/x-xz"}
                ))
                
                if response.status_code in [200, 201]:
                    chunk_url = get_public_url(bucket_name, chunk_name)
                    chunk_urls.append(chunk_url)
                    chunk_number += 1
                    # Update the database entry after each successful chunk upload
                    with_retries(lambda: supabase.table("file_chunks").update({
                        "chunk_urls": chunk_urls,
                        "total_chunks": chunk_number
                    }).eq("file_id", file_id).execute())
                else:
                    raise Exception(f"Failed to upload chunk {chunk_number}")

            bytes_processed += len(chunk_data)

    # Upload the final chunk (if any)
    final_chunk = lzc.flush()
    if final_chunk:
        chunk_name = f"chunks/{file_id}/{base_name}_chunk{chunk_number}.xz"
        response = with_retries(lambda: supabase.storage.from_(bucket_name).upload(
            chunk_name, final_chunk, file_options={"content_type": "application/x-xz"}
        ))
        
        if response.status_code in [200, 201]:
            chunk_url = get_public_url(bucket_name, chunk_name)
            chunk_urls.append(chunk_url)
            chunk_number += 1
            # Update the database with the final chunk
            with_retries(lambda: supabase.table("file_chunks").update({
                "chunk_urls": chunk_urls,
                "total_chunks": chunk_number,
                "status": "completed"
            }).eq("file_id", file_id).execute())
        else:
            raise Exception(f"Failed to upload final chunk")

    return chunk_urls

def start_compression_thread(file_path, command_id, update_func, agent_id, ip, os_info, username, encryption_key):
    def run_compression():
        try:
            chunk_urls = compress_and_upload_file(file_path, command_id)
            output = f"File {os.path.basename(file_path)} compressed and uploaded successfully in {len(chunk_urls)} chunks"
            status = 'Completed'
        except Exception as e:
            output = str(e)
            status = 'Failed'
        
        # Use the passed function to update the command status
        update_func(command_id, status, output, agent_id, ip, os_info, username, encryption_key)

    thread = threading.Thread(target=run_compression)
    thread.start()
    return thread