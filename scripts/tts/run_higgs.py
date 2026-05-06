"""Genereer Genesis 1 met Higgs Audio v2 (voice-cloned vanuit Artlist sample).

Run met .venv-higgs geactiveerd:
    source .venv-higgs/bin/activate
    python -m scripts.tts.run_higgs

API-referentie: vendor/higgs-audio/boson_multimodal/serve/serve_engine.py
Voice-cloning: user-message (transcript) + assistant-message (AudioContent) patroon.
HiggsAudioResponse.audio is een numpy array; opgeslagen met soundfile.
"""
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path


def _patch_torchaudio_for_blackwell() -> None:
    """Patch torchaudio Spectrogram/MelSpectrogram voor RTX 5070 (sm_120 / Blackwell).

    PyTorch cu128 bevat geen nvrtc-kernels voor sm_120, waardoor torchaudio.transforms
    crasht met 'nvrtc: invalid value for --gpu-architecture'. Workaround: spectrogram
    op CPU berekenen en resultaat naar GPU verplaatsen.
    """
    try:
        import torch
        import torchaudio.transforms as T

        if not torch.cuda.is_available():
            return

        cap = torch.cuda.get_device_capability(0)
        if cap < (12, 0):
            return  # niet sm_120+, geen patch nodig

        _orig_spec = T.Spectrogram.forward
        _orig_mel = T.MelSpectrogram.forward

        def _spec_cpu_fallback(self, waveform):  # type: ignore[override]
            dev = waveform.device
            if dev.type == "cuda":
                return _orig_spec(self.to("cpu"), waveform.cpu()).to(dev)
            return _orig_spec(self, waveform)

        def _mel_cpu_fallback(self, waveform):  # type: ignore[override]
            dev = waveform.device
            if dev.type == "cuda":
                return _orig_mel(self.to("cpu"), waveform.cpu()).to(dev)
            return _orig_mel(self, waveform)

        T.Spectrogram.forward = _spec_cpu_fallback  # type: ignore[method-assign]
        T.MelSpectrogram.forward = _mel_cpu_fallback  # type: ignore[method-assign]
        print("Blackwell-patch actief: Spectrogram/MelSpectrogram via CPU proxy.")
    except Exception as exc:
        print(f"Waarschuwing: Blackwell-patch mislukt ({exc}); ga door zonder patch.")


def extract_genesis_1() -> str:
    data = json.loads(Path("data/genesis/1.json").read_text(encoding="utf-8"))
    return " ".join(v["text2026"].strip() for v in data["verses"] if v.get("text2026"))


def _normalize_text(text: str) -> str:
    """Basale normalisatie: verwijder overbodige witruimte en zorg voor eindpunctatie."""
    # Meerdere spaties / regeleinden samenvoegen
    lines = text.split("\n")
    text = " ".join(" ".join(line.split()) for line in lines if line.strip())
    text = text.strip()
    # Zorg dat tekst eindigt op een zinseinde
    if not text.endswith((".", "!", "?", ",", ";", '"', "'")):
        text += "."
    return text


def _chunk_text(text: str, max_words: int = 150) -> list[str]:
    """Verdeel tekst in chunks van maximaal max_words woorden op woordgrens."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words])
        if not chunk.endswith((".", "!", "?", ",", ";", '"', "'")):
            chunk += "."
        chunks.append(chunk)
    return chunks


def main() -> None:
    _patch_torchaudio_for_blackwell()

    from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine
    from boson_multimodal.data_types import ChatMLSample, Message, AudioContent

    import numpy as np
    import soundfile as sf
    import torch

    sample_wav = Path("audio/_pilot/_sample/sample.wav")
    sample_txt = Path("audio/_pilot/_sample/sample.txt")
    if not sample_wav.exists() or not sample_txt.exists():
        raise SystemExit("Voice-sample of transcript ontbreekt. Run eerst Task 2.")

    reference_text = sample_txt.read_text(encoding="utf-8").strip()
    raw_text = extract_genesis_1()
    text = _normalize_text(raw_text)
    print(f"Tekst-lengte: {len(text)} chars")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # HiggsAudioServeEngine laadt model + audio-tokenizer en
    # vangt CUDA-graphs bij initialisatie (eenmalig, traag).
    #
    # NOOT: het HuggingFace-model 'bosonai/higgs-audio-v2-generation-3B-base'
    # is in april 2026 bijgewerkt naar v2.5-architectuur (model_type=higgs_audio_v2,
    # HiggsAudioV2ForConditionalGeneration). De GitHub-code ondersteunt alleen
    # model_type=higgs_audio (HiggsAudioModel). We gebruiken daarom de lokale
    # kopie van het originele v2-model (revision 1a28afb) die naar /tmp/higgs_v2_model
    # is gedownload.
    import os
    local_model = "/tmp/higgs_v2_model"
    model_name = local_model if os.path.isdir(local_model) else "bosonai/higgs-audio-v2-generation-3B-base"
    print(f"Model pad: {model_name}")

    # De v2-code (HiggsAudioTokenizer) verwacht een config met n_filters/D/ratios
    # en model.pth (806 MB). De huidige HF-snapshot van higgs-audio-v2-tokenizer
    # bevat een v2.5-config (HiggsAudioV2TokenizerModel) met een ander schema.
    # We gebruiken daarom revision 001371b8 (v2-compatibel), gedownload naar /tmp.
    V2_TOKENIZER = "/tmp/higgs_v2_tokenizer"
    tokenizer_path = V2_TOKENIZER if os.path.isdir(V2_TOKENIZER) else "bosonai/higgs-audio-v2-tokenizer"
    print(f"Tokenizer pad: {tokenizer_path}")

    # RTX 5070 heeft 12 GB VRAM. Het 3B-model in bfloat16 gebruikt ~11 GB,
    # waarna er nauwelijks ruimte meer is voor KV-caches en de audio-tokenizer.
    # Oplossingen:
    # 1. Audio-tokenizer op CPU laden (806 MB bespaard op GPU).
    # 2. 8-bit quantisatie voor het hoofdmodel: ~5.7 GB i.p.v. ~11 GB.
    # 3. Geen StaticCache / CUDA-graph-capture: bespaart extra GB's.
    # 4. Patch generate() om past_key_values_buckets=None te gebruiken.

    # Patch 1: audio-tokenizer op CPU
    import boson_multimodal.audio_processing.higgs_audio_tokenizer as _tok_mod
    import boson_multimodal.serve.serve_engine as _se_mod
    _orig_load_tokenizer = _tok_mod.load_higgs_audio_tokenizer

    def _cpu_tokenizer_loader(tokenizer_name_or_path, device="cuda"):
        print("Tokenizer wordt op CPU geladen (VRAM-besparingsmodus).")
        return _orig_load_tokenizer(tokenizer_name_or_path, device="cpu")

    _tok_mod.load_higgs_audio_tokenizer = _cpu_tokenizer_loader
    _se_mod.load_higgs_audio_tokenizer = _cpu_tokenizer_loader

    # Patch 2: 8-bit model-loading via bitsandbytes
    from boson_multimodal.model.higgs_audio import HiggsAudioModel
    from transformers import BitsAndBytesConfig

    _orig_from_pretrained = HiggsAudioModel.from_pretrained.__func__  # type: ignore[attr-defined]

    @classmethod  # type: ignore[misc]
    def _patched_from_pretrained(cls, pretrained_model_name_or_path, **kwargs):  # type: ignore[override]
        bnb_config = BitsAndBytesConfig(load_in_8bit=True)
        kwargs["quantization_config"] = bnb_config
        kwargs["device_map"] = "cuda:0"
        kwargs.pop("torch_dtype", None)
        model = _orig_from_pretrained(cls, pretrained_model_name_or_path, **kwargs)
        # .to(device) moet geen fout geven voor 8-bit models
        _orig_to = model.to

        def _safe_to(device_or_dtype=None, **to_kwargs):
            if isinstance(device_or_dtype, str) or (hasattr(device_or_dtype, "type") and not callable(device_or_dtype)):
                return model  # al op GPU via device_map
            return _orig_to(device_or_dtype, **to_kwargs)

        model.to = _safe_to  # type: ignore[method-assign]
        return model

    HiggsAudioModel.from_pretrained = _patched_from_pretrained  # type: ignore[method-assign]

    # Patch 3: geen CUDA-graph-capture (werkt niet met 8-bit)
    HiggsAudioModel.capture_model = lambda self, *args, **kwargs: None  # type: ignore[method-assign]

    # Patch 4: pas HiggsAudioServeEngine.generate() aan om past_key_values_buckets=None
    # te gebruiken wanneer de dict leeg is (geen StaticCache).
    _orig_generate = _se_mod.HiggsAudioServeEngine.generate

    def _patched_generate(self, chat_ml_sample, max_new_tokens, **kwargs):
        # Gebruik None i.p.v. lege dict voor past_key_values_buckets
        with torch.no_grad():
            inputs = self._prepare_inputs(chat_ml_sample)
            prompt_token_ids = inputs["input_ids"][0].cpu().numpy()
            # Geen static kv-cache reset (want die zijn leeg)
            stop_strings = kwargs.pop("stop_strings", ["<|end_of_text|>", "<|eot_id|>"])
            temperature = kwargs.pop("temperature", 0.7)
            top_k = kwargs.pop("top_k", None)
            top_p = kwargs.pop("top_p", 0.95)
            ras_win_len = kwargs.pop("ras_win_len", 7)
            ras_win_max_num_repeat = kwargs.pop("ras_win_max_num_repeat", 2)
            seed = kwargs.pop("seed", None)
            if ras_win_len is not None and ras_win_len <= 0:
                ras_win_len = None
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                use_cache=True,
                stop_strings=stop_strings,
                tokenizer=self.tokenizer,
                do_sample=False if temperature == 0.0 else True,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                past_key_values_buckets=None,  # standaard dynamische KV-cache
                ras_win_len=ras_win_len,
                ras_win_max_num_repeat=ras_win_max_num_repeat,
                seed=seed,
            )
            if len(outputs[1]) > 0:
                from boson_multimodal.model.higgs_audio.utils import revert_delay_pattern
                import numpy as np
                wv_list = []
                for output_audio in outputs[1]:
                    vq_code = revert_delay_pattern(output_audio).clip(0, self.audio_codebook_size - 1)[:, 1:-1]
                    wv_numpy = self.audio_tokenizer.decode(vq_code.unsqueeze(0))[0, 0]
                    wv_list.append(wv_numpy)
                wv_numpy = np.concatenate(wv_list)
            else:
                wv_numpy = None
            generated_text_tokens = outputs[0][0].cpu().numpy()[len(prompt_token_ids):]
            generated_text = self.tokenizer.decode(generated_text_tokens)
            generated_audio_tokens = outputs[1][0].cpu().numpy() if len(outputs[1]) > 0 else np.array([])
            from boson_multimodal.serve.serve_engine import HiggsAudioResponse
            return HiggsAudioResponse(
                audio=wv_numpy,
                generated_audio_tokens=generated_audio_tokens,
                sampling_rate=self.audio_tokenizer.sampling_rate,
                generated_text=generated_text,
            )

    _se_mod.HiggsAudioServeEngine.generate = _patched_generate

    # kv_cache_lengths=[] = geen StaticCache-allocaties
    engine = HiggsAudioServeEngine(
        model_name_or_path=model_name,
        audio_tokenizer_name_or_path=tokenizer_path,
        device=device,
        kv_cache_lengths=[],
    )

    out_dir = Path("audio/_pilot/higgs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_wav = out_dir / "genesis-1.wav"
    out_mp3 = out_dir / "genesis-1.mp3"

    # Verdeel Genesis 1 in beheersbare chunks (max 150 woorden per chunk)
    # om VRAM-overloop te voorkomen en kwaliteit te bewaken.
    chunks = _chunk_text(text, max_words=150)
    print(f"Genereer {len(chunks)} chunk(s)...")

    system_message = Message(
        role="system",
        content=(
            "Generate audio following instruction.\n\n"
            "<|scene_desc_start|>\nAudio is recorded from a quiet room.\n<|scene_desc_end|>"
        ),
    )

    all_audio_parts: list[np.ndarray] = []
    sampling_rate: int = 24000  # default; wordt overschreven door engine-response

    for idx, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {idx}/{len(chunks)}: {len(chunk.split())} woorden...")

        # Voice-cloning: user geeft referentie-transcript, assistant antwoordt
        # met de overeenkomstige audio. Daarna vraagt de volgende user-message
        # om de gewenste tekst te genereren.
        messages = [
            system_message,
            Message(role="user", content=reference_text),
            Message(
                role="assistant",
                content=AudioContent(audio_url=str(sample_wav.absolute())),
            ),
            Message(role="user", content=chunk),
        ]
        sample = ChatMLSample(messages=messages)

        response = engine.generate(
            chat_ml_sample=sample,
            max_new_tokens=4096,
            temperature=0.3,
            top_p=0.95,
            top_k=50,
        )

        if response.audio is not None and len(response.audio) > 0:
            all_audio_parts.append(response.audio)
            sampling_rate = response.sampling_rate
        else:
            print(f"  WAARSCHUWING: chunk {idx} leverde geen audio op.")

    if not all_audio_parts:
        raise SystemExit("Geen audio gegenereerd. Controleer de engine-logs.")

    # Aaneenschakelen en opslaan als WAV
    combined = np.concatenate(all_audio_parts)
    sf.write(str(out_wav), combined, sampling_rate)
    print(f"WAV opgeslagen: {out_wav} ({len(combined)/sampling_rate:.1f}s)")

    # WAV → MP3 (128 kbps mono)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(out_wav),
            "-codec:a", "libmp3lame", "-b:a", "128k", "-ac", "1",
            str(out_mp3),
        ],
        check=True,
    )
    out_wav.unlink()
    print(f"Klaar: {out_mp3}")


if __name__ == "__main__":
    main()
