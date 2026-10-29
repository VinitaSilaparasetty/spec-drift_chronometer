# Bundled spec vault

Mirror of `.kiro/steering/`, committed so the Warden Engine can load the human
intent specs when only `backend/` is deployed. The hosted demo ran this way and
every diff scored an identical 0.005 — the "no spec vocabulary" sentinel — so
drift never reached the threshold and the Justification Gate never fired.

`.kiro/steering/` remains the source of truth. `_load_spec_intent()` prefers, in
order: `$SPEC_VAULT_DIR`, this directory, `.kiro/steering/` walking up from
`backend/`, then `.kiro/steering/` under the working directory.

Re-sync after editing the steering files:

```bash
cp .kiro/steering/{governance.md,tech.md,product.md,human-intent-specs.md,spec.json} backend/spec_vault/
```

`GET /drift` reports `"spec_vault": "OK"` or `"UNAVAILABLE"`, so a deployment
that cannot see the vault is visible from the API rather than silently flat.
