#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const manifestPath = path.join(root, 'images', 'wiki', 'illustraties-liederen-gebeden-manifest.json');
const [category, itemId, status, reason = ''] = process.argv.slice(2);
const allowed = new Set(['pending', 'generated', 'validated', 'integrated']);

if (!category || !itemId || !allowed.has(status)) {
  console.error('Gebruik: node scripts/update_wiki_illustratie_status.js <categorie> <item-id> <pending|generated|validated|integrated> [foutreden]');
  process.exit(2);
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const item = manifest.items.find((entry) => entry.categorie === category && entry.itemId === itemId);
if (!item) {
  console.error(`Onbekend manifest-item: ${category}:${itemId}`);
  process.exit(3);
}

item.status = status;
item.foutreden = reason || null;
const now = new Date().toISOString();
if (status === 'generated') item.gegenereerdOp = now;
if (status === 'validated' || status === 'integrated') {
  item.gegenereerdOp ||= now;
  item.gevalideerdOp ||= now;
}
manifest.bijgewerktOp = now;
manifest.tellingen = manifest.items.reduce((result, entry) => {
  result.total += 1;
  result[entry.status] = (result[entry.status] || 0) + 1;
  result.perCategorie[entry.categorie] = (result.perCategorie[entry.categorie] || 0) + 1;
  return result;
}, { total: 0, pending: 0, generated: 0, validated: 0, integrated: 0, perCategorie: {} });

fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
console.log(`${category}:${itemId} -> ${status}`);
