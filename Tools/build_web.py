import os
import requests
import until


def render_markdown_to_html(md_content, github_token=None) -> str | None:
    github_api_url = "https://api.github.com/markdown"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    payload = {"text": md_content, "mode": "gfm"}

    response = requests.post(github_api_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.text
    else:
        print(f"[Web] GitHub API request failed, status code: {response.status_code}")
        print(f"[Web] Error message: {response.text}")
        return None


def convert_markdown_to_html(md_file_path, output_html_path, github_token=None) -> bool:
    with open(md_file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = render_markdown_to_html(md_content, github_token)

    if html_content is None:
        print(f"[Web] Failed to convert: {md_file_path}")
        return False

    template_path = os.path.join(os.path.dirname(__file__), "web_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    full_html = template.replace("{{CONTENT}}", html_content)

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    return True


def convert_all_markdown_files(directory, github_token=None) -> None:
    """Recursively convert all Markdown files to HTML in a directory and delete original MD files."""
    print("[Web] Start converting Markdown files to HTML...")
    converted_count = 0
    failed_count = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                md_path = os.path.join(root, file)
                html_path = md_path[:-3] + ".html"

                print(f"[Web] Converting: {md_path}")
                if convert_markdown_to_html(md_path, html_path, github_token):
                    converted_count += 1
                    os.remove(md_path)
                    print(f"[Web] Generated: {html_path}, deleted: {md_path}")
                else:
                    failed_count += 1
                    print(f"[Web] Failed: {md_path}")

    print(
        f"[Web] Conversion complete: {converted_count} succeeded, {failed_count} failed"
    )
    print("[Web] End converting Markdown files to HTML")


def generate_file_tree_html(public_dir, base_url=".", rule_extensions=None) -> str:
    """Generate HTML file tree.

    Args:
        public_dir: Directory to scan
        base_url: Base URL for file links
        rule_extensions: List of file extensions to count rules for (e.g., ['.conf', '.json'])
    """
    if rule_extensions is None:
        rule_extensions = [".conf", ".json"]

    def get_file_size(filepath):
        size = os.path.getsize(filepath)
        for unit in ["B", "KiB", "MiB", "GiB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TiB"

    def count_rules(filepath):
        """Count non-comment, non-empty lines in a file.

        For .conf files: counts non-comment, non-empty lines
        For .json files (sing-box format): counts total rule entries across all rule types
        """
        try:
            file_ext = os.path.splitext(filepath)[1].lower()

            if file_ext == ".json":
                # Handle sing-box JSON format
                import json

                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    count = 0
                    # sing-box format: {"version": 2, "rules": [{"domain": [...], "domain_suffix": [...], ...}]}
                    if "rules" in data and isinstance(data["rules"], list):
                        for rule_set in data["rules"]:
                            if isinstance(rule_set, dict):
                                # Count all entries in all rule type arrays
                                for _, values in rule_set.items():
                                    if isinstance(values, list):
                                        count += len(values)
                    return count
            else:
                # Handle .conf and other text-based formats
                with open(filepath, "r", encoding="utf-8") as f:
                    count = 0
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comment lines
                        if line and not line.startswith("#"):
                            count += 1
                    return count
        except Exception as e:
            print(f"Error counting rules in {filepath}: {e}")
            return 0

    def scan_directory(dir_path, relative_path="") -> list[str]:
        items = []
        try:
            entries = sorted(os.listdir(dir_path))
            for entry in entries:
                if entry.startswith(".") or entry == "index.html":
                    continue

                full_path = os.path.join(dir_path, entry)
                rel_path = (
                    os.path.join(relative_path, entry) if relative_path else entry
                )

                if os.path.isdir(full_path):
                    items.append(
                        {
                            "type": "dir",
                            "name": entry,
                            "path": rel_path,
                            "items": scan_directory(full_path, rel_path),
                        }
                    )
                else:
                    file_info = {
                        "type": "file",
                        "name": entry,
                        "path": rel_path,
                        "size": get_file_size(full_path),
                    }
                    # Add rule count for files in List directory with supported extensions
                    if rel_path.startswith("List" + os.sep) or rel_path.startswith(
                        "List/"
                    ):
                        file_ext = os.path.splitext(entry)[1].lower()
                        if file_ext in rule_extensions:
                            file_info["rules"] = count_rules(full_path)
                    items.append(file_info)
        except Exception as e:
            print(f"Error scanning {dir_path}: {e}")

        # Sort items: directories first, then files
        items.sort(key=lambda x: (x["type"] != "dir", x["name"]))
        return items

    def get_default_expand_state(path_parts, level) -> bool:
        """
        Config: expanded
        List: level 0 expanded, level 1 collapsed
        Mock: collapsed
        Module: level 0 expanded, level 1 collapsed
        Script: collapsed
        """
        if not path_parts:
            return True

        top_dir = path_parts[0]

        if top_dir == "Config":
            return True  # Config expanded
        elif top_dir == "List":
            return level == 0  # List only expanded at level 0
        elif top_dir == "Mock":
            return False  # Mock collapsed
        elif top_dir == "Module":
            return level == 0  # Module only expanded at level 0
        elif top_dir == "Script":
            return False  # Script collapsed
        else:
            return True

    def generate_html_tree(items, level=0, path_parts=[]) -> list[str]:
        html_lines = []
        html_lines.append('<ul class="file-tree">')

        for item in items:
            if item["type"] == "dir":
                current_path_parts = path_parts + [item["name"]]
                dir_id = f"dir-{item['path'].replace(os.sep, '-').replace('.', '-')}"

                is_expanded = get_default_expand_state(current_path_parts, level)

                expand_class = "expanded" if is_expanded else ""

                html_lines.append(f'<li class="folder {expand_class}">')
                html_lines.append(
                    f'<span class="folder-name" onclick="toggleFolder(\'{dir_id}\')">'
                )
                html_lines.append(
                    f'<span class="folder-icon">📁</span> <strong>{item["name"]}/</strong>'
                )
                html_lines.append("</span>")
                html_lines.append(f'<div id="{dir_id}" class="folder-content">')
                html_lines.extend(
                    generate_html_tree(item["items"], level + 1, current_path_parts)
                )
                html_lines.append("</div>")
                html_lines.append("</li>")
            else:
                file_url = f"{base_url}/{item['path'].replace(os.sep, '/')}"
                html_lines.append('<li class="file">')
                html_lines.append(f'<span class="file-icon">📄</span> ')
                html_lines.append(f'<a href="{file_url}">{item["name"]}</a> ')
                html_lines.append(f'<span class="file-info">')
                html_lines.append(f'<code class="file-size">{item["size"]}</code>')
                # Add rule count badge if present
                if "rules" in item:
                    html_lines.append(
                        f'<code class="rule-count">{item["rules"]} rules</code>'
                    )
                html_lines.append(f"</span>")
                html_lines.append("</li>")

        html_lines.append("</ul>")
        return html_lines

    file_tree = scan_directory(public_dir)

    html_content = "\n".join(generate_html_tree(file_tree))

    return html_content


def build_file_list_page(
    public_dir, output_path, base_url=".", github_token=None, rule_extensions=None
) -> None:
    """Build the file list page.

    Args:
        public_dir: Directory to scan
        output_path: Output HTML file path
        base_url: Base URL for file links
        github_token: GitHub token for API requests
        rule_extensions: List of file extensions to count rules for
    """
    print("[Web] Start building file list page...")

    template_path = os.path.join(os.path.dirname(__file__), "web_index_template.md")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    update_time = until.now_cn_iso8601()

    md_content = template_content.replace("{{UPDATE_TIME}}", update_time)

    html_content = render_markdown_to_html(md_content, github_token)

    if html_content is None:
        print("[Web] Failed to build file list page")
        return

    file_tree_html = generate_file_tree_html(public_dir, base_url, rule_extensions)
    html_content = html_content.replace("{{FILE_TREE}}", file_tree_html)

    # Use web_index_template.html (special template for index page)
    html_template_path = os.path.join(
        os.path.dirname(__file__), "web_index_template.html"
    )
    with open(html_template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    full_html = html_template.replace("{{CONTENT}}", html_content)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as html_file:
        html_file.write(full_html)

    print(f"[Web] File list page generated: {output_path}")
    print("[Web] End building file list page")


if __name__ == "__main__":
    import config

    build_file_list_page(
        config.OUT_DIR,
        os.path.join(config.OUT_DIR, "index.html"),
        github_token=config.GITHUB_TOKEN,
        rule_extensions=config.WEB_RULE_EXTENSIONS,
    )
