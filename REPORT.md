# Measured by us: Qwen3 MoE versus dense on one CPU

The MoE generated **9.120×** as many tokens per second as the dense model. The simple active-parameter prediction was **9.939×** (32.8B / 3.3B), so the measured ratio is **8.25% lower**. The models have similar total parameter counts, but this comparison does not establish that memory bandwidth alone caused the difference.

Measured on 2026-11-09 UTC (2026-11-10 IST). Raw evidence: [run.json](run.json), [MoE output](demo-1/results/moe.json), [dense output](demo-1/results/dense.json). The derived [measurement.json](measurement.json) retains all samples and the exact ratios. Commands and output are available for terminal plate replay in `run.json`.

## Results

Tokens/s are arithmetic means ± sample standard deviation across five timed repetitions. Ranges are observed minima and maxima, not confidence intervals.

| Publisher model, Q4_K_M | Prompt processing, 512 tokens | Prompt range | Generation, 128 tokens | Generation range |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-30B-A3B, MoE | 47.638386 ± 3.418993 | 41.6923–49.9630 | 12.227722 ± 0.043865 | 12.1605–12.2693 |
| Qwen3-32B, dense | 6.634155 ± 0.187171 | 6.29934–6.71880 | 1.340823 ± 0.001168 | 1.33929–1.34232 |

Measured generation ratio: `12.227722 / 1.340823 = 9.11956462560681`.
Predicted ratio: `32.8 / 3.3 = 9.93939393939394`.
Measured / predicted: `0.9175171726982461`.

## Fixed protocol

Test machine: Intel i7-7700K @ 4.20 GHz, four physical / eight logical cores, 33,576,022,016 bytes RAM, Linux `7.2.11-arch1-1`. Official llama.cpp CPU image, release b12211, build commit `7d7f0287530bc8981690f361d8c1627dbae1c99a`:

```text
ghcr.io/ggml-org/llama.cpp:full-b12211@sha256:8960de326dd60972cc4d442531f4efa006416d5896da2a39f0def0b55cbcb0c2
```

Each model ran once in its own container, sequentially, MoE then dense:

```text
env LD_LIBRARY_PATH=/app /app/llama-bench -m <model> -p 512 -n 128 -r 5 -t 4 -ngl 0 -o json
```

Both benchmark containers used `--network none`, no GPU request, and report backend `CPU`. The engine's default warmup occurs outside the timed repetition loop: a full prompt for prompt processing and one generated token for generation. These are separate synthetic pp512 and tg128 tests; generation does not follow a 512-token user prompt. No benchmark was repeated or tuned.

The exclusive `/scratch/gpu.lock` was held through preparation and both models. Immediately before measurement, load averages (1/5/15 minutes) were `1.000000, 0.796387, 0.651367`; none exceeded the discard threshold of 1.0. Afterward they were `4.000000, 3.942383, 3.042480`. The post-run load includes our four-thread benchmark. Cleanup verified that the lock was released and our containers had exited.

## Publisher provenance

Both files come from Qwen's own repositories, use Q4_K_M, and have Apache-2.0 licences. Immutable API, card, licence and download URLs are in [sources.json](sources.json). API responses, cards, licences and OCI metadata are preserved in [provenance/](provenance/hashes.json). Downloaded bytes were checked against the API's LFS SHA256 values before benchmarking.

| Model | Publisher card counts | File bytes | SHA256 |
| --- | --- | ---: | --- |
| [Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B-GGUF/blob/e4d4bafdfb96a411a163846265362aceb0b9c63a/README.md) | 30.5B total, 3.3B active | 18,556,685,824 | `0d003f6662faee786ed5da3e31b29c978de5ae5d275c8794c606a7f3c01aa8f5` |
| [Qwen3-32B](https://huggingface.co/Qwen/Qwen3-32B-GGUF/blob/938a7432affaec9157f883a87164e2646ae17555/README.md) | 32.8B total / dense active | 19,762,149,024 | `efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689` |

Combined model download payload: **38,318,834,848 bytes (38.319 GB)**. The image's compressed layer descriptors total **1,136,146,315 bytes**; combined nominal model + image-layer payload is **39,454,981,163 bytes (39.455 GB)**. Network framing, image metadata and TLS overhead were not counted, so this is not a measured wire-byte total.

The successful runner invocation took **1,835.606 s (30 min 35.606 s)**, including download, verification, preparation and both benchmarks. The model download step took 444.439 s; MoE and dense container steps took 172.006 s and 1,028.216 s respectively (20 min 0.222 s combined, including loading/warmup). The earlier image pull took 142.544 s. From the first preflight start to final completion, elapsed wall time was 2,061.914 s (34 min 21.914 s).

Two preflight failures are preserved in [attempts/](attempts/preflight-library-run.json): the container launcher needed its library path set, then Docker bridge networking lacked an external route. The final manifest explicitly declares host networking only for the public HTTPS model download. Neither preflight reached a benchmark; no host configuration was changed.

## Interpretation limits

This result supports a large decode-speed advantage for this MoE over this similarly sized dense model on this CPU. It does not show a universal proportional relationship or isolate a causal memory-bandwidth bottleneck. No bandwidth counters or output-quality comparisons were collected. Active parameter counts are rounded publisher claims, while speed is our measurement.

The prediction omits routing, shared/embedding/output weights, quantisation layout, CPU kernels and cache behaviour. The model order was fixed, the OS page cache was not cleared, and only one engine build, quantisation and pair were tested. All five samples, including the slower first prompt-processing samples, are retained.
