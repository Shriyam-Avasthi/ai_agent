# UX improvements for the calculator

class Calculator:
    def __init__(self):
        self.vault = SecretVault()

    def press_button(self, button):
        if button == '+':
            # Open the secret vault if the sequence is correct
            if self.vault.open_vault('+=+'):
                print('Secret vault opened!')
                self.vault.browse_secret_files()
            else:
                print('Invalid sequence. Try again.')
        elif button == '=':
            # Add a new secret file
            file_name = input('Enter the file name: ')
            content = input('Enter the file content: ')
            self.vault.add_secret_file(file_name, content)
            print('File added successfully!')
        else:
            print('Invalid button press. Try again.')