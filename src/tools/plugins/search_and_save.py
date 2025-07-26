"""
Search and save results tool
"""

from .. import tool
import os


@tool(
    description="Search for content in files and save the results to a file",
    category="combined",
    schema={
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "The keyword to search for in files"
            },
            "output_file": {
                "type": "string",
                "description": "The filename to save the search results to"
            }
        },
        "required": ["keyword", "output_file"]
    }
)
def search_and_save(keyword: str, output_file: str) -> str:
    """Search for a keyword in all files and save results to a file
    
    Args:
        keyword: The keyword to search for in files
        output_file: The filename to save the search results to
    
    Returns:
        Success message with match count
    """
    matches = []
    
    # Search through all files
    for root, _, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if keyword in line:
                            matches.append(f"{file_path}:{i}: {line.strip()}")
            except Exception:
                continue
    
    # Prepare search results
    if matches:
        search_results = f"Search results for '{keyword}':\n\n" + "\n".join(matches)
    else:
        search_results = f"No matches found for '{keyword}'."
    
    # Save results to file
    try:
        with open(output_file, "w") as f:
            f.write(search_results)
        return f"Search completed and results saved to {output_file}. Found {len(matches)} matches."
    except Exception as e:
        return f"Search completed but failed to save results: {e}\n\nResults:\n{search_results[:200]}..."
