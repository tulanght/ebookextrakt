# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/components/token_usage_panel.py
# Version: 1.0.0
# Author: Antigravity
# Description: UI Component to display API Token usage and estimated cost.
# --------------------------------------------------------------------------------

import customtkinter as ctk
from src.extract_app.modules.ui.theme import Colors, Fonts, Spacing
from src.extract_app.core.eta_calculator import calculate_cost

class TokenUsagePanel(ctk.CTkFrame):
    """
    Displays Token Usage details and estimated cost for a given article 
    or global context. Replicates the design from UI reference (Hình 6).
    """
    def __init__(self, master, db_manager, article_id=None, **kwargs):
        super().__init__(master, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS, border_width=1, border_color=Colors.BORDER, **kwargs)
        self.db_manager = db_manager
        self.article_id = article_id
        
        # Allowed tracking stages
        self.stages = ["translation", "optimize", "extract_glossary", "generate_brief"]
        self.stage_names = {
            "translation": "Dịch thuật (Translation)",
            "optimize": "Tối ưu hóa (Optimize)",
            "extract_glossary": "Gom từ vựng (Glossary)", 
            "generate_brief": "Dàn ý (Content Brief)"
        }
        self.labels = {}
        
        self._build_ui()
        self.refresh()
        
    def _build_ui(self):
        # Header block
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Spacing.MD, pady=(Spacing.MD, Spacing.SM))
        
        ctk.CTkLabel(
            header_frame, text="💲 TOKEN USAGE", 
            font=Fonts.BODY_BOLD, text_color=Colors.SUCCESS
        ).pack(side="left")
        
        self.lbl_cost = ctk.CTkLabel(
            header_frame, text="~ $0.000 USD", 
            font=Fonts.H3, text_color=Colors.WARNING
        )
        self.lbl_cost.pack(side="right")
        
        self.lbl_total_tokens = ctk.CTkLabel(
            header_frame, text="0 tokens", 
            font=Fonts.BODY_BOLD, text_color=Colors.SUCCESS,
            fg_color=Colors.BG_APP, corner_radius=4, padx=8, pady=2
        )
        self.lbl_total_tokens.pack(side="right", padx=Spacing.MD)

        # Body grid for stages
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="x", padx=Spacing.MD, pady=(0, Spacing.MD))
        
        for i, stage in enumerate(self.stages):
            col_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
            col_frame.grid(row=0, column=i, padx=(0, Spacing.XL), sticky="nw")
            
            ctk.CTkLabel(
                col_frame, text=self.stage_names[stage], 
                font=Fonts.SMALL, text_color=Colors.TEXT_MUTED
            ).pack(anchor="w")
            
            lbl_tokens = ctk.CTkLabel(
                col_frame, text="0", 
                font=Fonts.BODY_BOLD, text_color=Colors.PRIMARY
            )
            lbl_tokens.pack(anchor="w")
            
            lbl_in_out = ctk.CTkLabel(
                col_frame, text="in:0  out:0", 
                font=Fonts.TINY, text_color=Colors.TEXT_MUTED
            )
            lbl_in_out.pack(anchor="w")
            
            self.labels[stage] = {
                "tokens": lbl_tokens,
                "in_out": lbl_in_out
            }

    def set_article_id(self, article_id: int):
        self.article_id = article_id
        self.refresh()
        
    def refresh(self):
        if not self.article_id:
            db_records = []
        else:
            db_records = self.db_manager.get_article_api_usage(self.article_id)
            
        stage_totals = {s: {"in": 0, "out": 0, "cost": 0.0} for s in self.stages}
        total_tokens = 0
        total_cost = 0.0
        
        for r in db_records:
            t_in = r.get("tokens_in", 0)
            t_out = r.get("tokens_out", 0)
            engine = r.get("engine", "cloud")
            st = r.get("stage")
            
            # Map transform_website, transform_facebook to optimize
            if st and st.startswith("transform_"):
                st = "optimize"
                
            if st in stage_totals:
                stage_totals[st]["in"] += t_in
                stage_totals[st]["out"] += t_out
                cost = calculate_cost(t_in, t_out, engine)
                stage_totals[st]["cost"] += cost
                
                total_tokens += (t_in + t_out)
                total_cost += cost
                
        # Update UI
        self.lbl_cost.configure(text=f"~ ${total_cost:.4f} USD")
        self.lbl_total_tokens.configure(text=f"{total_tokens:,} tokens")
        
        for stage, data in stage_totals.items():
            t_in = data["in"]
            t_out = data["out"]
            tokens = t_in + t_out
            
            if total_tokens > 0:
                pct = int((tokens / total_tokens) * 100)
            else:
                pct = 0
                
            self.labels[stage]["tokens"].configure(text=f"{tokens:,}  {pct}%" if tokens > 0 else "0")
            
            # Highlight as per UI reference (in: blue-ish, out: orange-ish) though we just use basic text formatting for now
            self.labels[stage]["in_out"].configure(text=f"in:{t_in:,}  out:{t_out:,}")
