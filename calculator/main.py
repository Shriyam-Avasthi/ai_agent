from vault import Vault

vault = Vault()
sequence = ''

print("Welcome to the Secret Calculator!")
print("Enter expressions to calculate or a secret sequence to enter the vault.")

while True:
    user_input = input('\n> ')
    if not user_input:
        continue
        
    sequence += user_input
    
    if vault.open_vault(sequence):
        print('\n*** Secret Vault Opened! ***')
        while True:
            print('\nVault Menu:')
            print('1. Add secret file')
            print('2. Browse and read files')
            print('3. Exit Vault')
            choice = input('Choose an option: ')
            
            if choice == '1':
                file_name = input('Enter file name: ')
                content = input('Enter content: ')
                vault.add_file(file_name, content)
                print('File saved successfully.')
            elif choice == '2':
                files = vault.browse_files()
                if files:
                    read_choice = input('Enter file name to read (or press Enter to go back): ')
                    if read_choice:
                        print(f'\n--- {read_choice} ---\n{vault.get_file_content(read_choice)}\n---')
            elif choice == '3':
                print('Closing vault...')
                break
            else:
                print('Invalid choice.')
        sequence = ''
    else:
        # Perform calculator operations
        try:
            # We use eval carefully here for a simple calculator
            # In a real app, we'd use a safer parser
            result = eval(user_input)
            print(f"Result: {result}")
            # Reset sequence if the input was a valid calculation and didn't start a potential secret
            # But for simplicity, we only reset sequence when the vault is opened or’
            # we can keep it and only check for the suffix.
        except Exception as e:
            print(f"Error: {e}")
            # If it's not a valid expression, it might be part of the secret sequence.
            # We don't clear sequence here.
