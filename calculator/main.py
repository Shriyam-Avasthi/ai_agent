import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ast
import operator as op
import json
from datetime import datetime
from pathlib import Path

class Vault:
    def __init__(self, vault_dir="secret_vault"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(exist_ok=True)
        self.index_file = self.vault_dir / "index.txt"
        
        # Initialize vault with default message if it doesn't exist
        if not self.index_file.exists():
            self.index_file.write_text("This is the secret vault.\n")
    
    def add_file(self, file_name, content):
        # Sanitize filename
        safe_name = "".join(c for c in file_name if c.isalnum() or c in "._-")
        if not safe_name:
            safe_name = f"secret_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        file_path = self.vault_dir / safe_name
        file_path.write_text(content)
        
        # Update index
        with self.index_file.open("a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {safe_name}\n")
        
        return safe_name
    
    def browse_files(self):
        files = []
        for file_path in self.vault_dir.iterdir():
            if file_path.is_file() and file_path != self.index_file:
                files.append(file_path.name)
        return sorted(files)
    
    def get_file_content(self, file_name):
        file_path = self.vault_dir / file_name
        if file_path.exists() and file_path.is_file():
            return file_path.read_text()
        return None
    
    def delete_file(self, file_name):
        file_path = self.vault_dir / file_name
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False

# Supported operators for the safe calculator
OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg
}

def safe_eval(expr):
    """
    Safely evaluate a mathematical expression.
    """
    try:
        node = ast.parse(expr, mode='eval').body
        return _eval_node(node)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")

def _eval_node(node):
    if isinstance(node, ast.Constant): # Python 3.8+
        return node.value
    elif isinstance(node, ast.Num): # Python < 3.8
        return node.n
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise TypeError(f"Unsupported operator: {op_type}")
        return OPERATORS[op_type](_eval_node(node.left), _eval_node(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise TypeError(f"Unsupported operator: {op_type}")
        return OPERATORS[op_type](_eval_node(node.operand))
    else:
        raise TypeError(f"Unsupported expression component: {type(node)}")

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Calculator")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        self.bg_color = '#2c3e50'
        self.display_bg = '#34495e'
        self.btn_bg = '#3498db'
        self.btn_fg = '#ecf0f1'
        self.op_bg = '#e74c3c'
        self.num_bg = '#95a5a6'
        
        self.root.configure(bg=self.bg_color)
        
        # Calculator state
        self.current_input = ""
        self.history = []
        
        # Vault state
        self.vault = Vault()
        self.vault_mode = False
        self.sequence = ""
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Display frame
        display_frame = tk.Frame(main_frame, bg=self.display_bg, bd=2, relief='sunken')
        display_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        # History display
        self.history_text = tk.Text(
            display_frame, 
            height=2, 
            bg=self.display_bg, 
            fg=self.btn_fg, 
            font=('Courier', 10),
            state='disabled',
            wrap=tk.WORD
        )
        self.history_text.pack(fill=tk.BOTH, padx=5, pady=2)
        
        # Main display
        self.display = tk.Entry(
            display_frame, 
            font=('Arial', 24, 'bold'), 
            borderwidth=0, 
            bg=self.display_bg, 
            fg=self.btn_fg,
            justify='right'
        )
        self.display.pack(fill=tk.BOTH, padx=10, pady=10, ipady=10)
        self.display.bind('<Key>', self.on_key_press)
        self.display.focus_set()
        
        # Button frames
        btn_container = tk.Frame(main_frame, bg=self.bg_color)
        btn_container.pack(fill=tk.BOTH, expand=True)
        
        # Row 0: Clear and Delete
        row0 = tk.Frame(btn_container, bg=self.bg_color)
        row0.pack(fill=tk.BOTH, expand=True)
        
        self.create_button(row0, "C", self.clear_input, self.btn_bg)
        self.create_button(row0, "⌫", self.backspace, self.btn_bg)
        
        # Row 1: 7, 8, 9, /
        row1 = tk.Frame(btn_container, bg=self.bg_color)
        row1.pack(fill=tk.BOTH, expand=True)
        
        self.create_button(row1, "7", lambda: self.add_to_input('7'), self.num_bg)
        self.create_button(row1, "8", lambda: self.add_to_input('8'), self.num_bg)
        self.create_button(row1, "9", lambda: self.add_to_input('9'), self.num_bg)
        self.create_button(row1, "÷", lambda: self.add_to_input('/'), self.op_bg)
        
        # Row 2: 4, 5, 6, *
        row2 = tk.Frame(btn_container, bg=self.bg_color)
        row2.pack(fill=tk.BOTH, expand=True)
        
        self.create_button(row2, "4", lambda: self.add_to_input('4'), self.num_bg)
        self.create_button(row2, "5", lambda: self.add_to_input('5'), self.num_bg)
        self.create_button(row2, "6", lambda: self.add_to_input('6'), self.num_bg)
        self.create_button(row2, "×", lambda: self.add_to_input('*'), self.op_bg)
        
        # Row 3: 1, 2, 3, -
        row3 = tk.Frame(btn_container, bg=self.bg_color)
        row3.pack(fill=tk.BOTH, expand=True)
        
        self.create_button(row3, "1", lambda: self.add_to_input('1'), self.num_bg)
        self.create_button(row3, "2", lambda: self.add_to_input('2'), self.num_bg)
        self.create_button(row3, "3", lambda: self.add_to_input('3'), self.num_bg)
        self.create_button(row3, "-", lambda: self.add_to_input('-'), self.op_bg)
        
        # Row 4: 0, ., =, +
        row4 = tk.Frame(btn_container, bg=self.bg_color)
        row4.pack(fill=tk.BOTH, expand=True)
        
        self.create_button(row4, "0", lambda: self.add_to_input('0'), self.num_bg)
        self.create_button(row4, ".", lambda: self.add_to_input('.'), self.num_bg)
        self.create_button(row4, "=", self.calculate, self.op_bg)
        self.create_button(row4, "+", lambda: self.add_to_input('+'), self.op_bg)
        
        # Row 5: History, Vault
        row5 = tk.Frame(btn_container, bg=self.bg_color)
        row5.pack(fill=tk.BOTH, expand=True)
        
        self.create_button(row5, "History", self.show_history, self.btn_bg)
        self.create_button(row5, "Vault", self.toggle_vault_mode, self.btn_bg)
    
    def create_button(self, parent, text, command, bg_color):
        btn = tk.Button(
            parent, 
            text=text, 
            font=('Arial', 14, 'bold'),
            bg=bg_color,
            fg=self.btn_fg,
            bd=0,
            padx=10,
            pady=10,
            command=command,
            cursor='hand2'
        )
        btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2, pady=2)
        
        # Hover effects
        btn.bind('<Enter>', lambda e: btn.config(bg=self.lighten_color(bg_color)))
        btn.bind('<Leave>', lambda e: btn.config(bg=bg_color))
        
        return btn
    
    def lighten_color(self, color):
        # Convert hex to RGB
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        # Lighten by increasing to 255 with 30% intensity
        r = min(255, int(r + (255 - r) * 0.3))
        g = min(255, int(g + (255 - g) * 0.3))
        b = min(255, int(b + (255 - b) * 0.3))
        
        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def add_to_input(self, value):
        self.current_input += value
        self.update_display()
        
        # Add to sequence for vault access
        self.sequence += value
        if self.sequence.endswith("+=+"):
            self.open_vault()
    
    def clear_input(self):
        self.current_input = ""
        self.update_display()
    
    def backspace(self):
        if self.current_input:
            self.current_input = self.current_input[:-1]
            self.update_display()
    
    def update_display(self):
        self.display.delete(0, tk.END)
        self.display.insert(0, self.current_input)
    
    def calculate(self):
        if not self.current_input:
            return
        
        try:
            result = safe_eval(self.current_input)
            
            # Format result
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            
            # Add to history
            expression = self.current_input
            self.history.append(f"{expression} = {result}")
            if len(self.history) > 50:  # Limit history size
                self.history.pop(0)
            
            # Update display
            self.current_input = str(result)
            self.update_display()
            
            # Update history text
            self.history_text.config(state='normal')
            self.history_text.delete(1.0, tk.END)
            self.history_text.insert(1.0, "\n".join(self.history[-3:]))
            self.history_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid expression: {e}")
    
    def show_history(self):
        if not self.history:
            messagebox.showinfo("History", "No calculations yet.")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("Calculation History")
        history_window.geometry("400x300")
        history_window.configure(bg=self.bg_color)
        
        # History title
        title = tk.Label(
            history_window, 
            text="Calculation History", 
            font=('Arial', 16, 'bold'),
            bg=self.bg_color,
            fg=self.btn_fg
        )
        title.pack(pady=10)
        
        # Scrolled text for history
        history_text = scrolledtext.ScrolledText(
            history_window,
            font=('Courier', 10),
            bg=self.display_bg,
            fg=self.btn_fg,
            wrap=tk.WORD
        )
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add history items
        for item in reversed(self.history):
            history_text.insert(tk.END, item + "\n")
        
        history_text.config(state='disabled')
        
        # Clear history button
        clear_btn = tk.Button(
            history_window,
            text="Clear History",
            bg=self.op_bg,
            fg=self.btn_fg,
            command=lambda: self.clear_history(history_window)
        )
        clear_btn.pack(pady=10)
    
    def clear_history(self, window):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            self.history = []
            self.history_text.config(state='normal')
            self.history_text.delete(1.0, tk.END)
            self.history_text.config(state='disabled')
            window.destroy()
    
    def on_key_press(self, event):
        # Handle keyboard input
        key = event.char
        
        # Numbers and operators
        if key in '0123456789+-*/.':
            self.add_to_input(key)
            return "break"  # Prevent default behavior
        
        # Enter key for equals
        if event.keysym == 'Return':
            self.calculate()
            return "break"
        
        # Backspace
        if event.keysym == 'BackSpace':
            self.backspace()
            return "break"
        
        # Escape key to clear
        if event.keysym == 'Escape':
            self.clear_input()
            return "break"
        
        # Other keys - add to sequence for vault access
        if event.char or event.keysym in ['plus', 'equal']:
            # Convert keysym to character
            if event.keysym == 'plus':
                key = '+'
            elif event.keysym == 'equal':
                key = '='
            
            self.sequence += key
            if self.sequence.endswith("+=+"):
                self.open_vault()
    
    def toggle_vault_mode(self):
        if self.vault_mode:
            self.close_vault()
        else:
            self.open_vault()
    
    def open_vault(self):
        self.vault_mode = True
        self.sequence = ""  # Reset sequence
        
        # Create vault window
        self.vault_window = tk.Toplevel(self.root)
        self.vault_window.title("Secret Vault")
        self.vault_window.geometry("500x400")
        self.vault_window.configure(bg=self.bg_color)
        self.vault_window.protocol("WM_DELETE_WINDOW", self.close_vault)  # Handle window close
        
        # Vault title
        title = tk.Label(
            self.vault_window, 
            text="🔒 Secret Vault 🔒", 
            font=('Arial', 18, 'bold'),
            bg=self.bg_color,
            fg=self.btn_fg
        )
        title.pack(pady=10)
        
        # Info text
        info = tk.Label(
            self.vault_window,
            text="Store your secrets safely",
            font=('Arial', 10),
            bg=self.bg_color,
            fg=self.btn_fg
        )
        info.pack(pady=5)
        
        # File list frame
        list_frame = tk.Frame(self.vault_window, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Files list
        files_label = tk.Label(
            list_frame,
            text="Stored Secrets:",
            font=('Arial', 12, 'bold'),
            bg=self.bg_color,
            fg=self.btn_fg
        )
        files_label.pack(anchor='w')
        
        # Create frame for listbox and scrollbar
        listbox_frame = tk.Frame(list_frame, bg=self.bg_color)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Listbox for files
        self.file_listbox = tk.Listbox(
            listbox_frame,
            font=('Courier', 10),
            bg=self.display_bg,
            fg=self.btn_fg,
            selectbackground=self.op_bg
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for listbox
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Connect listbox and scrollbar
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Update file list
        self.refresh_file_list()
        
        # Buttons frame
        btn_frame = tk.Frame(self.vault_window, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Add button
        add_btn = tk.Button(
            btn_frame,
            text="Add Secret",
            bg=self.btn_bg,
            fg=self.btn_fg,
            command=self.add_secret
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # View button
        view_btn = tk.Button(
            btn_frame,
            text="View Secret",
            bg=self.btn_bg,
            fg=self.btn_fg,
            command=self.view_secret
        )
        view_btn.pack(side=tk.LEFT, padx=5)
        
        # Delete button
        delete_btn = tk.Button(
            btn_frame,
            text="Delete Secret",
            bg=self.op_bg,
            fg=self.btn_fg,
            command=self.delete_secret
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(
            btn_frame,
            text="Close Vault",
            bg=self.op_bg,
            fg=self.btn_fg,
            command=self.close_vault
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Bind double-click to view
        self.file_listbox.bind('<Double-1>', lambda e: self.view_secret())
        
    def refresh_file_list(self):
        # Clear current list
        self.file_listbox.delete(0, tk.END)
        
        # Add index file first
        self.file_listbox.insert(tk.END, "index.txt")
        
        # Add all files
        files = self.vault.browse_files()
        for file in sorted(files):
            if file != "index.txt":  # Don't duplicate index
                self.file_listbox.insert(tk.END, file)
        
    def add_secret(self):
        # Create add secret dialog
        add_window = tk.Toplevel(self.vault_window)
        add_window.title("Add Secret")
        add_window.geometry("400x300")
        add_window.configure(bg=self.bg_color)
        
        # File name
        tk.Label(
            add_window,
            text="File Name:",
            font=('Arial', 12),
            bg=self.bg_color,
            fg=self.btn_fg
        ).pack(pady=(10, 0))
        
        name_entry = tk.Entry(
            add_window,
            font=('Arial', 12),
            bg=self.display_bg,
            fg=self.btn_fg
        )
        name_entry.pack(fill=tk.X, padx=20, pady=5)
        
        # Content
        tk.Label(
            add_window,
            text="Secret Content:",
            font=('Arial', 12),
            bg=self.bg_color,
            fg=self.btn_fg
        ).pack(pady=(10, 0))
        
        content_text = scrolledtext.ScrolledText(
            add_window,
            font=('Arial', 10),
            bg=self.display_bg,
            fg=self.btn_fg,
            height=8
        )
        content_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Buttons
        btns_frame = tk.Frame(add_window, bg=self.bg_color)
        btns_frame.pack(pady=10)
        
        def save_secret():
            name = name_entry.get().strip()
            content = content_text.get(1.0, tk.END).strip()
            
            if not name:
                name = f"secret_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            if content:
                filename = self.vault.add_file(name, content)
                messagebox.showinfo("Success", f"Secret saved as {filename}")
                self.refresh_file_list()
                add_window.destroy()
            else:
                messagebox.showwarning("Warning", "Please enter some content")
        
        save_btn = tk.Button(
            btns_frame,
            text="Save",
            bg=self.btn_bg,
            fg=self.btn_fg,
            command=save_secret
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            btns_frame,
            text="Cancel",
            bg=self.op_bg,
            fg=self.btn_fg,
            command=add_window.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def view_secret(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a secret to view")
            return
        
        filename = self.file_listbox.get(selection[0])
        content = self.vault.get_file_content(filename)
        
        if content is None:
            messagebox.showerror("Error", "Could not read the secret")
            return
        
        # Create view window
        view_window = tk.Toplevel(self.vault_window)
        view_window.title(f"Viewing: {filename}")
        view_window.geometry("500x400")
        view_window.configure(bg=self.bg_color)
        
        # Title
        tk.Label(
            view_window,
            text=f"{filename}",
            font=('Arial', 14, 'bold'),
            bg=self.bg_color,
            fg=self.btn_fg
        ).pack(pady=10)
        
        # Content
        content_text = scrolledtext.ScrolledText(
            view_window,
            font=('Courier', 10),
            bg=self.display_bg,
            fg=self.btn_fg
        )
        content_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        content_text.insert(1.0, content)
        content_text.config(state='disabled')
        
        # Close button
        close_btn = tk.Button(
            view_window,
            text="Close",
            bg=self.op_bg,
            fg=self.btn_fg,
            command=view_window.destroy
        )
        close_btn.pack(pady=10)
    
    def delete_secret(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a secret to delete")
            return
        
        filename = self.file_listbox.get(selection[0])
        
        if filename == "index.txt":
            messagebox.showwarning("Warning", "You cannot delete the index file")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{filename}'?"):
            if self.vault.delete_file(filename):
                messagebox.showinfo("Success", f"'{filename}' has been deleted")
                self.refresh_file_list()
            else:
                messagebox.showerror("Error", "Could not delete the file")
    
    def close_vault(self):
        if hasattr(self, 'vault_window'):
            self.vault_window.destroy()
        self.vault_mode = False

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()