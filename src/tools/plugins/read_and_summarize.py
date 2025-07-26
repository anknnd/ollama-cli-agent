"""
Read file and generate summary tool
"""

from .. import tool
from ..shared import generate_content_with_llm


@tool(
    description="Read a file and generate a summary, saving it to another file",
    category="combined",
    schema={
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "The file to read and summarize"
            },
            "output_file": {
                "type": "string",
                "description": "The file to save the summary to"
            }
        },
        "required": ["input_file", "output_file"]
    }
)
def read_and_summarize(input_file: str, output_file: str) -> str:
    """Read a file and generate a summary, saving it to another file
    
    Args:
        input_file: The file to read and summarize
        output_file: The file to save the summary to
    
    Returns:
        Success message
    """
    try:
        # Read the input file
        with open(input_file, "r") as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file {input_file}: {e}"
    
    try:
        # Generate summary using shared LLM function
        prompt = f"Please provide a concise summary of the following content:\n\n{content}"
        summary = generate_content_with_llm(
            prompt,
            "You are a helpful assistant that creates concise summaries."
        )
        
        # Save summary to output file
        with open(output_file, "w") as f:
            f.write(f"Summary of {input_file}:\n\n{summary}")
            
        return f"Read {input_file}, generated summary, and saved to {output_file} successfully."
        
    except Exception as e:
        return f"Error generating or saving summary: {e}"
