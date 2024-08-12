"""Creates documentation from a cerberus schema."""

import json
import argparse


def parse_schema(schema, indent=0, is_sub=False):
    """Parses the cerberus schema."""
    rows = []
    max_lengths = {
        "Field Name": 10,
        "Type": 4,
        "Default": 7,
        "Description": 11,
    }  # Default header widths
    # print(schema)
    for key, properties in schema.items():
        field_name = f"{'    ' * indent}{key}"
        if not hasattr(properties, "get"):
            return [], {}
        field_type = properties.get("type", "N/A")
        default_value = json.dumps(
            properties.get("default", "N/A")
        )  # Ensure default values are properly formatted

        # Generate a basic description based on the field type
        description = ""

        if "schema" in properties:
            # Handle nested schemas
            sub_rows, sub_lengths = parse_schema(properties["schema"], indent + 1, True)
            rows.append((field_name, field_type, default_value, "See details below:"))
            rows.extend(sub_rows)
            # Update max lengths from sub-tables
            for key, length in sub_lengths.items():
                max_lengths[key] = max(max_lengths[key], length)
        else:
            rows.append((field_name, field_type, default_value, description))

        # Update maximum lengths for alignment
        max_lengths["Field Name"] = max(max_lengths["Field Name"], len(field_name))
        max_lengths["Type"] = max(max_lengths["Type"], len(field_type))
        max_lengths["Default"] = max(max_lengths["Default"], len(default_value))
        max_lengths["Description"] = max(max_lengths["Description"], len(description))

    if not is_sub:  # Only output headers and format for the top-level table
        headers = ["Field Name", "Type", "Default", "Description"]
        header_row = "| " + " | ".join(h.ljust(max_lengths[h]) for h in headers) + " |"
        separator_row = "|-" + "-|-".join("-" * max_lengths[h] for h in headers) + "-|"
        formatted_rows = [header_row, separator_row]
        formatted_rows += [
            "| "
            + " | ".join(
                str(field).ljust(max_lengths[h]) for field, h in zip(row, headers)
            )
            + " |"
            for row in rows
        ]
        return formatted_rows
    else:
        return rows, max_lengths


def main():
    """Creates documentation from a cerberus schemea."""
    # Set up argparse to handle command line arguments
    parser = argparse.ArgumentParser(
        description="Parse a Cerberus schema JSON file into a Markdown table."
    )
    parser.add_argument(
        "filename",
        type=str,
        help="The path to the JSON file containing the Cerberus schema.",
    )

    # Parse the arguments from the command line
    args = parser.parse_args()

    # Read and load the JSON file
    try:
        with open(args.filename) as file:
            schema = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {args.filename} was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file {args.filename} is not a valid JSON file.")
        return

    # Assuming parse_schema is a function defined to take a schema and return Markdown
    markdown_output = parse_schema(schema)
    for line in markdown_output:
        print(line)


if __name__ == "__main__":
    main()
