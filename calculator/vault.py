class Vault:
    def __init__(self):
        self.secret_files = {}
        self.current_file = None
    
    def add_file(self, file_name, content):
        self.secret_files[file_name] = content
    
    def browse_files(self):
        if not self.secret_files:
            print("No secret files found.")
            return []
        print("\nSecret Files:")
        for file_name in self.secret_files:
            print(f"- {file_name}")
        return list(self.secret_files.keys())
    
    def get_file_content(self, file_name):
        return self.secret_files.get(file_name, "File not found.")
    
    def open_vault(self, sequence):
        if sequence.endswith('+=+'):
            return True
        else:
            return False
