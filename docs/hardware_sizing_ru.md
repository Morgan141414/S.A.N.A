# S.A.N.A. Hardware Sizing

Дата версии: 2026-06-04.

## Текущий сервер

```text
CPU: Intel i5-12400F
RAM: 31 GiB
GPU: NVIDIA GeForce RTX 3050
VRAM: 8 GB
```

Текущий сервер подходит для:

- backend/API разработки;
- deterministic safety pipeline;
- evaluation reports;
- локального inference через Ollama;
- smoke tests;
- очень осторожного QLoRA dry-run planning.

Текущий сервер не подходит для:

- обучения модели с нуля;
- комфортного fine-tuning 7B/8B;
- экспериментов с 13B+;
- модели уровня frontier.

## Практические уровни железа

### Уровень A: текущая разработка

```text
GPU VRAM: 8 GB
RAM: 32 GB
Disk: 200 GB+ SSD
```

Подходит для:

- inference quantized 7B/8B;
- тестов guardrails;
- небольших smoke/evaluation runs;
- подготовки datasets, manifests и reports.

Ограничения:

- 8B QLoRA является tight target;
- batch size почти всегда 1;
- long context быстро упирается в VRAM;
- training может быть нестабильным или слишком медленным.

### Уровень B: минимальный комфортный fine-tuning

```text
GPU: RTX 3090 24GB, RTX 4090 24GB или аналог
VRAM: 24 GB
RAM: 64 GB
Disk: 1 TB NVMe
CPU: 8-16 cores
```

Подходит для:

- QLoRA 7B/8B;
- маленьких LoRA experiments;
- нормального batch/gradient accumulation;
- post-training evaluation без постоянной борьбы за память.

Это минимальный разумный уровень для первого серьезного S.A.N.A. fine-tuning.

### Уровень C: сильный локальный research server

```text
GPU: 1x RTX 6000 Ada 48GB, RTX A6000 48GB или 2x 24GB GPU
VRAM: 48 GB total+
RAM: 128 GB
Disk: 2 TB NVMe
CPU: 16-32 cores
```

Подходит для:

- QLoRA/LoRA 13B/14B;
- более длинного context;
- нескольких baseline моделей;
- более быстрых evaluation/fine-tuning циклов.

### Уровень D: high-end local lab

```text
GPU: 1x H100 80GB, A100 80GB или несколько 48GB/80GB GPU
VRAM: 80 GB+
RAM: 256 GB+
Disk: 4 TB NVMe+
CPU: 32+ cores
```

Подходит для:

- 30B+ experiments;
- serious multi-model comparison;
- larger context;
- faster iteration;
- advanced fine-tuning workflows.

### Уровень E: frontier-scale

```text
GPU cluster: many H100/B200-class GPUs
VRAM: hundreds of GB to many TB across cluster
RAM/storage/network: cluster-grade
Data: large curated corpus + expert evals + safety reviews
Team: ML, data, safety, infra, clinical review
```

Это уровень не одного сервера. Модель уровня ChatGPT 5.5 требует не только GPU, но и:

- огромного pretraining/fine-tuning pipeline;
- качественных данных;
- preference data;
- safety policy;
- red-team;
- eval harness;
- monitoring;
- rollback;
- постоянного сравнения моделей.

## Рекомендация покупки

Если покупать следующий сервер специально для S.A.N.A., лучший первый шаг:

```text
GPU: RTX 4090 24GB или RTX 3090 24GB
RAM: 64-128 GB
Disk: 1-2 TB NVMe
CPU: 12-16 cores
OS: Ubuntu 24.04 LTS
```

Если бюджет позволяет и цель - research server на годы:

```text
GPU: 48GB VRAM class
RAM: 128 GB
Disk: 2 TB NVMe
```

## Что важно не забыть

- VRAM важнее CPU для fine-tuning.
- 24GB - практический минимум для спокойного 7B/8B QLoRA.
- 48GB заметно расширяет простор для 13B/14B.
- 80GB+ нужен для больших моделей и серьезного research.
- Для S.A.N.A. качество данных и evaluation важнее раннего запуска обучения.
