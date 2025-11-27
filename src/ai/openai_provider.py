"""
OpenAI-compatible API provider for video analysis
Supports any OpenAI-compatible API endpoint with custom URL and API key
"""

import requests
import base64
import cv2
from pathlib import Path
from typing import List, Dict, Optional
import json


class OpenAIProvider:
    """OpenAI-compatible provider for video analysis"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 vision_model: str = "gpt-4o", text_model: str = "gpt-4o",
                 vision_api_key: str = None, vision_base_url: str = None,
                 text_api_key: str = None, text_base_url: str = None):
        """
        Initialize OpenAI-compatible provider with separate configs for vision and text

        Args:
            api_key: Default API key for authentication (used if specific keys not provided)
            base_url: Default base URL for the API endpoint (used if specific URLs not provided)
            vision_model: Vision model name for analyzing images (default: gpt-4o)
            text_model: Text model name for synthesis (default: gpt-4o)
            vision_api_key: API key specifically for vision model (optional)
            vision_base_url: Base URL specifically for vision model (optional)
            text_api_key: API key specifically for text model (optional)
            text_base_url: Base URL specifically for text model (optional)
        """
        # Vision model configuration
        self.vision_api_key = vision_api_key or api_key
        self.vision_base_url = (vision_base_url or base_url).rstrip('/')
        self.vision_model = vision_model

        # Text model configuration
        self.text_api_key = text_api_key or api_key
        self.text_base_url = (text_base_url or base_url).rstrip('/')
        self.text_model = text_model

        # Default configuration (for backward compatibility)
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

    def _extract_frames(self, video_path: Path, num_frames: int = 10) -> List[bytes]:
        """Extract evenly-spaced frames from video"""
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames == 0:
            cap.release()
            return []

        # Calculate frame indices to extract
        frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Convert to JPEG bytes
                _, buffer = cv2.imencode('.jpg', frame)
                frames.append(buffer.tobytes())

        cap.release()
        return frames

    def _analyze_frame(self, frame_bytes: bytes) -> Optional[str]:
        """Analyze a single frame using vision model"""
        try:
            # Encode frame as base64
            frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')

            # Prepare messages for vision API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe what application or activity is shown in this screenshot. Be concise and specific. Just describe what you see."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{frame_b64}"
                            }
                        }
                    ]
                }
            ]

            # Use vision-specific headers and URL
            vision_headers = {
                "Authorization": f"Bearer {self.vision_api_key}",
                "Content-Type": "application/json"
            }

            # Send to vision-specific OpenAI-compatible API
            response = requests.post(
                f"{self.vision_base_url}/chat/completions",
                json={
                    "model": self.vision_model,
                    "messages": messages,
                    "max_tokens": 100,
                    "temperature": 0.7
                },
                headers=vision_headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"❌ API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"❌ Frame analysis error: {e}")
            return None

    def _synthesize_descriptions(self, descriptions: List[str]) -> Optional[Dict]:
        """Synthesize frame descriptions into timeline card"""
        try:
            # Combine descriptions
            combined = "\n".join([f"- {desc}" for desc in descriptions if desc])

            messages = [
                {
                    "role": "user",
                    "content": f"""Based on these screen activity descriptions, create a summary:

{combined}

Provide a JSON response with:
1. title: A concise title (max 5 words)
2. summary: Brief summary of activities (1-2 sentences)
3. category: Choose from (Work, Communication, Development, Design, Entertainment, Productivity, Research, Social Media, Video, Music, Gaming, Other)

Format as JSON only:
{{"title": "...", "summary": "...", "category": "..."}}"""
                }
            ]

            # Use text-specific headers and URL
            text_headers = {
                "Authorization": f"Bearer {self.text_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.text_base_url}/chat/completions",
                json={
                    "model": self.text_model,
                    "messages": messages,
                    "max_tokens": 200,
                    "temperature": 0.7
                },
                headers=text_headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content'].strip()

                # Try to extract JSON
                if '{' in response_text and '}' in response_text:
                    json_start = response_text.index('{')
                    json_end = response_text.rindex('}') + 1
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)

            return None

        except Exception as e:
            print(f"❌ Synthesis error: {e}")
            return None

    def analyze_video(self, video_path: Path) -> Optional[Dict]:
        """
        Analyze a video file using frame extraction + description

        Returns:
            Dict with 'title', 'summary', 'category'
        """
        try:
            print(f"🎬 Extracting frames from: {video_path.name}")
            frames = self._extract_frames(video_path, num_frames=5)

            if not frames:
                print(f"❌ No frames extracted")
                return None

            print(f"🔍 Analyzing {len(frames)} frames...")
            descriptions = []
            for i, frame_bytes in enumerate(frames):
                desc = self._analyze_frame(frame_bytes)
                if desc:
                    descriptions.append(desc)
                    print(f"  Frame {i+1}/{len(frames)}: {desc[:60]}...")

            if not descriptions:
                print(f"❌ No descriptions generated")
                return None

            print(f"📝 Synthesizing results...")
            result = self._synthesize_descriptions(descriptions)

            if result:
                print(f"✅ Analysis complete: {result.get('title', 'Unknown')}")
                return result
            else:
                # Fallback: create basic result from descriptions
                return {
                    "title": "Screen Activity",
                    "summary": ". ".join(descriptions[:2]),
                    "category": "Other"
                }

        except Exception as e:
            print(f"❌ Video analysis error: {e}")
            return None

    def analyze_batch(self, video_paths: List[Path]) -> List[Dict]:
        """Analyze multiple videos"""
        results = []
        for video_path in video_paths:
            result = self.analyze_video(video_path)
            if result:
                results.append(result)
        return results