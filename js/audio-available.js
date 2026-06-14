/* Open Staten Vertaling — AUDIO_AVAILABLE + stem-keuze
 * GENEREER-OUTPUT — niet handmatig editen. Higgs Audio v3, man + vrouw.
 * Bevat nu: alle goedgekeurde hfst + het volledige Nieuwe Testament.
 */
window.AUDIO_AVAILABLE = {
    genesis: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
    psalmen: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150],
    johannes: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21],
    handelingen: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28],
    markus: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
    romeinen: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
    '1johannes': [1,2,3,4,5],
    '2johannes': [1],
    '3johannes': [1],
    efeziers: [1,2,3,4,5,6],
    gebedvanmanasse: [1],
    filemon: [1],
    judas: [1],
    baruch: [1,2,3,4,5,6],
    jakobus: [1,2,3,4,5],
    '1makkabeeen': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
    susanna: [1],
    ezra: [1,2,3,4,5,6,7,8,9,10],
    filippenzen: [1,2,3,4],
    titus: [1,2,3],
    kolossenzen: [1,2,3,4],
    mattheus: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28],
    lukas: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24],
    '1korinthiers': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
    '2korinthiers': [1,2,3,4,5,6,7,8,9,10,11,12,13],
    galaten: [1,2,3,4,5,6],
    '1tessalonicensen': [1,2,3,4,5],
    '2tessalonicensen': [1,2,3],
    '1timotheus': [1,2,3,4,5,6],
    '2timotheus': [1,2,3,4],
    hebreeen: [1,2,3,4,5,6,7,8,9,10,11,12,13],
    '1petrus': [1,2,3,4,5],
    '2petrus': [1,2,3],
    openbaring: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22],
};

/* Centrale stem-helper — gedeeld door lees.js en app.js. */
window.OV_AUDIO = {
    labels: { m: 'Man', v: 'Vrouw' },
    getVoice() { const v = localStorage.getItem('ov_voice'); return (v === 'v' || v === 'm') ? v : 'm'; },
    setVoice(v) { if (v === 'm' || v === 'v') localStorage.setItem('ov_voice', v); },
    toggleVoice() { const nv = this.getVoice() === 'm' ? 'v' : 'm'; this.setVoice(nv); return nv; },
    label(v) { return this.labels[v || this.getVoice()]; },
    src(bookId, chapter) { return `audio/${bookId}/${chapter}-${this.getVoice()}.mp3`; },
    available(bookId, chapter) { const list = (window.AUDIO_AVAILABLE || {})[bookId] || []; return list.includes(chapter); },
};
