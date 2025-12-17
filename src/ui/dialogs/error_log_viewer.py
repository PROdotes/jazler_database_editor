from tkinter import Toplevel, Frame, Text, Label, Button, Scrollbar, END, BOTH, RIGHT, Y, X, LEFT, VERTICAL
from tkinter import ttk
from src.ui.theme import theme
from src.utils.error_handler import ErrorHandler

class ErrorLogViewer(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Error Log Viewer")
        self.geometry("900x600")
        self.configure(bg=theme.BG_DARK)
        self.current_errors = []
        
        # UI Setup
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        # Top Frame: Toolbar
        toolbar = Frame(self, bg=theme.BG_DARK)
        toolbar.pack(fill=X, padx=10, pady=10)
        
        self.btn_refresh = Button(toolbar, text="Refresh", command=self._load_data, 
                                 bg=theme.BTN_ACTIVE, fg=theme.FG_WHITE, relief="flat", padx=10)
        self.btn_refresh.pack(side=LEFT, padx=(0, 10))
        
        # Main Content: Database style list (Treeview)
        # Using a paned window to split List and Details
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Frame for Treeview
        tree_frame = Frame(paned, bg=theme.BG_DARK)
        paned.add(tree_frame, weight=3)
        
        columns = ("Time", "Level", "Context", "Message")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        # Scrollbar
        vpath = Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vpath.set)
        
        self.tree.heading("Time", text="Time", anchor="w")
        self.tree.heading("Level", text="Level", anchor="w")
        self.tree.heading("Context", text="Context", anchor="w")
        self.tree.heading("Message", text="Message", anchor="w")
        
        self.tree.column("Time", width=150, minwidth=120)
        self.tree.column("Level", width=80, minwidth=60)
        self.tree.column("Context", width=150, minwidth=100)
        self.tree.column("Message", width=400, minwidth=200)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vpath.pack(side=RIGHT, fill=Y)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Frame for Details
        detail_frame = Frame(paned, bg=theme.BG_DARK)
        paned.add(detail_frame, weight=2)
        
        Label(detail_frame, text="Error Details / Stack Trace:", bg=theme.BG_DARK, fg=theme.FG_WHITE).pack(anchor="w", pady=(5, 0))
        
        self.txt_details = Text(detail_frame, bg=theme.BG_LIGHTER, fg=theme.FG_WHITE, 
                               font=("Consolas", 10), relief="flat")
        self.txt_details.pack(fill=BOTH, expand=True, pady=5)
        
        # Style Treeview
        style = ttk.Style()
        style.configure("Treeview", background="#2b2b2b", foreground="#ffffff", fieldbackground="#2b2b2b", rowheight=25)
        style.map("Treeview", background=[("selected", theme.BTN_ACTIVE)])
        
        # Tags for colors
        self.tree.tag_configure("CRITICAL", foreground="#ff4d4d") # Red
        self.tree.tag_configure("ERROR", foreground="#ff6b6b")    # Light Red
        self.tree.tag_configure("WARNING", foreground="#ffd93d")  # Yellow
        self.tree.tag_configure("INFO", foreground="#ffffff")
        self.tree.tag_configure("SILENT", foreground="#a0a0a0")   # Gray

    def _load_data(self):
        try:
            # Clear existing
            for i in self.tree.get_children():
                self.tree.delete(i)
                
            self.current_errors = ErrorHandler.get_recent_errors(limit=100)
            ErrorHandler.log_info(f"Viewer loaded {len(self.current_errors)} errors")
            
            if not self.current_errors:
                # Add placeholder if empty
                self.tree.insert("", "end", values=("", "INFO", "", "No errors found in log file."))
                return
            
            # Insert in reverse order (newest top)
            for i, err in enumerate(reversed(self.current_errors)):
                tags = (err.get("level", "INFO"),)
                values = (
                    err.get("timestamp", "")[:19].replace("T", " "), # Clean up timestamp
                    err.get("level", ""),
                    err.get("context", ""),
                    err.get("message", "")
                )
                # Use 'i' as index to map back to reversed list
                self.tree.insert("", "end", iid=str(i), values=values, tags=tags)
                
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error Log Error", f"Failed to load error log:\n{e}")
            
    def _on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        iid = selected[0]
        try:
            index = int(iid)
            # data was reversed
            err = list(reversed(self.current_errors))[index]
            
            # Construct details
            details = f"Time: {err.get('timestamp')}\n"
            details += f"Level: {err.get('level')}\n"
            details += f"Context: {err.get('context')}\n"
            details += f"Message: {err.get('message')}\n"
            
            exc = err.get("exception")
            if exc:
                details += f"\nException: {exc}\n"
                
            trace = err.get("stack_trace")
            if trace:
                details += f"\nStack Trace:\n{trace}"
                
            self.txt_details.delete("1.0", END)
            self.txt_details.insert("1.0", details)
            
        except (ValueError, IndexError):
            pass

    def _clear_log(self):
        ErrorHandler.clear_log_file()
        self._load_data()

    def show(self):
        """Display the dialog."""
        self.deiconify()
        self.lift()
        self.focus_force()
