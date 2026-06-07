from __future__ import annotations

import argparse
from pathlib import Path

from app.modules.conversation.azure_speech import synthesize_reply_audio
from app.modules.conversation.llm_client import generate_reply
from app.modules.conversation.qwen_stt import _qwen_transcribe_wav_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test Qwen ASR + local reply generation.")
    parser.add_argument("audio_path", help="Path to a wav audio file.")
    parser.add_argument("--scene", default="interview", help="Scene id, e.g. interview/restaurant/meeting.")
    parser.add_argument("--persona", default="strict_interviewer", help="Persona id for the scene.")
    parser.add_argument("--difficulty", type=int, default=1, help="Difficulty level.")
    parser.add_argument("--background", default="", help="Optional custom scenario background.")
    parser.add_argument(
        "--save-reply-audio",
        action="store_true",
        help="Also synthesize assistant reply audio and save it beside the input file.",
    )
    args = parser.parse_args()

    audio_path = Path(args.audio_path)
    wav_bytes = audio_path.read_bytes()

    transcript = _qwen_transcribe_wav_bytes(wav_bytes)
    reply_text = generate_reply(
        scene_id=args.scene,
        persona_id=args.persona,
        difficulty=args.difficulty,
        custom_background=args.background or None,
        history=[],
        user_text=transcript,
    )

    print("=== Transcript ===")
    print(transcript)
    print()
    print("=== Reply ===")
    print(reply_text)

    if args.save_reply_audio:
        reply_audio_b64, audio_format = synthesize_reply_audio(reply_text)
        reply_audio_path = audio_path.with_name(f"{audio_path.stem}.reply.wav")
        reply_audio_path.write_bytes(__import__("base64").b64decode(reply_audio_b64))
        print()
        print("=== Reply Audio ===")
        print(f"saved={reply_audio_path}")
        print(f"format={audio_format}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
