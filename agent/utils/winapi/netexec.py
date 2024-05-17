import clr  # pythonnet module
import requests
from io import BytesIO
from System.Reflection import Assembly, BindingFlags
from System import Array, Byte, String
from System.IO import StringWriter, TextWriter
from System import Console
from ..config import SUPABASE_KEY

def load_dotnet_assembly(file_url, arguments):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    # Download the .NET assembly
    response = requests.get(file_url, headers=headers)
    response.raise_for_status()

    # Load the assembly into memory without writing to disk
    assembly_data = response.content
    assembly_stream = BytesIO(assembly_data)
    assembly_bytes = Array[Byte](list(assembly_stream.getvalue()))
    assembly = Assembly.Load(assembly_bytes)

    # Find the entry point (Main method) dynamically
    entry_point = None
    for type in assembly.GetTypes():
        method_info = type.GetMethod("Main", BindingFlags.Public | BindingFlags.Static)
        if method_info:
            entry_point = method_info
            break

    if not entry_point:
        raise Exception("No suitable entry point (Main method) found in the assembly.")

    # Prepare arguments for the entry point
    if entry_point.GetParameters():
        args = Array[String](arguments.split())
    else:
        args = None

    # Capture the standard output and standard error
    stdout = StringWriter()
    stderr = StringWriter()
    original_stdout = Console.Out
    original_stderr = Console.Error

    try:
        Console.SetOut(stdout)
        Console.SetError(stderr)
        entry_point.Invoke(None, [args])
    finally:
        Console.SetOut(original_stdout)
        Console.SetError(original_stderr)

    # Return the captured output
    output = stdout.ToString()
    error = stderr.ToString()

    if error:
        return output, error
    return output, None
