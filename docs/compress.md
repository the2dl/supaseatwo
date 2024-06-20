# File Compression Utility

This module provides functions to compress and chunk files, as well as to merge chunked files back into a single file.

## Functions:
* `ensure_output_directory`: Ensures that the output directory for chunked files exists.
* `chunk_file`: Chunks a file into smaller pieces.
* `merge_chunks`: Merges chunk files into a single file.
* `compress_file`: Compresses a file using LZMA, chunks the compressed file, and merges the chunks back into a final compressed file.