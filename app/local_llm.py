
import json
import os
from pathlib import Path
from threading import Lock

_MODEL = None
_MODEL_PATH = None
_MODEL_LOCK = Lock()


def get_model():
    """Load the local GGUF model once per Python process."""
    global _MODEL, _MODEL_PATH

    model_path = os.getenv("LOCAL_GGUF_PATH", "").strip()

    if not model_path:
        raise RuntimeError(
            "LOCAL_GGUF_PATH is not configured. "
            "Set it to your local GGUF model file."
        )

    path = Path(model_path).expanduser()

    if not path.is_file():
        raise RuntimeError(
            f"GGUF model file was not found: {path}"
        )

    with _MODEL_LOCK:
        if _MODEL is not None and _MODEL_PATH == str(path.resolve()):
            return _MODEL

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed in this environment."
            ) from exc

        try:
            gpu_layers = int(os.getenv("LLAMA_GPU_LAYERS", "0"))
            context_size = int(os.getenv("LLAMA_CONTEXT_SIZE", "4096"))

            model = Llama(
                model_path=str(path.resolve()),
                n_ctx=context_size,
                n_gpu_layers=gpu_layers,
                verbose=False,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not load the local GGUF model: {exc}"
            ) from exc

        _MODEL = model
        _MODEL_PATH = str(path.resolve())

        return _MODEL


def generate_json(system_prompt: str, user_prompt: str) -> dict:
    """Generate and parse a JSON object using local inference."""
    model = get_model()

    try:
        response = model.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=900,
        )

        content = response["choices"][0]["message"]["content"]

        if not isinstance(content, str) or not content.strip():
            raise ValueError("The model returned empty output.")

        result = json.loads(content)

        if not isinstance(result, dict):
            raise ValueError("Expected a JSON object.")

        return result

    except Exception as exc:
        raise RuntimeError(
            f"Local LLM inference or JSON parsing failed: {exc}"
        ) from exc
