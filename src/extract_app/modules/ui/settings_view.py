# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/settings_view.py
# Version: 1.2.0
# Description: Main Settings View (embedded in main window).
# --------------------------------------------------------------------------------

import customtkinter as ctk
import tkinter as tk
from .theme import Colors, Fonts, Spacing
from .custom_dialog import ask_yes_no, show_info, show_warning, show_error

class SettingsView(ctk.CTkFrame):
    """
    Settings View embedded in the main window (Dark Navy theme).
    Includes: Hybrid API Settings (Cloud/Local), Appearance, etc.
    """
    
    def __init__(self, parent, settings_manager, translation_service):
        super().__init__(parent, fg_color="transparent")
        
        self.settings_manager = settings_manager
        self.translation_service = translation_service
        
        # Build UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the tabbed interface."""
        # Main Title
        header = ctk.CTkLabel(
            self, text="Cài Đặt Hệ Thống", 
            font=Fonts.H1, text_color=Colors.TEXT_PRIMARY
        )
        header.pack(anchor="w", padx=Spacing.XL, pady=(Spacing.XL, Spacing.MD))

        self.tabview = ctk.CTkTabview(
            self, fg_color=Colors.BG_CARD,
            segmented_button_fg_color=Colors.BG_APP,
            segmented_button_selected_color=Colors.PRIMARY,
            segmented_button_selected_hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.TEXT_PRIMARY
        )
        self.tabview.pack(padx=Spacing.XL, pady=(0, Spacing.XL), fill="both", expand=True)
        
        self.tabview.add("Dịch thuật & AI")
        self.tabview.add("Từ Vựng (Glossary)")
        self.tabview.add("Giao diện & Hệ thống")
        
        self._build_translation_tab(self.tabview.tab("Dịch thuật & AI"))
        self._build_glossary_tab(self.tabview.tab("Từ Vựng (Glossary)"))
        self._build_system_tab(self.tabview.tab("Giao diện & Hệ thống"))
        
        self.tabview.set("Dịch thuật & AI")
    
    def _build_translation_tab(self, parent):
        """Build the Hybrid Translation settings tab."""
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        scroll.pack(fill="both", expand=True, padx=Spacing.SM, pady=Spacing.SM)
        
        # --- 1. Engine Selection ---
        ctk.CTkLabel(
            scroll, text="Chọn Bộ máy Dịch thuật", 
            font=Fonts.H3, text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, Spacing.MD))
        
        self.engine_var = tk.StringVar(value=self.settings_manager.get("translation_engine", "cloud"))
        
        engine_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        engine_frame.pack(fill="x", pady=Spacing.SM)
        
        ctk.CTkRadioButton(
            engine_frame, text="Cloud (Gemini API)", variable=self.engine_var, value="cloud",
            command=self._update_ui_state, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER
        ).pack(side="left", padx=Spacing.XL)
        
        ctk.CTkRadioButton(
            engine_frame, text="Local (TranslateGemma)", variable=self.engine_var, value="local",
            command=self._update_ui_state, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER
        ).pack(side="left", padx=Spacing.XL)
        
        # --- Dynamic Container for Settings ---
        self.dynamic_settings_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.dynamic_settings_frame.pack(fill="x")
        
        # --- 2. Cloud Settings ---
        self.cloud_frame = ctk.CTkFrame(self.dynamic_settings_frame, fg_color=Colors.BG_APP, corner_radius=Spacing.CARD_RADIUS)
        self.cloud_frame.pack(fill="x", pady=Spacing.MD, ipady=Spacing.SM)
        
        ctk.CTkLabel(
            self.cloud_frame, text="Cấu hình Cloud AI", 
            font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=Spacing.MD, pady=Spacing.SM)
        
        # Provider Selection
        provider_frame = ctk.CTkFrame(self.cloud_frame, fg_color="transparent")
        provider_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
        
        ctk.CTkLabel(provider_frame, text="Nền tảng:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.provider_var = tk.StringVar(value=self.settings_manager.get("cloud_provider", "ai_studio"))
        
        ctk.CTkRadioButton(
            provider_frame, text="Google AI Studio", variable=self.provider_var, value="ai_studio",
            command=self._update_cloud_ui, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER
        ).pack(side="left", padx=(0, Spacing.MD))
        
        ctk.CTkRadioButton(
            provider_frame, text="Vertex AI (300$)", variable=self.provider_var, value="vertex_ai",
            command=self._update_cloud_ui, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER
        ).pack(side="left", padx=Spacing.SM)

        # Provider Settings Container
        self.provider_settings_container = ctk.CTkFrame(self.cloud_frame, fg_color="transparent")
        self.provider_settings_container.pack(fill="x")

        # AI Studio Frame
        self.ai_studio_frame = ctk.CTkFrame(self.provider_settings_container, fg_color="transparent")
        self.ai_studio_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
        
        ctk.CTkLabel(self.ai_studio_frame, text="API Key:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.api_key_var = tk.StringVar(value=self.settings_manager.get_api_key())
        self.api_key_entry = ctk.CTkEntry(
            self.ai_studio_frame, textvariable=self.api_key_var, show="•", width=300,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY,
            height=32
        )
        self.api_key_entry.pack(side="left", padx=Spacing.SM, fill="x", expand=True)
        
        self.show_api_key = False
        self.btn_toggle = ctk.CTkButton(
            self.ai_studio_frame, text="👁", width=32, height=32, command=self._toggle_key_visibility,
            fg_color=Colors.BG_CARD, hover_color=Colors.BG_CARD_HOVER, border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY
        )
        self.btn_toggle.pack(side="left", padx=Spacing.SM)

        # Vertex AI Frame
        self.vertex_frame = ctk.CTkFrame(self.provider_settings_container, fg_color="transparent")
        self.vertex_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
        
        v_api_frame = ctk.CTkFrame(self.vertex_frame, fg_color="transparent")
        v_api_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(v_api_frame, text="API Key:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.v_api_key_var = tk.StringVar(value=self.settings_manager.get("vertex_api_key", ""))
        ctk.CTkEntry(
            v_api_frame, textvariable=self.v_api_key_var, placeholder_text="(Ưu tiên dùng API Key từ Agent Platform nếu có)",
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32, show="•"
        ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)


        v_proj_frame = ctk.CTkFrame(self.vertex_frame, fg_color="transparent")
        v_proj_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(v_proj_frame, text="Project ID:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.v_proj_var = tk.StringVar(value=self.settings_manager.get("vertex_project_id", ""))
        ctk.CTkEntry(
            v_proj_frame, textvariable=self.v_proj_var,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32
        ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)
        
        v_reg_frame = ctk.CTkFrame(self.vertex_frame, fg_color="transparent")
        v_reg_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(v_reg_frame, text="Region:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.v_reg_var = tk.StringVar(value=self.settings_manager.get("vertex_region", "us-central1"))
        ctk.CTkEntry(
            v_reg_frame, textvariable=self.v_reg_var,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32
        ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)

        v_json_frame = ctk.CTkFrame(self.vertex_frame, fg_color="transparent")
        v_json_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(v_json_frame, text="JSON Key:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.v_json_var = tk.StringVar(value=self.settings_manager.get("vertex_credentials_path", ""))
        ctk.CTkEntry(
            v_json_frame, textvariable=self.v_json_var, placeholder_text="(Bỏ trống nếu dùng gcloud ADC)",
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32
        ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)
        ctk.CTkButton(
            v_json_frame, text="Browse", width=60, height=32, command=self._browse_json,
            fg_color=Colors.BG_CARD, hover_color=Colors.BG_CARD_HOVER, border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="right")

        # Model Selection
        model_select_frame = ctk.CTkFrame(self.cloud_frame, fg_color="transparent")
        model_select_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
        
        ctk.CTkLabel(model_select_frame, text="Model:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        self.STUDIO_MODELS = [
            "gemini-3.1-pro-preview",
            "gemini-3.1-flash-lite",
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
        self.VERTEX_MODELS = [
            "gemini-3.1-pro-preview",
            "gemini-3.1-flash-lite",
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
        
        provider = self.settings_manager.get("cloud_provider", "ai_studio")
        initial_models = self.VERTEX_MODELS if provider == "vertex_ai" else self.STUDIO_MODELS
        current_model = self.settings_manager.get("cloud_model_name", initial_models[0])
        self.cloud_model_var = tk.StringVar(value=current_model)
        
        self.cloud_model_menu = ctk.CTkComboBox(
            model_select_frame, variable=self.cloud_model_var, values=initial_models, width=280,
            fg_color=Colors.BG_INPUT, button_color=Colors.BORDER, button_hover_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY, dropdown_fg_color=Colors.BG_CARD, dropdown_text_color=Colors.TEXT_PRIMARY
        )
        self.cloud_model_menu.pack(side="left", padx=Spacing.SM)
        
        ctk.CTkLabel(
            model_select_frame, text="(Pro = Chất lượng, Flash = Tốc độ)", 
            text_color=Colors.TEXT_MUTED, font=Fonts.TINY
        ).pack(side="left", padx=Spacing.MD)

        # Chunk size & Delay (dùng cho cả Cloud)
        perf_frame = ctk.CTkFrame(self.cloud_frame, fg_color="transparent")
        perf_frame.pack(fill="x", padx=Spacing.MD, pady=(0, Spacing.SM))
        ctk.CTkLabel(perf_frame, text="Chunk size:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.chunk_size_var = tk.StringVar(value=str(self.settings_manager.get("chunk_size", 15000)))
        ctk.CTkEntry(
            perf_frame, textvariable=self.chunk_size_var, width=80,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32
        ).pack(side="left", padx=Spacing.SM)
        ctk.CTkLabel(perf_frame, text="Delay (s):", width=70, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=(Spacing.LG, 0))
        self.delay_var = tk.StringVar(value=str(self.settings_manager.get("chunk_delay", 2.0)))
        ctk.CTkEntry(
            perf_frame, textvariable=self.delay_var, width=60,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32
        ).pack(side="left", padx=Spacing.SM)
        
        # --- 3. Local Settings ---
        self.local_frame = ctk.CTkFrame(self.dynamic_settings_frame, fg_color=Colors.BG_APP, corner_radius=Spacing.CARD_RADIUS)
        self.local_frame.pack(fill="x", pady=Spacing.MD, ipady=Spacing.SM)
        
        ctk.CTkLabel(
            self.local_frame, text="Cấu hình Local LLM (GPU)", 
            font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=Spacing.MD, pady=Spacing.SM)
        
        model_frame = ctk.CTkFrame(self.local_frame, fg_color="transparent")
        model_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
        ctk.CTkLabel(model_frame, text="Model Path (.gguf):", width=120, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        self.model_path_var = tk.StringVar(value=self.settings_manager.get("local_model_path", ""))
        self.model_entry = ctk.CTkEntry(
            model_frame, textvariable=self.model_path_var,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32
        )
        self.model_entry.pack(side="left", padx=Spacing.SM, fill="x", expand=True)
        
        ctk.CTkButton(
            model_frame, text="Browse", width=60, height=32, command=self._browse_model,
            fg_color=Colors.BG_CARD, hover_color=Colors.BG_CARD_HOVER, border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="right")
        
        # Configs (Style, GPU)
        config_frame = ctk.CTkFrame(self.local_frame, fg_color="transparent")
        config_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
        
        ctk.CTkLabel(config_frame, text="Văn phong:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.style_var = tk.StringVar(value=self.settings_manager.get("current_style", "standard"))
        
        styles = ["standard", "facebook_gem", "website_seo", "literary", "casual"] 
        self.style_menu = ctk.CTkSegmentedButton(
            config_frame, variable=self.style_var, values=styles
        )
        self.style_menu.pack(side="left", padx=Spacing.SM)
        
        ctk.CTkLabel(config_frame, text="GPU Layers:", width=80, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=(Spacing.XL, 0))
        self.gpu_layers_var = tk.StringVar(value=str(self.settings_manager.get("n_gpu_layers", -1)))
        ctk.CTkEntry(
            config_frame, textvariable=self.gpu_layers_var, width=50,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY, height=32
        ).pack(side="left", padx=Spacing.SM)
        ctk.CTkLabel(config_frame, text="(-1 = Auto)", text_color=Colors.TEXT_MUTED, font=Fonts.TINY).pack(side="left")
        
        # --- 4. Common Settings --- (chỉ còn Local cần thêm perf settings)
        
        # --- Actions ---
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.pack(fill="x", pady=Spacing.MD, padx=Spacing.SM)
        
        self.status_label = ctk.CTkLabel(action_frame, text="", text_color=Colors.TEXT_MUTED, font=Fonts.BODY)
        self.status_label.pack(side="left")
        
        ctk.CTkButton(
            action_frame, text="Lưu Cài đặt", command=self._save_settings, width=120, height=40,
            fg_color=Colors.SUCCESS, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.SUCCESS_HOVER,
            font=Fonts.BODY_BOLD, corner_radius=Spacing.BUTTON_RADIUS
        ).pack(side="right")
        
        ctk.CTkButton(
            action_frame, text="Test Model", command=self._test_connection, width=100, height=40,
            fg_color=Colors.BG_CARD, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.BG_CARD_HOVER,
            border_width=1, border_color=Colors.BORDER,
            font=Fonts.BODY, corner_radius=Spacing.BUTTON_RADIUS
        ).pack(side="right", padx=Spacing.MD)
        
        # Initial State
        self._update_ui_state()

    def _build_glossary_tab(self, parent):
        from .glossary_tab import GlossaryTab
        tab = GlossaryTab(parent, self.translation_service.glossary_manager)
        tab.pack(fill="both", expand=True, padx=Spacing.SM, pady=Spacing.SM)



    def _build_system_tab(self, parent):
        """Placeholder for system settings."""
        ctk.CTkLabel(
            parent, text="Cấu hình Giao diện", 
            font=Fonts.H3, text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=Spacing.LG, padx=Spacing.LG)
        
        # Theme
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", padx=Spacing.LG, pady=Spacing.SM)
        ctk.CTkLabel(theme_frame, text="Chế độ màu:", width=100, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.theme_var = tk.StringVar(value=ctk.get_appearance_mode())
        self.theme_menu = ctk.CTkSegmentedButton(
            theme_frame, variable=self.theme_var,
            values=["Dark", "Light", "System"],
            command=self._change_theme
        )
        self.theme_menu.pack(side="left")

    def _update_ui_state(self):
        engine = self.engine_var.get()
        if engine == "cloud":
            self.local_frame.pack_forget()
            self.cloud_frame.pack(fill="x", pady=Spacing.MD, ipady=Spacing.SM)
            self._update_cloud_ui()
        else:
            self.cloud_frame.pack_forget()
            self.local_frame.pack(fill="x", pady=Spacing.MD, ipady=Spacing.SM)

    def _update_cloud_ui(self):
        provider = self.provider_var.get()
        if provider == "ai_studio":
            self.vertex_frame.pack_forget()
            self.ai_studio_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
            self.cloud_model_menu.configure(values=self.STUDIO_MODELS)
            if self.cloud_model_var.get() not in self.STUDIO_MODELS:
                self.cloud_model_var.set(self.STUDIO_MODELS[0])
        else:
            self.ai_studio_frame.pack_forget()
            self.vertex_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
            self.cloud_model_menu.configure(values=self.VERTEX_MODELS)
            if self.cloud_model_var.get() not in self.VERTEX_MODELS:
                self.cloud_model_var.set(self.VERTEX_MODELS[0])

    def _toggle_key_visibility(self):
        self.show_api_key = not self.show_api_key
        self.api_key_entry.configure(show="" if self.show_api_key else "•")
        self.btn_toggle.configure(text="🙈" if self.show_api_key else "👁")

    def _browse_model(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("GGUF Model", "*.gguf")])
        if file_path:
            self.model_path_var.set(file_path)

    def _browse_json(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("JSON Key", "*.json")])
        if file_path:
            import shutil
            from pathlib import Path
            dest_dir = Path("config/keys")
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / Path(file_path).name
            try:
                shutil.copy2(file_path, dest_file)
                self.v_json_var.set(str(dest_file.absolute()))
                self.status_label.configure(text="✓ Đã copy JSON key vào dự án", text_color=Colors.SUCCESS)
                
                # Auto-add to .gitignore
                gitignore_path = Path(".gitignore")
                ignore_rule = "config/keys/"
                content = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
                if ignore_rule not in content:
                    with open(gitignore_path, "a", encoding="utf-8") as f:
                        f.write(f"\n# GCP Keys\n{ignore_rule}\n")
            except Exception as e:
                self.status_label.configure(text=f"✗ Lỗi copy file: {e}", text_color=Colors.DANGER)

    def _change_theme(self, new_theme: str):
        ctk.set_appearance_mode(new_theme)
        self.settings_manager.set("theme", new_theme)

    def _save_settings(self):
        # Common
        self.settings_manager.set("translation_engine", self.engine_var.get())
        try: self.settings_manager.set("chunk_size", int(self.chunk_size_var.get()))
        except: pass
        try: self.settings_manager.set("chunk_delay", float(self.delay_var.get()))
        except: pass
        
        # Cloud
        self.settings_manager.set("cloud_provider", self.provider_var.get())
        self.settings_manager.set("vertex_project_id", self.v_proj_var.get().strip())
        self.settings_manager.set("vertex_region", self.v_reg_var.get().strip())
        self.settings_manager.set("vertex_credentials_path", self.v_json_var.get().strip())
        self.settings_manager.set("vertex_api_key", self.v_api_key_var.get().strip())
        self.settings_manager.set_api_key(self.api_key_var.get().strip())
        self.settings_manager.set("cloud_model_name", self.cloud_model_var.get())

        # Reload cloud client với cấu hình mới
        self.translation_service.cloud_client.setup()
        
        # Local
        self.settings_manager.set("local_model_path", self.model_path_var.get())
        self.settings_manager.set("current_style", self.style_var.get())
        try: self.settings_manager.set("n_gpu_layers", int(self.gpu_layers_var.get()))
        except: pass
        
        self.status_label.configure(text="✓ Đã lưu cài đặt thành công!", text_color=Colors.SUCCESS)
        self.after(2000, lambda: self.status_label.configure(text=""))

    def _test_connection(self):
        # Always save current settings first to apply them to CloudAIClient
        self._save_settings()
        
        engine = self.engine_var.get()
        self.status_label.configure(text="⏳ Đang kiểm tra...", text_color=Colors.WARNING)
        self.update()
        
        if engine == "cloud":
            try:
                res = self.translation_service.cloud_client.translate_chunk("Hello")
                if res[0]:
                     self.status_label.configure(text="✓ Cloud API/Vertex OK", text_color=Colors.SUCCESS)
                else:
                     self.status_label.configure(text=f"✗ {res[2]}", text_color=Colors.DANGER)
            except Exception as e:
                self.status_label.configure(text=f"✗ {e}", text_color=Colors.DANGER)
        else: 
            model_path = self.model_path_var.get()
            if not model_path:
                 self.status_label.configure(text="✗ Chưa chọn file model", text_color=Colors.DANGER)
                 return
            try:
                from ...core.local_genai import LocalGenAI
                self.status_label.configure(text="⏳ Đang load model vào GPU...", text_color=Colors.WARNING)
                self.update()
                
                gpu_layers = int(self.gpu_layers_var.get())
                LocalGenAI.get_instance().load_model(model_path, n_gpu_layers=gpu_layers)
                
                self.status_label.configure(text="✓ Model Loaded Ready!", text_color=Colors.SUCCESS)
            except Exception as e:
                 self.status_label.configure(text=f"✗ Lỗi: {e}", text_color=Colors.DANGER)
