import ast

def extract_signatures(file_path):
    """
    Extract class and function signatures from a Python file.

    Args:
        file_path (str): Path to the Python file to be analyzed.

    Returns:
        list: A list of strings representing class and function signatures.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        source_code = file.read()

    tree = ast.parse(source_code)
    signatures = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Extract class signature
            signatures.append(f"class {node.name}:")

        elif isinstance(node, ast.FunctionDef):
            # Extract function signature
            args = [arg.arg for arg in node.args.args]
            args_str = ", ".join(args)
            signatures.append(f"def {node.name}({args_str}):")

    return signatures

if __name__ == "__main__":
    # Replace 'your_file.py' with the path to the Python file you want to analyze
    file_path = 'image_container.py'
    try:
        signatures = extract_signatures(file_path)
        print("\n".join(signatures))
    except Exception as e:
        print(f"Error: {e}")
