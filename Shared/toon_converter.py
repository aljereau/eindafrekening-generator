import json

class ToonConverter:
    """
    Converter for TOON (Token-Oriented Object Notation) format.
    Optimizes token usage for LLMs by removing redundant syntax (braces, quotes, commas).
    """

    @staticmethod
    def to_toon(data, indent_level=0):
        """
        Convert a dictionary or list to TOON format string.
        """
        indent = "  " * indent_level
        output = []

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    output.append(f"{indent}{key}")
                    output.append(ToonConverter.to_toon(value, indent_level + 1))
                else:
                    # Simple key-value pair
                    # Check if value needs quoting (e.g. contains spaces but isn't a sentence)
                    # For simplicity in this version, we just print str(value)
                    # A more robust version might handle multi-line strings specifically
                    val_str = str(value)
                    output.append(f"{indent}{key} {val_str}")
        
        elif isinstance(data, list):
            # Check if it's a list of dictionaries (common case)
            if data and isinstance(data[0], dict):
                # For lists of objects, we can just list them
                # Optionally we could use a table format, but for now we just iterate
                for item in data:
                    output.append(f"{indent}-")
                    output.append(ToonConverter.to_toon(item, indent_level + 1))
            else:
                # Simple list
                for item in data:
                    output.append(f"{indent}- {item}")
        
        else:
            # Primitive value
            return f"{indent}{data}"

        return "\n".join(output)

    @staticmethod
    def convert(data):
        """Public entry point"""
        return ToonConverter.to_toon(data)
