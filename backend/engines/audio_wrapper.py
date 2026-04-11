import argparse
import json
import sys

import jiwer
import torch
from datasets import load_dataset
from faster_whisper import WhisperModel


def run_audio_eval(model_size: str, limit: int, run_id: str):

    # Normalize model string — faster-whisper only accepts size strings like
    # "tiny", "base", "small", "medium", "large-v3".
    # The frontend sends "openai/whisper-tiny" (HF repo format); strip the prefix.
    for prefix in ("openai/whisper-", "whisper-"):
        if model_size.startswith(prefix):
            model_size = model_size[len(prefix):]
            break

    # Hardware-aware device selection
    if torch.cuda.is_available():
        free_vram_gb = torch.cuda.mem_get_info()[0] / 1024**3
        device = "cuda" if free_vram_gb > 0.5 else "cpu"
        compute_type = "int8_float16" if device == "cuda" else "int8"
        print(f"[audio_eval] Device: {device} | Free VRAM: {free_vram_gb:.2f}GB")
    else:
        device = "cpu"
        compute_type = "int8"
        print("[audio_eval] Device: cpu")

    # Load model — downloads Systran/faster-whisper-{size} from HF on first run
    print(f"[audio_eval] Loading whisper-{model_size}...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    # Stream LibriSpeech test-clean — no full download required
    print(f"[audio_eval] Streaming LibriSpeech test-clean (limit={limit})...")
    ds = load_dataset(
        "librispeech_asr",
        "clean",
        split="test",
        streaming=True,
    )

    references = []
    hypotheses = []

    for i, sample in enumerate(ds):
        if i >= limit:
            break

        audio_array = sample["audio"]["array"]  # datasets decodes automatically
        reference = sample["text"].lower().strip()

        segments, _ = model.transcribe(audio_array, beam_size=1)
        hypothesis = " ".join(s.text for s in segments).lower().strip()

        references.append(reference)
        hypotheses.append(hypothesis)

        print(f"[audio_eval] {i+1}/{limit} | REF: {reference[:60]}")
        print(f"[audio_eval] {i+1}/{limit} | HYP: {hypothesis[:60]}")

    # jiwer.wer(reference, hypothesis) — reference MUST be first arg
    wer_score = jiwer.wer(references, hypotheses)
    accuracy = round(1 - wer_score, 4)
    wer_score = round(wer_score, 4)

    # Sanity guard — reversed args yield WER > 1.0 in edge cases
    assert 0.0 <= wer_score <= 2.0, f"Suspicious WER value: {wer_score}"

    print(f"[audio_eval] WER: {wer_score} | Accuracy: {accuracy}")

    # Build unified EvalResult schema matching schemas.py / api.ts.
    # accuracy is the primary bar-chart metric (higher=better).
    # wer is kept as supplementary context (Results.tsx inverts its bar).
    result = {
        "run_id": run_id,
        "model": f"whisper-{model_size}",
        "modality": "audio",
        "task": "librispeech",
        "engine": "faster-whisper",
        "metrics": {
            "accuracy": accuracy,
            "wer": wer_score,
        },
        "trajectory": []
    }

    # Emit the sentinel line that eval_runner.py scrapes from stdout
    print(f"[EVAL_RESULT] {json.dumps(result)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="base")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--run_id", required=True)
    # Accept --task / --modality from eval_runner for interface consistency
    parser.add_argument("--task", default="librispeech")
    parser.add_argument("--modality", default="audio")
    args = parser.parse_args()
    run_audio_eval(args.model, args.limit, args.run_id)
