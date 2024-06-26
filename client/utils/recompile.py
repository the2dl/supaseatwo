import os
import requests
import lzma
from .database import supabase, SUPABASE_KEY, get_public_url

# ANSI escape codes for colors
GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
RESET = '\033[0m'

def list_compressed_files():
    response = supabase.table("file_chunks").select("file_id", "file_name").execute()
    if response.data:
        return [(item['file_id'], item['file_name']) for item in response.data]
    return []

def recompile_file(file_id, output_path):
    print(f"{YELLOW}Fetching chunk information...{RESET}")
    response = supabase.table("file_chunks").select("*").eq("file_id", file_id).execute()
    if not response.data:
        raise Exception(f"No chunk information found for file ID {file_id}")

    chunk_info = response.data[0]
    chunk_urls = chunk_info["chunk_urls"]
    total_chunks = len(chunk_urls)
    print(f"{YELLOW}Total chunks to process: {total_chunks}{RESET}")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    with lzma.open(output_path, 'wb') as output_file:
        decompressor = lzma.LZMADecompressor()
        for index, chunk_url in enumerate(chunk_urls, 1):
            print(f"{YELLOW}Downloading and processing chunk {index}/{total_chunks}...{RESET}")
            response = requests.get(chunk_url, headers=headers)
            if response.status_code == 200:
                compressed_chunk = response.content
                decompressed_chunk = decompressor.decompress(compressed_chunk)
                output_file.write(decompressed_chunk)
                print(f"{GREEN}Chunk {index}/{total_chunks} processed successfully.{RESET}")
            else:
                raise Exception(f"Failed to download chunk {index}: {chunk_url}")

    print(f"{GREEN}All chunks processed. Finalizing file...{RESET}")

def recompile_compressed_files():
    print(f"\n{GREEN}Recompile Compressed Files:{RESET}")
    compressed_files = list_compressed_files()

    if not compressed_files:
        print(f"{RED}No compressed files available for recompilation.{RESET}")
        return

    for i, (file_id, file_name) in enumerate(compressed_files, 1):
        print(f"{i}. {file_name} (ID: {file_id})")

    choice = input("\nEnter the number of the file you want to recompile (or 'q' to quit): ")

    if choice.lower() == 'q':
        return

    try:
        index = int(choice) - 1
        if 0 <= index < len(compressed_files):
            file_id, file_name = compressed_files[index]
            output_path = input("Enter the output path for the recompiled file: ")

            if os.path.exists(output_path):
                overwrite = input(f"{RED}File already exists. Overwrite? (y/n): {RESET}")
                if overwrite.lower() != 'y':
                    print("Recompilation cancelled.")
                    return

            print(f"{YELLOW}Starting recompilation of {file_name}...{RESET}")
            recompile_file(file_id, output_path)
            print(f"{GREEN}File recompiled successfully: {output_path}{RESET}")
        else:
            print(f"{RED}Invalid choice.{RESET}")
    except ValueError:
        print(f"{RED}Invalid input. Please enter a number.{RESET}")
    except Exception as e:
        print(f"{RED}An error occurred during recompilation: {str(e)}{RESET}")