from functions.get_file_content import get_file_content
from functions.get_files_info import get_files_info
from functions.run_python_file import run_python_file
from functions.write_file import write_file


def main():
    working_dir = "calculator"
    # root_contents = get_files_info(working_dir, ".")
    # print(root_contents)
    # pkg_contents = get_files_info(working_dir, "pkg")
    # print(pkg_contents)
    # pkg_contents = get_files_info(working_dir, "../")
    # print(pkg_contents)
    #
    # print(get_file_content(working_dir, "main.py"))
    # print(get_file_content(working_dir, "/bin/cat"))
    # print(get_file_content(working_dir, "pkg/doesnotexist.py"))
    # print(get_file_content(working_dir, "pkg/calculator.py"))
    #
    # lorem = get_file_content(working_dir, "lorem.txt")
    # print(write_file(working_dir, "lorem.txt", "HELLO"))
    # print(write_file(working_dir, "lorem2.txt", lorem))
    # print(write_file(working_dir, "/tmp/temp.txt", lorem))

    print(run_python_file(working_dir, "main.py", ["3 + 5"]))
    print(run_python_file(working_dir, "tests.py"))
    print(run_python_file(working_dir, "../main.py"))
    print(run_python_file(working_dir, "nonexistent.py"))

main()
