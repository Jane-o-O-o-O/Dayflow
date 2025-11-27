"""
主应用程序控制器
协调 Dayflow 的所有组件
"""

from pathlib import Path
from core.config import config
from core.storage import Storage
from core.recorder import ScreenRecorder
from core.cleanup import CleanupService
from ai.gemini_provider import GeminiProvider
from ai.ollama_provider import OllamaProvider
from ai.openai_provider import OpenAIProvider
from analysis.timeline_generator import TimelineGenerator


class AppController:
    """主应用程序控制器"""

    def __init__(self):
        # Core components
        self.config = config
        self.storage = Storage(config.db_path)

        # Recording
        self.recorder = ScreenRecorder(config, self.storage)
        self.is_recording = False

        # Analysis
        self.timeline_generator = TimelineGenerator(config, self.storage)
        self.llm_provider = None

        # Cleanup
        self.cleanup_service = CleanupService(config, self.storage)

        # UI (set later)
        self.window = None
        self.tray_icon = None

        # Initialize LLM provider
        self.init_llm_provider()

    def init_llm_provider(self):
        """根据配置初始化 LLM 提供商"""
        provider_type = self.config.get('llm_provider', 'gemini')

        try:
            if provider_type == 'gemini':
                api_key = self.config.get('gemini_api_key', '')
                if not api_key:
                    print("⚠️  未配置 Gemini API 密钥")
                    self.llm_provider = None
                else:
                    self.llm_provider = GeminiProvider(api_key)
                    print("✅ Gemini 提供商已初始化")
            elif provider_type == 'ollama':
                base_url = self.config.get('ollama_base_url', 'http://localhost:11434')
                model = self.config.get('ollama_model', 'llava')
                self.llm_provider = OllamaProvider(base_url, model)
                print("✅ Ollama 提供商已初始化")
            elif provider_type == 'openai':
                # Get configuration for vision and text models separately
                default_api_key = self.config.get('openai_api_key', '')
                default_base_url = self.config.get('openai_base_url', 'https://api.openai.com/v1')

                vision_api_key = self.config.get('openai_vision_api_key', default_api_key)
                vision_base_url = self.config.get('openai_vision_base_url', default_base_url)
                vision_model = self.config.get('openai_vision_model', 'gpt-4o')

                text_api_key = self.config.get('openai_text_api_key', default_api_key)
                text_base_url = self.config.get('openai_text_base_url', default_base_url)
                text_model = self.config.get('openai_text_model', 'gpt-4o')

                if not (vision_api_key or text_api_key):
                    print("⚠️  未配置 OpenAI API 密钥")
                    self.llm_provider = None
                else:
                    self.llm_provider = OpenAIProvider(
                        default_api_key, default_base_url, vision_model, text_model,
                        vision_api_key, vision_base_url, text_api_key, text_base_url
                    )
                    print(f"✅ OpenAI 提供商已初始化")
                    print(f"   视觉模型：{vision_model} (URL: {vision_base_url})")
                    print(f"   文本模型：{text_model} (URL: {text_base_url})")
            else:
                print(f"❌ 未知的 LLM 提供商：{provider_type}")
                self.llm_provider = None

            # Set provider for timeline generator
            self.timeline_generator.set_llm_provider(self.llm_provider)

        except Exception as e:
            print(f"❌ 初始化 LLM 提供商时出错：{e}")
            self.llm_provider = None

    def start_recording(self):
        """开始屏幕录制"""
        self.recorder.start_recording()
        self.is_recording = True
        self.config.set('recording_enabled', True)

    def stop_recording(self):
        """停止屏幕录制"""
        self.recorder.stop_recording()
        self.is_recording = False
        self.config.set('recording_enabled', False)

    def analyze_now(self):
        """触发立即分析"""
        self.timeline_generator.analyze_now()

    def start_services(self):
        """启动后台服务"""
        # Start timeline generator
        self.timeline_generator.start()

        # Start cleanup service
        self.cleanup_service.start()

        # Auto-start recording if enabled
        if self.config.get('recording_enabled', False):
            self.start_recording()

    def stop_services(self):
        """停止所有后台服务"""
        self.stop_recording()
        self.timeline_generator.stop()
        self.cleanup_service.stop()

    def run(self):
        """运行应用程序"""
        # Import here to avoid circular dependency
        from ui.main_window import MainWindow
        from ui.tray_icon import TrayIcon

        # Start services
        self.start_services()

        # Create and show main window
        self.window = MainWindow(self)

        # Create tray icon
        self.tray_icon = TrayIcon(self)
        self.tray_icon.run()

        # Run main loop
        try:
            self.window.mainloop()
        finally:
            # Cleanup
            self.stop_services()
            if self.tray_icon:
                self.tray_icon.stop()
