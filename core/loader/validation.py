import ast

def validate_python_source(source: str, filename: str = "<module>"):
    ast.parse(source, filename=filename)
    return True
