"""
Results View component for the ExtractPDF-EPUB application.
Handles displaying metadata, content tree, and the extract action.
"""
from typing import Any, Dict, List, Callable
from functools import partial
from pathlib import Path
from PIL import Image

import customtkinter as ctk

class ResultsView(ctk.CTkFrame):
    """
    Main view for displaying parsed results including metadata and content tree.
    """
    def __init__(self, master, on_extract: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_extract = on_extract
        
        # UI Attributes
        self.metadata_panel: ctk.CTkFrame
        self.cover_label: ctk.CTkLabel
        self.title_label: ctk.CTkLabel
        self.author_label: ctk.CTkLabel
        self.content_panel: ctk.CTkScrollableFrame
        self.bottom_bar: ctk.CTkFrame
        self.extract_btn: ctk.CTkButton
        
        self._create_widgets()

    def _create_widgets(self):
        """Create the layout and widgets."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Metadata Panel (Left Side)
        self.metadata_panel = ctk.CTkFrame(self, width=280, corner_radius=10)
        self.metadata_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ns")
        self.metadata_panel.grid_propagate(False)
        self.metadata_panel.grid_rowconfigure(3, weight=1) # Spacer

        self.cover_label = ctk.CTkLabel(self.metadata_panel, text="")
        self.cover_label.grid(row=0, column=0, padx=20, pady=20)

        self.title_label = ctk.CTkLabel(
            self.metadata_panel, text="Title", font=("", 16, "bold"), wraplength=240, justify="center"
        )
        self.title_label.grid(row=1, column=0, padx=10, pady=(0, 5))

        self.author_label = ctk.CTkLabel(self.metadata_panel, text="Author", wraplength=240, text_color="gray")
        self.author_label.grid(row=2, column=0, padx=10, pady=5)

        # 2. Content Panel (Right Side, Scrollable)
        self.content_panel = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.content_panel.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        
        # 3. Bottom Action Bar
        self.bottom_bar = ctk.CTkFrame(self, height=60, corner_radius=10, fg_color=("gray90", "gray16"))
        self.bottom_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        self.bottom_bar.grid_columnconfigure(0, weight=1)
        
        # Info text in bar
        self.status_label = ctk.CTkLabel(self.bottom_bar, text="Sẵn sàng trích xuất", text_color="gray")
        self.status_label.grid(row=0, column=0, padx=20, sticky="w")
        
        # Extract Button
        self.extract_btn = ctk.CTkButton(
            self.bottom_bar,
            text="TRÍCH XUẤT NỘI DUNG",
            font=ctk.CTkFont(weight="bold"),
            height=36,
            command=self._on_extract_click
        )
        self.extract_btn.grid(row=0, column=1, padx=20, pady=12)

    def show_results(self, results: Dict[str, Any]):
        """Populate the view with results data."""
        self._update_metadata(results.get('metadata', {}))
        self._display_content_tree(results.get('content', []))
        
        # Reset Status
        item_count = len(results.get('content', []))
        self.status_label.configure(text=f"Đã tìm thấy {item_count} mục nội dung.")

    def _update_metadata(self, metadata: Dict[str, Any]):
        """Update the metadata panel."""
        self.title_label.configure(text=metadata.get('title', 'Không có tiêu đề'))
        self.author_label.configure(text=metadata.get('author', 'Không rõ tác giả'))
        
        cover_path = metadata.get('cover_image_path', '')
        self._load_cover_image(cover_path)

    def _load_cover_image(self, cover_path: str):
        """Load and display the cover image with resizing."""
        if cover_path and Path(cover_path).exists():
            try:
                img = Image.open(cover_path)
                # Calculate new height to maintain aspect ratio with fixed width approx 240
                target_width = 240
                width_percent = (target_width / float(img.size[0]))
                new_height = int((float(img.size[1]) * float(width_percent)))
                
                resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
                img = img.resize((target_width, new_height), resample_filter)

                ctk_img = ctk.CTkImage(light_image=img, size=(target_width, new_height))
                self.cover_label.configure(image=ctk_img, text="")
                self.cover_label.image = ctk_img 
            except Exception:
                self.cover_label.configure(image=None, text="[Lỗi ảnh]")
        else:
            self.cover_label.configure(image=None, text="[No Cover]")

    def _display_content_tree(self, content_tree: List[Dict[str, Any]]):
        """Recursively build and display the content tree structure."""
        for widget in self.content_panel.winfo_children():
            widget.destroy()
        self._create_tree_view_nodes(self.content_panel, content_tree, 0)

    @staticmethod
    def _toggle_children(button: ctk.CTkButton, frame: ctk.CTkFrame):
        """Helper function to show/hide a children frame."""
        if frame.winfo_viewable():
            frame.pack_forget()
            button.configure(text="+")
        else:
            frame.pack(fill="x", expand=True, padx=0, pady=0)
            button.configure(text="-")

    def _create_tree_view_nodes(self, parent_widget, nodes: List[Dict[str, Any]], level: int):
        """Create the UI widgets for a list of nodes at a specific indentation level."""
        indent = level * 25
        for node_data in nodes:
            node_title = node_data.get('title', 'No Title')
            children = node_data.get('children', [])
            
            # Use a slightly different look for nodes
            node_container = ctk.CTkFrame(parent_widget, fg_color="transparent")
            node_container.pack(fill="x", expand=True, pady=1)
            
            header_frame = ctk.CTkFrame(node_container, fg_color="transparent")
            header_frame.pack(fill="x", padx=(indent, 5))
            header_frame.grid_columnconfigure(1, weight=1)
            
            children_frame = ctk.CTkFrame(node_container, fg_color="transparent")
            
            toggle_button = ctk.CTkButton(
                header_frame, 
                text="+" if children else "•", 
                width=24, 
                height=24,
                fg_color="transparent",
                text_color="gray",
                hover_color=("gray90", "gray20")
            )
            toggle_button.grid(row=0, column=0, sticky="w")
            
            title_label = ctk.CTkLabel(header_frame, text=node_title, font=("", 13), anchor="w")
            title_label.grid(row=0, column=1, sticky="ew", padx=5)
            
            # Simple stats badge
            summary_label = self._create_summary_label(header_frame, node_data)
            summary_label.grid(row=0, column=2, sticky="e", padx=5)

            if children:
                # Wiring the toggle
                command = partial(self._toggle_children, toggle_button, children_frame)
                toggle_button.configure(command=command)
                self._create_tree_view_nodes(children_frame, children, level + 1)
            else:
                 toggle_button.configure(state="disabled")

    def _aggregate_content_from_children(self, node: Dict[str, Any]) -> List:
        """Recursively gather all content from a node and its children."""
        aggregated_content = list(node.get('content', []))
        for child in node.get('children', []):
            aggregated_content.extend(
                self._aggregate_content_from_children(child))
        return aggregated_content

    def _create_summary_label(self, master, node_data: Dict[str, Any]) -> ctk.CTkLabel:
        """Create a summary label."""
        content_to_summarize = self._aggregate_content_from_children(node_data)
        total_words = sum(
            len(str(data).split()) for c_type, data in content_to_summarize if c_type == 'text'
        )
        image_count = sum(1 for c_type, _ in content_to_summarize if c_type == 'image')
        
        # Minimalist summary
        text = ""
        if total_words > 0: text += f"{total_words} words "
        if image_count > 0: text += f"{image_count} imgs"
        
        return ctk.CTkLabel(master, text=text, text_color="gray", font=("", 10))

    def _on_extract_click(self):
        """Handle extract button click."""
        # Open directory selector
        target_dir = ctk.filedialog.askdirectory(title="Chọn thư mục lưu kết quả")
        if target_dir:
            self.on_extract(target_dir)
