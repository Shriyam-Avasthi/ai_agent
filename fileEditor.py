import os


class FileEditor:
    def _read_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, file_path, content):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def apply_search_replace(self, file_path, search_text, replace_text):
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist."

        content = self._read_file(file_path)

        content = content.replace("\r\n", "\n")
        search_text = search_text.replace("\r\n", "\n")
        replace_text = replace_text.replace("\r\n", "\n")

        if content.count(search_text) == 1:
            new_content = content.replace(search_text, replace_text)
            self._write_file(file_path, new_content)
            return f"Success: Replaced perfectly."

        elif content.count(search_text) > 1:
            return "Error: Search block is not unique. Please include more surrounding context."

        return self._apply_fuzzy_indent_patch(
            file_path, content, search_text, replace_text
        )

    def _apply_fuzzy_indent_patch(self, file_path, content, search_text, replace_text):
        content_lines = content.splitlines()
        search_lines = search_text.splitlines()

        if not search_lines:
            return "Error: Search block is empty."

        stripped_search = [line.lstrip() for line in search_lines]

        match_index = -1
        match_indentation = ""

        for i in range(len(content_lines) - len(search_lines) + 1):
            window = content_lines[i : i + len(search_lines)]
            stripped_window = [line.lstrip() for line in window]

            if stripped_window == stripped_search:
                match_index = i
                # Extract the base indentation from the first matched line in the file
                original_line = window[0]
                stripped_line = stripped_window[0]
                match_indentation = original_line[
                    : len(original_line) - len(stripped_line)
                ]
                break

        if match_index == -1:
            return (
                "Error: SEARCH block not found exactly in file. "
                "Ensure you copy-paste the exact lines you want to replace without modifying them."
            )

        replace_lines = replace_text.splitlines()
        if replace_lines and replace_lines[0].lstrip():
            llm_base_indent = replace_lines[0][
                : len(replace_lines[0]) - len(replace_lines[0].lstrip())
            ]
        else:
            llm_base_indent = ""

        aligned_replace_lines = []
        for line in replace_lines:
            if line.startswith(llm_base_indent):
                aligned_line = match_indentation + line[len(llm_base_indent) :]
                aligned_replace_lines.append(aligned_line)
            else:
                aligned_replace_lines.append(line)

        new_content_lines = (
            content_lines[:match_index]
            + aligned_replace_lines
            + content_lines[match_index + len(search_lines) :]
        )

        self._write_file(file_path, "\n".join(new_content_lines) + "\n")
        return "Success: Replaced using auto-aligned indentation."


if __name__ == "__main__":
    editor = FileEditor()
    editor.apply_search_replace(
        "main.py", "def foo():\nprint('a')", "def foo():\nprint('b')"
    )
