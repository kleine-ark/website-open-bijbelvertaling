#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const MANIFEST = path.join(ROOT, 'images', 'wiki', 'illustraties-liederen-gebeden-manifest.json');

const CATEGORIES = [
  { key: 'liederen', source: 'data/naslag-liederen.json' },
  { key: 'gebeden', source: 'data/naslag-gebeden.json' },
];

const PILOTS = new Map([
  ['liederen:lied-bij-de-schelfzee', 'images/wiki/proefserie/lied-bij-de-schelfzee.webp'],
  ['gebeden:jezus-in-gethsemane', 'images/wiki/proefserie/jezus-in-gethsemane.webp'],
]);

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function buildPrompt(category, item) {
  const passage = normalize((item.tekstpassages || []).map((entry) => entry.label).join('; '));
  const summary = normalize(item.beschrijving);
  const mode = category === 'liederen' ? 'biblical song' : 'biblical prayer';
  const focus = category === 'liederen'
    ? 'a restrained moment of sung worship or lament, not a performance spectacle'
    : 'a restrained moment of prayer, supplication, thanksgiving or intercession, not theatrical action';

  return [
    'Use case: historical-scene',
    'Asset type: square wiki catalogue tile illustration',
    `Primary request: illustrate ${item.naam}, the ${mode} connected with ${passage || 'the cited biblical passage'}`,
    `Biblical context: ${summary}`,
    `Narrative focus: ${focus}; select one instantly recognizable visual moment or symbolic still life from the supplied biblical context`,
    'Scene/backdrop: historically plausible ancient Near Eastern or first-century biblical setting appropriate to the cited passage, fading naturally into warm aged parchment with delicate fibers and subtle patina',
    'Subject: one clear focal person, small group, or symbolic object arrangement that is specific to this item; natural anatomy, historically plausible clothing and material culture',
    'Style/medium: highly refined historical pencil drawing with fine navy-gray graphite contours and very subtle transparent watercolor washes, matching the restrained hand-drawn museum-plate quality of the Open Vertaling biblical instrument illustrations',
    'Composition/framing: square, calm centered or gently asymmetrical composition, clear silhouette, generous breathing room, no crowded panorama',
    'Lighting/mood: gentle natural light, quiet, reverent and emotionally appropriate',
    'Color palette: parchment cream, sand, muted antique gold, faded olive, warm brown and restrained blue-gray with deep navy contours; low saturation',
    'Materials/textures: handwoven linen and wool, weathered wood, stone, earth and vegetation appropriate to the historical period',
    'Constraints: no text, no letters, no numbers, no artist signature, no corner mark, no frame, no border, no watermark, no modern objects, no fantasy costume, no halo, no glowing aura, no dramatic rays, no theatrical action, no photorealism, no cartoon style',
  ].join('\n');
}

const previous = fs.existsSync(MANIFEST)
  ? JSON.parse(fs.readFileSync(MANIFEST, 'utf8'))
  : { items: [] };
const priorByKey = new Map((previous.items || []).map((item) => [`${item.categorie}:${item.itemId}`, item]));
const items = [];

for (const category of CATEGORIES) {
  const sourcePath = path.join(ROOT, category.source);
  const data = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
  const outputDir = path.join(ROOT, 'images', 'wiki', category.key);
  fs.mkdirSync(outputDir, { recursive: true });

  for (const item of data.items) {
    const key = `${category.key}:${item.id}`;
    const doelpad = `images/wiki/${category.key}/${item.id}.webp`;
    const absoluteTarget = path.join(ROOT, doelpad);
    const prior = priorByKey.get(key);
    const pilot = PILOTS.get(key) || null;
    const fileExists = fs.existsSync(absoluteTarget);
    const preservedStatus = fileExists && ['validated', 'integrated'].includes(prior?.status)
      ? prior.status
      : (fileExists ? 'generated' : 'pending');
    items.push({
      categorie: category.key,
      itemId: item.id,
      naam: item.naam,
      doelpad,
      status: preservedStatus,
      prompt: prior?.prompt || buildPrompt(category.key, item),
      foutreden: fileExists ? null : (prior?.foutreden || null),
      bronPilot: pilot,
      gegenereerdOp: fileExists ? (prior?.gegenereerdOp || null) : null,
      gevalideerdOp: fileExists ? (prior?.gevalideerdOp || null) : null,
    });
  }
}

const counts = items.reduce((result, item) => {
  result.total += 1;
  result[item.status] = (result[item.status] || 0) + 1;
  result.perCategorie[item.categorie] = (result.perCategorie[item.categorie] || 0) + 1;
  return result;
}, { total: 0, pending: 0, generated: 0, validated: 0, integrated: 0, perCategorie: {} });

const manifest = {
  schemaVersie: 1,
  stijl: 'Historische potloodtekening met subtiele aquarel op warm perkament; zand, goud, olijf en navy; rustig, herkenbaar, zonder tekst of kader.',
  vasteStijlreferenties: [
    'images/wiki/proefserie/lied-bij-de-schelfzee.webp',
    'images/wiki/proefserie/jezus-in-gethsemane.webp',
    'images/wiki/muziekinstrumenten/harp.webp',
    'images/wiki/muziekinstrumenten/trompet.webp',
  ],
  uitvoer: { formaat: 'WebP', breedte: 640, hoogte: 640 },
  bijgewerktOp: new Date().toISOString(),
  tellingen: counts,
  items,
};

fs.writeFileSync(MANIFEST, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(counts));
