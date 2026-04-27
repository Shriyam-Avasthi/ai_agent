import os

class SecretVault:
    def __init__(self):
        self.secret_code = '+=+'
        self.secret_files = []
        self.current_file = None

    def add_secret_file(self, file_name, content):
        with open(f'./secret_vault/{file_name}', 'w') as f:
            f.write(content)
        self.secret_files.append(file_name)

    def browse_secret_files(self):
        for i, file in enumerate(self.secret_files):
            print(f'{i+1}. {file}')

    def open_vault(self, code):
        if code == self.secret_code:
            return True
        else:
            return False
