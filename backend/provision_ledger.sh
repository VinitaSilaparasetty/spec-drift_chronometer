#!/bin/bash
echo "📑 Syncing Warden Policy Ledger..."
mkdir -p .kiro/logs
mkdir -p steering
echo "timestamp=$(date +%s)" > .kiro/last_sync.audit
echo "✅ Ledger Provisioned Successfully."
