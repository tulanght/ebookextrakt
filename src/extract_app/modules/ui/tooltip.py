import customtkinter as ctk

class ToolTip:
    """
    A simple tooltip that appears when hovering over a widget.
    (Dark Navy Theme)
    """
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        
        # Bind events
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave) # Hide on click

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self, event=None):
        if self.tooltip_window or not self.text:
            return
            
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Creates a toplevel window
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        # Leaves only the label and removes the app window
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Styling
        label = ctk.CTkLabel(
            tw, text=self.text, justify='left',
            fg_color="#1E293B", # Colors.BG_CARD
            text_color="#F8FAFC", # Colors.TEXT_PRIMARY
            corner_radius=4,
            width=50,
            padx=10, pady=5,
            font=("Inter", 12)
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()
