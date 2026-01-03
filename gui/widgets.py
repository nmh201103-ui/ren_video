"""
Custom widgets cho GUI
"""
import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """Frame có scrollbar"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Canvas và scrollbar
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class StatusLabel(ttk.Label):
    """Label hiển thị status với màu sắc"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.default_bg = self.cget('background')
    
    def set_success(self, text: str):
        """Set text thành công (màu xanh)"""
        self.config(text=text, foreground='green')
    
    def set_error(self, text: str):
        """Set text lỗi (màu đỏ)"""
        self.config(text=text, foreground='red')
    
    def set_info(self, text: str):
        """Set text thông tin (màu đen)"""
        self.config(text=text, foreground='black')
    
    def set_warning(self, text: str):
        """Set text cảnh báo (màu cam)"""
        self.config(text=text, foreground='orange')




