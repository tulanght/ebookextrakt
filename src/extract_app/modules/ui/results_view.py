# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/results_view.py
# Version: 1.1.0
# Author: Antigravity
# Description: Results View with Lazy Loading and Featherweight display.
# --------------------------------------------------------------------------------

from typing import Any, Dict, List, Callable, Optional, Tuple, Union
from functools import partial
from pathlib import Path
from PIL import Image

import customtkinter as ctk

class ResultsView(ctk.CTkFrame):
    """
    Main view for displaying parsed results including metadata and content tree.
    
    Implements 'Featherweight' mode by using lazy loading for tree nodes.
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
        # self.metadata_panel.grid_propagate(False) # This was hiding content
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
                self.cover_label.image = ctk_img  # Keep reference
            except Exception:
                self.cover_label.configure(image=None, text="[Lỗi ảnh]")
        else:
            self.cover_label.configure(image=None, text="[No Cover]")

    def _display_content_tree(self, content_tree: List[Dict[str, Any]]):
        """Clear and rebuild the content tree."""
        for widget in self.content_panel.winfo_children():
            widget.destroy()
        # Start the recursion at level 0
        self._create_lazy_nodes(self.content_panel, content_tree, 0)

    def _create_lazy_nodes(self, parent_widget, nodes: List[Dict[str, Any]], level: int):
        """
        Create UI widgets for nodes. 
        Note: Does NOT recurse immediately. Content is generated on expand.
        """
        indent = level * 25
        for node_data in nodes:
            node_title = node_data.get('title', 'No Title')
            content = node_data.get('content', [])
            children = node_data.get('children', [])
            
            # 1. Container for this node
            node_container = ctk.CTkFrame(parent_widget, fg_color="transparent")
            node_container.pack(fill="x", expand=True, pady=1)
            
            # 2. Header Frame (Always visible)
            header_frame = ctk.CTkFrame(node_container, fg_color="transparent")
            header_frame.pack(fill="x", padx=(indent, 5))
            header_frame.grid_columnconfigure(1, weight=1)
            
            # 3. Children/Content Frame (Hidden by default)
            expansion_frame = ctk.CTkFrame(node_container, fg_color="transparent")
            # Don't pack it yet.
            
            # 4. Toggle Button
            has_expandable_content = len(content) > 0 or len(children) > 0
            
            toggle_button = ctk.CTkButton(
                header_frame, 
                text="+" if has_expandable_content else "•", 
                width=24, 
                height=24,
                fg_color="transparent",
                text_color="gray",
                hover_color=("gray90", "gray20")
            )
            toggle_button.grid(row=0, column=0, sticky="w")
            
            # 5. Title
            title_label = ctk.CTkLabel(header_frame, text=node_title, font=("", 13), anchor="w")
            title_label.grid(row=0, column=1, sticky="ew", padx=5)
            
            # 6. Stats
            summary_label = self._create_summary_label(header_frame, node_data)
            summary_label.grid(row=0, column=2, sticky="e", padx=5)

            if has_expandable_content:
                # Lazy Loading: Pass the data needed to generate children later
                command = partial(
                    self._on_toggle_node, 
                    toggle_button=toggle_button, 
                    expansion_frame=expansion_frame,
                    node_content=content,
                    node_children=children,
                    current_level=level
                )
                toggle_button.configure(command=command)
            else:
                 toggle_button.configure(state="disabled")

    def _on_toggle_node(self, toggle_button, expansion_frame, node_content, node_children, current_level):
        """
        Handle expand/collapse.
        First time expand: Generates widgets.
        Subsequent: Toggles visibility.
        """
        if expansion_frame.winfo_viewable():
            # Collapse
            expansion_frame.pack_forget()
            toggle_button.configure(text="+")
        else:
            # Expand
            expansion_frame.pack(fill="x", expand=True, padx=0, pady=0)
            toggle_button.configure(text="-")
            
            # Check if this is the first time (frame is empty)
            if not expansion_frame.winfo_children():
                # 1. Render Content (Text/Images) for *this* node
                if node_content:
                    self._render_node_content(expansion_frame, node_content, current_level)
                
                # 2. Render Children Nodes (Recursive step)
                if node_children:
                    self._create_lazy_nodes(expansion_frame, node_children, current_level + 1)

    def _render_node_content(self, parent, content_list: List[Union[Dict, Tuple]], level: int):
        """
        Render placeholders for text/images within a node.
        Handles both Dict {'type':..., 'data':...} and Tuple ('type', data) formats.
        """
        indent = (level + 1) * 25 # Indent slightly more than the parent node
        
        for item in content_list:
            # Normalize data format
            c_type = ""
            c_data = ""
            
            if isinstance(item, dict):
                c_type = item.get('type')
                c_data = item.get('data')
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                c_type = item[0]
                c_data = item[1]
            
            row_frame = ctk.CTkFrame(parent, fg_color="transparent", height=20)
            row_frame.pack(fill="x", padx=(indent, 5), pady=1)
            
            if c_type == 'text':
                word_count = len(str(c_data).split())
                preview = str(c_data)[:50].replace('\n', ' ') + "..."
                lbl = ctk.CTkLabel(
                    row_frame, 
                    text=f"[Text: {word_count} words]  {preview}", 
                    text_color=("gray50", "gray70"),
                    font=("Consolas", 11)
                )
                lbl.pack(side="left")
                
            elif c_type == 'image':
                # Handle image data which might be a dict {'anchor':..., 'caption':...} or just path string
                img_path = ""
                if isinstance(c_data, dict):
                     img_path = c_data.get('anchor', str(c_data))
                else:
                     img_path = str(c_data)

                filename = Path(img_path).name
                lbl = ctk.CTkLabel(
                    row_frame, 
                    text=f"📷 [Image: {filename}]", 
                    text_color=("#3B8ED0", "#1F6AA5"), # Link colorish
                    font=("Consolas", 11, "bold")
                )
                lbl.pack(side="left")

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
        
        total_words = 0
        image_count = 0
        
        for item in content_to_summarize:
            c_type = ""
            c_data = ""
            if isinstance(item, dict):
                c_type = item.get('type')
                c_data = item.get('data')
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                c_type = item[0]
                c_data = item[1]
                
            if c_type == 'text':
                total_words += len(str(c_data).split())
            elif c_type == 'image':
                image_count += 1
        
        # Minimalist summary
        parts = []
        if total_words > 0: parts.append(f"{total_words} words")
        if image_count > 0: parts.append(f"{image_count} imgs")
        text = ", ".join(parts)
        
        return ctk.CTkLabel(master, text=text, text_color="gray", font=("", 10))

    def _on_extract_click(self):
        """Handle extract button click."""
        target_dir = ctk.filedialog.askdirectory(title="Chọn thư mục lưu kết quả")
        if target_dir:
            self.on_extract(target_dir)
