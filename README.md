# MoE versus dense on one CPU

A measurement by [Vikawork](https://vikawork.com/): how fast does a mixture-of-experts (MoE) model generate text on a
desktop CPU, compared with a dense model of almost the same size?

| Model (publisher GGUF, Q4_K_M) | Parameters, from Qwen's model cards | Generation, tokens/s |
| --- | --- | ---: |
| [Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B-GGUF/blob/e4d4bafdfb96a411a163846265362aceb0b9c63a/README.md), MoE | 30.5 B total, 3.3 B active per token | 12.23 |
| [Qwen3-32B](https://huggingface.co/Qwen/Qwen3-32B-GGUF/blob/938a7432affaec9157f883a87164e2646ae17555/README.md), dense | 32.8 B, all active | 1.34 |

The MoE model generated **9.1 times** as many tokens per second. Dividing the active parameter counts (32.8 / 3.3)
predicts 9.9 times; the measured ratio is about 8% lower.

This is one model pair on one CPU, measured once on 10 November 2026 (IST). It does not prove why the gap exists: no
memory-traffic counters and no output-quality comparison were collected. [REPORT.md](REPORT.md) has the full
results, the protocol and the limits.

## Setup

- Intel Core i7-7700K, 4 cores / 8 threads, 32 GB RAM, Linux. No GPU used (`-ngl 0`).
- llama.cpp release b12211, the official CPU container image, pinned by digest.
- `llama-bench`: 512-token prompt test and 128-token generation test, 5 timed repetitions each, 4 threads.

## Files

| File | Contents |
| --- | --- |
| [REPORT.md](REPORT.md) | Results, protocol, provenance and limits |
| [measurement.json](measurement.json) | Every sample and the derived ratios |
| [run.json](run.json) | The commands that ran, with their output, timings and file hashes |
| [demo-1/results/](demo-1/results/) | Raw `llama-bench` JSON for each model |
| [demo.yaml](demo.yaml) | The run manifest (JSON syntax): image digest, model files with SHA256, steps |
| [sources.json](sources.json) | Pinned model revisions, download URLs, licences and model-card URLs |
| [provenance/](provenance/) | Snapshots of the model cards, licences, API responses and image metadata |
| [attempts/](attempts/) | Two setup failures before the run; neither reached a benchmark |
| [scripts/download.py](scripts/download.py) | The model download step, with hash verification |

`run.json` and `demo.yaml` contain paths from the test machine (`/fast/vikawork`, `/scratch/vikawork`) and its label
(`oldpc`). They are kept as recorded.

## Run it yourself

You need Docker, about 40 GB of disk and 32 GB of RAM. The dense model takes about 17 minutes on this CPU.

```sh
IMAGE=ghcr.io/ggml-org/llama.cpp:full-b12211@sha256:8960de326dd60972cc4d442531f4efa006416d5896da2a39f0def0b55cbcb0c2
mkdir -p models && cd models
curl -LO https://huggingface.co/Qwen/Qwen3-30B-A3B-GGUF/resolve/e4d4bafdfb96a411a163846265362aceb0b9c63a/Qwen3-30B-A3B-Q4_K_M.gguf
curl -LO https://huggingface.co/Qwen/Qwen3-32B-GGUF/resolve/938a7432affaec9157f883a87164e2646ae17555/Qwen3-32B-Q4_K_M.gguf
sha256sum *.gguf   # compare with sources.json
cd ..

for model in Qwen3-30B-A3B-Q4_K_M Qwen3-32B-Q4_K_M; do
  docker run --rm --network none --mount type=bind,src="$PWD/models",dst=/models,readonly \
    --entrypoint env "$IMAGE" LD_LIBRARY_PATH=/app \
    /app/llama-bench -m /models/$model.gguf -p 512 -n 128 -r 5 -t 4 -ngl 0 -o json
done
```

Set `-t` to your physical core count. Your ratio will differ with the CPU, memory speed and core count.

## Licences

The model cards and licence texts under `provenance/` belong to their publishers (Qwen, Apache-2.0) and are kept as
evidence of what was tested. No model weights are in this repository.
