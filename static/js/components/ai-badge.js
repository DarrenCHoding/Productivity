// Penanda "Usulan AI". Setiap hasil dari AI wajib ditandai dengan ini,
// supaya selalu jelas mana yang dibuat AI dan mana yang Anda tulis sendiri.

import { icon } from '../icons.js';
import { el } from '../ui.js';

const MODEL_NAMES = {
  'claude-haiku-4-5': 'Claude Haiku 4.5',
  'claude-sonnet-5-5': 'Claude Sonnet 5.5',
  'claude-opus-5-5': 'Claude Opus 5.5',
};

export function modelName(id) {
  return MODEL_NAMES[id] || id;
}

/** @param label  'Usulan AI' (default) atau teks lain, misalnya 'Jawaban AI' */
export function aiBadge(model, label = 'Usulan AI') {
  return el('span', { class: 'ai-badge', title: model ? `Dibuat oleh ${modelName(model)}` : 'Dibuat oleh AI' },
    icon('sparkle', 14), label);
}
