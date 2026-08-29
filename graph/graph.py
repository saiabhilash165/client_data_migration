import os
import webbrowser

from graph.build_graph import build_migration_graph


OUTPUT_DIR = "outputs"
MERMAID_FILE = os.path.join(OUTPUT_DIR, "migration_graph.mmd")
HTML_FILE = os.path.join(OUTPUT_DIR, "migration_graph.html")
PNG_FILE = os.path.join(OUTPUT_DIR, "migration_graph.png")


def save_mermaid_file(mermaid_text):
    with open(MERMAID_FILE, "w", encoding="utf-8") as file:
        file.write(mermaid_text)


def save_html_file(mermaid_text):
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Migration Graph</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <h2>Client Data Migration Graph</h2>

    <div class="mermaid">
{mermaid_text}
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: "default",
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
    </script>
</body>
</html>
"""

    with open(HTML_FILE, "w", encoding="utf-8") as file:
        file.write(html_content)


def save_png_file(compiled_graph):
    try:
        png_bytes = compiled_graph.get_graph().draw_mermaid_png()

        with open(PNG_FILE, "wb") as file:
            file.write(png_bytes)

        print(f"PNG graph saved to: {PNG_FILE}")

    except Exception as error:
        print("Could not generate PNG graph.")
        print("Reason:", error)
        print("HTML graph is still generated and can be viewed in browser.")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    compiled_graph = build_migration_graph()

    mermaid_text = compiled_graph.get_graph().draw_mermaid()

    print("\nMermaid Graph:")
    print(mermaid_text)

    save_mermaid_file(mermaid_text)
    save_html_file(mermaid_text)
    save_png_file(compiled_graph)

    print("\nGraph files generated:")
    print(f"- {MERMAID_FILE}")
    print(f"- {HTML_FILE}")
    print(f"- {PNG_FILE}")

    html_path = os.path.abspath(HTML_FILE)

    print("\nOpening graph in browser...")
    webbrowser.open(f"file:///{html_path}")


if __name__ == "__main__":
    main()