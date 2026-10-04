// Tes fungsi tanggal di tampilan (static/js/dates.js).
// Dijalankan oleh tests/test_frontend.py dengan beberapa zona waktu.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  addDays, daysBetween, describeDue, formatClock, formatDuration, formatShort, formatTime, toISODate,
} from '../../static/js/dates.js';

test('toISODate memakai tanggal lokal dengan nol di depan', () => {
  assert.equal(toISODate(new Date(2026, 0, 5)), '2026-01-05');
  assert.equal(toISODate(new Date(2026, 11, 31, 23, 59)), '2026-12-31');
});

test('addDays melewati akhir bulan, akhir tahun, dan tahun kabisat', () => {
  assert.equal(addDays('2026-10-31', 1), '2026-11-01');
  assert.equal(addDays('2026-12-31', 1), '2027-01-01');
  assert.equal(addDays('2027-01-01', -1), '2026-12-31');
  assert.equal(addDays('2028-02-28', 1), '2028-02-29');
  assert.equal(addDays('2027-02-28', 1), '2027-03-01');
  // Melewati pergantian jam musim panas (di zona waktu yang memakainya)
  assert.equal(addDays('2026-03-28', 2), '2026-03-30');
  assert.equal(addDays('2026-10-24', 2), '2026-10-26');
});

test('daysBetween menghitung selisih hari, termasuk melewati pergantian jam', () => {
  assert.equal(daysBetween('2026-10-04', '2026-10-04'), 0);
  assert.equal(daysBetween('2026-10-04', '2026-10-06'), 2);
  assert.equal(daysBetween('2026-10-06', '2026-10-04'), -2);
  assert.equal(daysBetween('2026-03-28', '2026-03-30'), 2);
  assert.equal(daysBetween('2026-10-24', '2026-10-26'), 2);
  assert.equal(daysBetween('2026-01-01', '2027-01-01'), 365);
});

test('describeDue memberi label deadline yang benar', () => {
  const today = '2026-10-04';
  assert.deepEqual(describeDue('2026-10-03', today), { state: 'overdue', label: 'Terlambat 1 hari' });
  assert.deepEqual(describeDue('2026-09-24', today), { state: 'overdue', label: 'Terlambat 10 hari' });
  assert.deepEqual(describeDue('2026-10-04', today), { state: 'today', label: 'Hari ini' });
  assert.deepEqual(describeDue('2026-10-05', today), { state: 'tomorrow', label: 'Besok' });
  const future = describeDue('2026-10-24', today);
  assert.equal(future.state, 'future');
  assert.match(future.label, /24 Okt/);
  // Akhir bulan: 31 Oktober -> 1 November adalah "Besok"
  assert.equal(describeDue('2026-11-01', '2026-10-31').state, 'tomorrow');
});

test('formatShort menampilkan tahun hanya bila bukan tahun ini', () => {
  const thisYear = new Date().getFullYear();
  assert.doesNotMatch(formatShort(`${thisYear}-06-15`), new RegExp(String(thisYear)));
  assert.match(formatShort(`${thisYear + 1}-06-15`), new RegExp(String(thisYear + 1)));
});

test('formatClock untuk tampilan timer', () => {
  assert.equal(formatClock(25 * 60 * 1000), '25:00');
  assert.equal(formatClock(0), '00:00');
  assert.equal(formatClock(-5000), '00:00');
  assert.equal(formatClock(999), '00:01'); // dibulatkan ke atas: tidak tampil 00:00 sebelum benar-benar habis
  assert.equal(formatClock(65 * 60 * 1000), '1:05:00');
});

test('formatDuration untuk total waktu fokus (dibulatkan ke menit terdekat)', () => {
  assert.equal(formatDuration(20), 'kurang dari 1 menit');
  assert.equal(formatDuration(45), '1 menit');
  assert.equal(formatDuration(60), '1 menit');
  assert.equal(formatDuration(89), '1 menit');
  assert.equal(formatDuration(90), '2 menit');
  assert.equal(formatDuration(25 * 60), '25 menit');
  assert.equal(formatDuration(3600), '1 jam');
  assert.equal(formatDuration(4500), '1 jam 15 menit');
  assert.equal(formatDuration(4500, { short: true }), '1j 15m');
  assert.equal(formatDuration(3600, { short: true }), '1j');
  assert.equal(formatDuration(20, { short: true }), '<1m');
});

test('formatTime mengambil jam dari waktu ISO', () => {
  assert.equal(formatTime('2026-10-04T09:05:00'), '09.05');
  assert.equal(formatTime('2026-10-04T23:59:59'), '23.59');
});
