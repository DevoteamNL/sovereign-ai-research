# AI-Q Patches

Patch files for features we intend to contribute back to the upstream NVIDIA AI-Q repository, or other minor source-level changes that need to be applied before building custom images.

## Patch Creation Workflow

1. **Develop and commit** in `upstream/aiq/` submodule
2. **Generate patch**: e.g. `cd upstream/aiq && git format-patch -1 HEAD -o ../../patches/aiq/`
3. **Reset submodule**: `git reset --hard HEAD~1 && git clean -fd`
4. **Track patch**: `git add patches/aiq/*.patch && git commit`
5. **Submit upstream** via PR to NVIDIA AI-Q for patch changes we want to contribute to upstream code
6. **Remove patch** once merged and submodule updated

## Applying Patches

To apply patches to a fresh upstream checkout:

```bash
cd upstream/aiq
git am ../../patches/aiq/*.patch
```

This applies all patches in order:
1. `0001-Add-arbitrary-header-support-to-OTEL-exporter.patch`
2. `0002-Add-runtime-branding-customization-support.patch`

If patch application fails:

```bash
git am --abort
```

## Notes

- Patches are numbered to ensure correct application order.
- Use `git format-patch` + `git am` when you want to preserve commit metadata.
- Use patches primarily for source-level features or fixes pending upstream contribution.
- Do not commit local AI-Q submodule commits to this repository
- After running `git am`, the submodule will have new local commits and the parent repo will show `upstream/aiq` as modified. That is expected during build/testing.
