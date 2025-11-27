"""
Main application window using customtkinter
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional
import threading


class MainWindow(ctk.CTk):
    """Main Dayflow window"""

    def __init__(self, app_controller):
        super().__init__()

        self.app = app_controller
        self.config = app_controller.config

        # Window setup
        self.title("Dayflow - 自动跟踪您的一天")
        width = self.config.get('window_width', 1200)
        height = self.config.get('window_height', 800)
        self.geometry(f"{width}x{height}")

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create UI
        self._create_ui()

        # Update timeline periodically
        self._update_timeline()
        self._schedule_update()

    def _create_ui(self):
        """Create the main UI layout"""
        # Top bar
        self.top_bar = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.top_bar.pack(fill="x", padx=0, pady=0)

        # Title
        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="📅 Dayflow",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=15)

        # Recording status
        self.status_label = ctk.CTkLabel(
            self.top_bar,
            text="⏸️  未录制",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left", padx=10)

        # Record button
        self.record_button = ctk.CTkButton(
            self.top_bar,
            text="🎥 开始录制",
            command=self._toggle_recording,
            width=150,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.record_button.pack(side="right", padx=20)

        # Analyze Now button
        self.analyze_button = ctk.CTkButton(
            self.top_bar,
            text="⚡ 立即分析",
            command=self._analyze_now,
            width=130,
            height=35,
            fg_color="green"
        )
        self.analyze_button.pack(side="right", padx=10)

        # Settings button
        self.settings_button = ctk.CTkButton(
            self.top_bar,
            text="⚙️  设置",
            command=self._show_settings,
            width=120,
            height=35,
            fg_color="gray"
        )
        self.settings_button.pack(side="right", padx=10)

        # Main content area
        self.content = ctk.CTkFrame(self)
        self.content.pack(fill="both", expand=True, padx=20, pady=10)

        # Timeline header
        today_str = datetime.now().strftime('%Y年%m月%d日')
        self.timeline_header = ctk.CTkLabel(
            self.content,
            text=f"今日时间线 - {today_str}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.timeline_header.pack(pady=(10, 20))

        # Scrollable timeline
        self.timeline_scroll = ctk.CTkScrollableFrame(
            self.content,
            label_text=""
        )
        self.timeline_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Update recording status
        self._update_status()

    def _toggle_recording(self):
        """Toggle recording on/off"""
        if self.app.is_recording:
            self.app.stop_recording()
        else:
            self.app.start_recording()
        self._update_status()

    def _analyze_now(self):
        """Trigger immediate analysis"""
        self.analyze_button.configure(state="disabled", text="⏳ 分析中...")

        def analyze_thread():
            self.app.analyze_now()
            self.after(0, lambda: self.analyze_button.configure(
                state="normal", text="⚡ 立即分析"
            ))
            self.after(0, self._update_timeline)

        threading.Thread(target=analyze_thread, daemon=True).start()

    def _show_settings(self):
        """Show settings dialog"""
        SettingsDialog(self, self.config, self.app)

    def _update_status(self):
        """Update recording status display"""
        if self.app.is_recording:
            self.status_label.configure(text="🟢 录制中")
            self.record_button.configure(
                text="⏹️  停止录制",
                fg_color="red"
            )
        else:
            self.status_label.configure(text="⏸️  未录制")
            self.record_button.configure(
                text="🎥 开始录制",
                fg_color=["#3B8ED0", "#1F6AA5"]
            )

    def _update_timeline(self):
        """Update timeline cards from database"""
        # Clear existing cards
        for widget in self.timeline_scroll.winfo_children():
            widget.destroy()

        # Get timeline cards for today
        cards = self.app.storage.get_timeline_cards_for_today()

        if not cards:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self.timeline_scroll,
                text="尚无时间线卡片。\n开始录制以构建您的时间线！",
                font=ctk.CTkFont(size=16),
                text_color="gray"
            )
            empty_label.pack(pady=50)
            return

        # Display cards
        for card in cards:
            self._create_timeline_card(card)

    def _create_timeline_card(self, card):
        """Create a timeline card widget"""
        # Card frame
        card_frame = ctk.CTkFrame(
            self.timeline_scroll,
            corner_radius=10,
            border_width=2,
            border_color=card.get('color', '#757575')
        )
        card_frame.pack(fill="x", pady=8, padx=5)

        # Time range
        start_dt = datetime.fromtimestamp(card['start_time'])
        end_dt = datetime.fromtimestamp(card['end_time'])
        time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"

        time_label = ctk.CTkLabel(
            card_frame,
            text=time_str,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        time_label.pack(anchor="w", padx=15, pady=(10, 5))

        # Title
        title_label = ctk.CTkLabel(
            card_frame,
            text=card['title'],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w", padx=15, pady=5)

        # Category
        category_label = ctk.CTkLabel(
            card_frame,
            text=f"📁 {card.get('category', '其他')}",
            font=ctk.CTkFont(size=12),
            text_color=card.get('color', '#757575')
        )
        category_label.pack(anchor="w", padx=15, pady=5)

        # Summary
        if card.get('summary'):
            summary_label = ctk.CTkLabel(
                card_frame,
                text=card['summary'],
                font=ctk.CTkFont(size=14),
                wraplength=700,
                justify="left"
            )
            summary_label.pack(anchor="w", padx=15, pady=(5, 15))

    def _schedule_update(self):
        """Schedule periodic timeline updates"""
        self._update_timeline()
        self.after(30000, self._schedule_update)  # Update every 30 seconds


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window"""

    def __init__(self, parent, config, app):
        super().__init__(parent)

        self.config = config
        self.app = app

        self.title("Dayflow 设置")
        self.geometry("600x500")

        # Create settings UI
        self._create_ui()

    def _create_ui(self):
        """Create settings UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️  设置",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # LLM Provider section
        provider_frame = ctk.CTkFrame(scroll_frame)
        provider_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            provider_frame,
            text="AI 提供商",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)

        # Provider selection
        self.provider_var = ctk.StringVar(value=self.config.get('llm_provider', 'gemini'))

        provider_radio_frame = ctk.CTkFrame(provider_frame, fg_color="transparent")
        provider_radio_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkRadioButton(
            provider_radio_frame,
            text="Google Gemini (云端)",
            variable=self.provider_var,
            value="gemini",
            command=self._on_provider_change
        ).pack(anchor="w", pady=5)

        ctk.CTkRadioButton(
            provider_radio_frame,
            text="Ollama (本地)",
            variable=self.provider_var,
            value="ollama",
            command=self._on_provider_change
        ).pack(anchor="w", pady=5)

        ctk.CTkRadioButton(
            provider_radio_frame,
            text="OpenAI 兼容",
            variable=self.provider_var,
            value="openai",
            command=self._on_provider_change
        ).pack(anchor="w", pady=5)

        # Gemini API Key
        self.gemini_frame = ctk.CTkFrame(provider_frame)
        self.gemini_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            self.gemini_frame,
            text="Gemini API 密钥：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=5)

        self.api_key_entry = ctk.CTkEntry(
            self.gemini_frame,
            width=400,
            show="*",
            placeholder_text="输入您的 Gemini API 密钥"
        )
        self.api_key_entry.pack(fill="x", pady=5)
        self.api_key_entry.insert(0, self.config.get('gemini_api_key', ''))

        # Ollama settings
        self.ollama_frame = ctk.CTkFrame(provider_frame)
        self.ollama_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            self.ollama_frame,
            text="Ollama 基础 URL：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=5)

        self.ollama_url_entry = ctk.CTkEntry(
            self.ollama_frame,
            width=400,
            placeholder_text="http://localhost:11434"
        )
        self.ollama_url_entry.pack(fill="x", pady=5)
        self.ollama_url_entry.insert(0, self.config.get('ollama_base_url', 'http://localhost:11434'))

        # OpenAI settings
        self.openai_frame = ctk.CTkFrame(provider_frame)

        # Vision model settings
        vision_section = ctk.CTkFrame(self.openai_frame)
        vision_section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            vision_section,
            text="🖼️  视觉模型设置",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)

        ctk.CTkLabel(
            vision_section,
            text="视觉模型 API 密钥：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=15, pady=5)

        self.vision_api_key_entry = ctk.CTkEntry(
            vision_section,
            width=400,
            show="*",
            placeholder_text="输入视觉模型的 API 密钥"
        )
        self.vision_api_key_entry.pack(fill="x", padx=15, pady=5)
        self.vision_api_key_entry.insert(0, self.config.get('openai_vision_api_key', self.config.get('openai_api_key', '')))

        ctk.CTkLabel(
            vision_section,
            text="视觉模型 基础 URL：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=15, pady=5)

        self.vision_base_url_entry = ctk.CTkEntry(
            vision_section,
            width=400,
            placeholder_text="https://api.openai.com/v1"
        )
        self.vision_base_url_entry.pack(fill="x", padx=15, pady=5)
        self.vision_base_url_entry.insert(0, self.config.get('openai_vision_base_url', self.config.get('openai_base_url', 'https://api.openai.com/v1')))

        ctk.CTkLabel(
            vision_section,
            text="视觉模型名称：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=15, pady=5)

        self.vision_model_entry = ctk.CTkEntry(
            vision_section,
            width=400,
            placeholder_text="gpt-4o, claude-3-5-sonnet-20241022, qwen-vl-plus"
        )
        self.vision_model_entry.pack(fill="x", padx=15, pady=5)
        self.vision_model_entry.insert(0, self.config.get('openai_vision_model', 'gpt-4o'))

        # Text model settings
        text_section = ctk.CTkFrame(self.openai_frame)
        text_section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            text_section,
            text="📝 文本模型设置",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)

        ctk.CTkLabel(
            text_section,
            text="文本模型 API 密钥：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=15, pady=5)

        self.text_api_key_entry = ctk.CTkEntry(
            text_section,
            width=400,
            show="*",
            placeholder_text="输入文本模型的 API 密钥"
        )
        self.text_api_key_entry.pack(fill="x", padx=15, pady=5)
        self.text_api_key_entry.insert(0, self.config.get('openai_text_api_key', self.config.get('openai_api_key', '')))

        ctk.CTkLabel(
            text_section,
            text="文本模型 基础 URL：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=15, pady=5)

        self.text_base_url_entry = ctk.CTkEntry(
            text_section,
            width=400,
            placeholder_text="https://api.openai.com/v1"
        )
        self.text_base_url_entry.pack(fill="x", padx=15, pady=5)
        self.text_base_url_entry.insert(0, self.config.get('openai_text_base_url', self.config.get('openai_base_url', 'https://api.openai.com/v1')))

        ctk.CTkLabel(
            text_section,
            text="文本模型名称：",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=15, pady=5)

        self.text_model_entry = ctk.CTkEntry(
            text_section,
            width=400,
            placeholder_text="gpt-4o, gpt-4o-mini, claude-3-5-haiku-20241022"
        )
        self.text_model_entry.pack(fill="x", padx=15, pady=5)
        self.text_model_entry.insert(0, self.config.get('openai_text_model', 'gpt-4o'))

        # Help text
        help_label = ctk.CTkLabel(
            self.openai_frame,
            text="💡 提示：可以为视觉和文本模型使用不同的服务（如硅基流动、通义千问等）",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        help_label.pack(anchor="w", padx=15, pady=10)

        # Legacy settings for backward compatibility
        self.openai_api_key_entry = self.vision_api_key_entry
        self.openai_base_url_entry = self.vision_base_url_entry
        self.openai_vision_model_entry = self.vision_model_entry
        self.openai_text_model_entry = self.text_model_entry

        # Show/hide provider-specific settings
        self._on_provider_change()

        # Recording settings
        recording_frame = ctk.CTkFrame(scroll_frame)
        recording_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            recording_frame,
            text="录制设置",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)

        # Retention days
        retention_label = ctk.CTkLabel(
            recording_frame,
            text=f"保留天数：{self.config.get('retention_days', 3)} 天",
            font=ctk.CTkFont(size=14)
        )
        retention_label.pack(anchor="w", padx=15, pady=5)

        self.retention_slider = ctk.CTkSlider(
            recording_frame,
            from_=1,
            to=30,
            number_of_steps=29,
            command=lambda v: retention_label.configure(text=f"保留天数：{int(v)} 天")
        )
        self.retention_slider.pack(fill="x", padx=15, pady=5)
        self.retention_slider.set(self.config.get('retention_days', 3))

        # Save button
        save_button = ctk.CTkButton(
            self,
            text="💾 保存设置",
            command=self._save_settings,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        save_button.pack(pady=20)

    def _on_provider_change(self):
        """Handle provider selection change"""
        provider = self.provider_var.get()
        if provider == 'gemini':
            self.gemini_frame.pack(fill="x", padx=15, pady=10)
            self.ollama_frame.pack_forget()
            self.openai_frame.pack_forget()
        elif provider == 'ollama':
            self.gemini_frame.pack_forget()
            self.ollama_frame.pack(fill="x", padx=15, pady=10)
            self.openai_frame.pack_forget()
        elif provider == 'openai':
            self.gemini_frame.pack_forget()
            self.ollama_frame.pack_forget()
            self.openai_frame.pack(fill="x", padx=15, pady=10)
        else:
            self.gemini_frame.pack_forget()
            self.ollama_frame.pack_forget()
            self.openai_frame.pack_forget()

    def _save_settings(self):
        """Save settings and close dialog"""
        # Save provider
        provider = self.provider_var.get()
        self.config.set('llm_provider', provider)

        # Save API keys
        gemini_api_key = self.api_key_entry.get().strip()
        if gemini_api_key:
            self.config.set('gemini_api_key', gemini_api_key)

        # Save Ollama URL
        ollama_url = self.ollama_url_entry.get().strip()
        if ollama_url:
            self.config.set('ollama_base_url', ollama_url)

        # Save OpenAI settings - new separated configuration
        vision_api_key = self.vision_api_key_entry.get().strip()
        if vision_api_key:
            self.config.set('openai_vision_api_key', vision_api_key)

        vision_base_url = self.vision_base_url_entry.get().strip()
        if vision_base_url:
            self.config.set('openai_vision_base_url', vision_base_url)

        vision_model = self.vision_model_entry.get().strip()
        if vision_model:
            self.config.set('openai_vision_model', vision_model)

        text_api_key = self.text_api_key_entry.get().strip()
        if text_api_key:
            self.config.set('openai_text_api_key', text_api_key)

        text_base_url = self.text_base_url_entry.get().strip()
        if text_base_url:
            self.config.set('openai_text_base_url', text_base_url)

        text_model = self.text_model_entry.get().strip()
        if text_model:
            self.config.set('openai_text_model', text_model)

        # Save legacy settings for backward compatibility
        openai_api_key = self.openai_api_key_entry.get().strip()
        if openai_api_key:
            self.config.set('openai_api_key', openai_api_key)

        openai_base_url = self.openai_base_url_entry.get().strip()
        if openai_base_url:
            self.config.set('openai_base_url', openai_base_url)

        # Save retention
        self.config.set('retention_days', int(self.retention_slider.get()))

        # Reinitialize LLM provider
        self.app.init_llm_provider()

        # Close dialog
        self.destroy()
