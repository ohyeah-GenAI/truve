# VQA Illusion Service

착시/왜곡 기반 VQA 챌린지 로직을 담당합니다.

## Model cache contract (offline)

- Model manifest: `services/vqa-illusion/model-cache-manifest.json`
- Default cache root: `~/.cache/vqa-bot-detection/illusion-vqa/models/`
- Override env var: `ILLUSION_VQA_MODEL_CACHE`

### Validate pinned manifest

```bash
python "services/vqa-illusion/scripts/model_cache_tool.py" --validate-manifest
```

### Prefetch pinned snapshots

```bash
python "services/vqa-illusion/scripts/model_cache_tool.py" --prefetch
```

### Dry-run prefetch plan

```bash
python "services/vqa-illusion/scripts/model_cache_tool.py" --prefetch --dry-run
```

### Verify local snapshots

```bash
python "services/vqa-illusion/scripts/model_cache_tool.py" --verify
```

### Offline smoke generation

After prefetch + verify, run:

```bash
python "services/vqa-illusion/scripts/generate_problem_bank.py" --seed 42 --max-images 1
```

Runtime model loading is local-only and uses `local_files_only=True`; missing local snapshots fail fast with an actionable cache error.

## Durable docs graduation target (follow-up)

- Planned stable runbook target: `docs/illusion-vqa/model-cache-runbook.md`
- Follow-up task source: `.sisyphus/task-followups/illusion-vqa-model-cache-doc-graduation.md`
