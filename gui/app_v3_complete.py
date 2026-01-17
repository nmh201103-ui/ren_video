"""
NMH03 Video Pro v3 - Complete Edition
Main application entry point with modular tab architecture
"""
import tkinter as tk
from tkinter import ttk
import os
from utils.helpers import ensure_directory
from utils.logger import get_logger
from gui.tabs import ProductReviewTab, MovieReviewTab, VideoClipperTab

logger = get_logger()


class NMH03VideoProV3:
    """Main application - Video creator with multiple tabs"""
    
    VIDEO_FORMATS = {
        'short': {'name': '⚡ Short (15-30s)', 'duration': 30, 'scenes': 3, 'icon': '⚡'},
        'medium': {'name': '📹 Medium (45-60s)', 'duration': 60, 'scenes': 5, 'icon': '📹'},
        'long': {'name': '🎬 Long (2-5 min)', 'duration': 180, 'scenes': 10, 'icon': '🎬'},
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎬 NMH03 Video Pro v3 - Complete Edition")
        self.root.geometry("1500x900")
        self.root.resizable(True, True)
        self.root.configure(bg="#0d1117")
        
        self.video_path = None
        self.status_text = tk.StringVar(value="Ready 🚀")
        self.progress_percent = tk.IntVar(value=0)
        
        self._setup_ui()
        ensure_directory("output/videos")
        ensure_directory("output/segments")
        ensure_directory("output/clips")
    
    def _setup_ui(self):
        """Build main UI with tabs"""
        main = tk.Frame(self.root, bg="#0d1117")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self._setup_header(main)
        
        # Tabs
        content = tk.Frame(main, bg="#0d1117")
        content.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Custom.TNotebook', 
                       background='#161b22', 
                       borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                       background='#21262d',
                       foreground='#8b949e',
                       padding=[25, 12],
                       font=('Segoe UI', 11, 'bold'))
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', '#58a6ff')],
                 foreground=[('selected', '#ffffff')])
        
        self.notebook = ttk.Notebook(content, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.product_tab = tk.Frame(self.notebook, bg="#161b22")
        self.movie_tab = tk.Frame(self.notebook, bg="#161b22")
        self.clipper_tab = tk.Frame(self.notebook, bg="#161b22")
        self.settings_tab = tk.Frame(self.notebook, bg="#161b22")
        
        self.notebook.add(self.product_tab, text='  📦 Product Review  ')
        self.notebook.add(self.movie_tab, text='  📽️ Movie Review  ')
        self.notebook.add(self.clipper_tab, text='  ✂️ Video Clipper  ')
        self.notebook.add(self.settings_tab, text='  ⚙️ Settings  ')
        
        # Initialize tab content
        self.product_review = ProductReviewTab(
            self.product_tab, 
            self._update_status,
            video_formats=self.VIDEO_FORMATS
        )
        
        self.movie_review = MovieReviewTab(
            self.movie_tab,
            self._update_status
        )
        
        self.video_clipper = VideoClipperTab(self.clipper_tab)
        
        self._setup_settings_tab()
    
    def _setup_header(self, parent):
        """Setup header with title and version"""
        header = tk.Frame(parent, bg="#161b22", height=100)
        header.pack(fill=tk.X, pady=(0, 20))
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg="#161b22")
        title_frame.pack(side=tk.LEFT, padx=30, pady=25)
        
        tk.Label(title_frame,
                text="🎬 NMH03 Video Pro",
                font=("Segoe UI", 26, "bold"),
                fg="#58a6ff",
                bg="#161b22").pack(anchor="w")
        
        tk.Label(title_frame,
                text="Product • Movie • Video Clipper • Auto Highlights",
                font=("Segoe UI", 10),
                fg="#8b949e",
                bg="#161b22").pack(anchor="w")
        
        tk.Label(header,
                text="v3.1",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#238636",
                padx=10,
                pady=5).pack(side=tk.RIGHT, padx=30)
    
    def _setup_settings_tab(self):
        """Setup settings tab"""
        container = tk.Frame(self.settings_tab, bg="#161b22", padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        self._add_card(container, "⚙️ API Configuration", "Optional AI services")
        
        settings = [
            ("OPENAI_API_KEY", "OpenAI API Key (for ChatGPT script generation)"),
            ("OMDB_API_KEY", "OMDb API Key (for movie metadata)"),
            ("DID_API_KEY", "D-ID API Key (premium avatar)"),
        ]
        
        for key, desc in settings:
            frame = tk.Frame(container, bg="#21262d", padx=20, pady=15)
            frame.pack(fill=tk.X, pady=10)
            
            tk.Label(frame, text=desc, font=("Segoe UI", 10, "bold"),
                    fg="#c9d1d9", bg="#21262d").pack(anchor="w")
            
            entry = tk.Entry(frame, font=("Consolas", 10),
                           bg="#161b22", fg="#c9d1d9",
                           insertbackground="#58a6ff",
                           relief=tk.FLAT, show="*")
            entry.pack(fill=tk.X, pady=(5, 0), ipady=8)
        
        tk.Button(container,
                 text="💾 Save Settings",
                 font=("Segoe UI", 12, "bold"),
                 bg="#238636", fg="#ffffff",
                 relief=tk.FLAT, cursor="hand2").pack(pady=20, ipadx=30, ipady=12)
    
    def _add_card(self, parent, title, subtitle=""):
        """Add section card"""
        frame = tk.Frame(parent, bg="#161b22")
        frame.pack(fill=tk.X, padx=20, pady=(20, 5))
        
        tk.Label(frame, text=title, font=("Segoe UI", 14, "bold"),
                fg="#c9d1d9", bg="#161b22").pack(anchor="w")
        
        if subtitle:
            tk.Label(frame, text=subtitle, font=("Segoe UI", 9),
                    fg="#8b949e", bg="#161b22").pack(anchor="w")
    
    def _update_status(self, message, progress):
        """Update status from tabs"""
        self.status_text.set(message)
        if progress is not None:
            self.progress_percent.set(progress)
    
    def run(self):
        """Start application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = NMH03VideoProV3()
    app.run()
