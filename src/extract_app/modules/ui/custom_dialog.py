import customtkinter as ctk
from .theme import Colors, Fonts, Spacing

class CustomDialog(ctk.CTkToplevel):
    """A custom dialog window matching the Dark Navy theme."""
    def __init__(self, master, title: str, message: str, type: str = "info", on_close=None):
        super().__init__(master)
        self.title(title)
        self.geometry("420x200")
        self.configure(fg_color=Colors.BG_APP)
        self.attributes('-topmost', True)
        self.resizable(False, False)
        
        self.result = False
        self.on_close = on_close
        
        # Main Frame
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=Spacing.XL, pady=Spacing.XL)
        
        icon = "ℹ"
        icon_color = Colors.PRIMARY
        if type == "warning":
            icon = "⚠"
            icon_color = Colors.WARNING
        elif type == "danger" or type == "question":
            icon = "❓" if type == "question" else "‼"
            icon_color = Colors.DANGER if type == "danger" else Colors.PRIMARY
        elif type == "success":
            icon = "✓"
            icon_color = Colors.SUCCESS
            
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, Spacing.MD))
        
        ctk.CTkLabel(header, text=icon, font=("Segoe UI", 28, "bold"), text_color=icon_color).pack(side="left", padx=(0, Spacing.MD))
        ctk.CTkLabel(header, text=title, font=Fonts.H3, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        ctk.CTkLabel(self.frame, text=message, font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, justify="left", wraplength=360).pack(fill="x", pady=(0, Spacing.LG))
        
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")
        
        if type in ["warning", "danger", "question"]:
            btn_cancel = ctk.CTkButton(
                btn_frame, text="Không", width=90, fg_color="transparent",
                border_width=1, border_color=Colors.BORDER, text_color=Colors.TEXT_MUTED,
                hover_color=Colors.BG_CARD_HOVER, command=self._on_cancel
            )
            btn_cancel.pack(side="right", padx=(Spacing.MD, 0))
            
            btn_ok = ctk.CTkButton(
                btn_frame, text="Có", width=90, fg_color=Colors.DANGER if type == "danger" else Colors.PRIMARY,
                text_color="white", command=self._on_ok
            )
            btn_ok.pack(side="right")
        else:
            btn_ok = ctk.CTkButton(
                btn_frame, text="OK", width=90, fg_color=Colors.PRIMARY,
                text_color="white", command=self._on_ok
            )
            btn_ok.pack(side="right")
            
        # Center dialog
        self.update_idletasks()
        self._center_window()
        self.grab_set()

    def _center_window(self):
        try:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _on_ok(self):
        self.result = True
        self._close()
        
    def _on_cancel(self):
        self.result = False
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()
        if self.on_close:
            self.on_close(self.result)

def ask_yes_no(master, title: str, message: str, is_danger=False, callback=None) -> bool:
    dialog = CustomDialog(master, title, message, type="danger" if is_danger else "question", on_close=callback)
    if not callback:
        master.wait_window(dialog)
        return dialog.result
    return False

def show_info(master, title: str, message: str) -> None:
    dialog = CustomDialog(master, title, message, type="info")
    master.wait_window(dialog)

def show_warning(master, title: str, message: str) -> None:
    dialog = CustomDialog(master, title, message, type="warning")
    master.wait_window(dialog)

def show_error(master, title: str, message: str) -> None:
    dialog = CustomDialog(master, title, message, type="danger")
    master.wait_window(dialog)
