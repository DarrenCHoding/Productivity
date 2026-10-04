// Ikon kecil (SVG) yang dipakai di tampilan.

const PATHS = {
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13.5 6.5l4 4"/>',
  trash: '<path d="M4 7h16"/><path d="M10 11v6M14 11v6"/><path d="M6 7l1 13h10l1-13"/><path d="M9 7V4h6v3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  chevron: '<path d="M9 6l6 6-6 6"/>',
  calendar: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
  flag: '<path d="M6 21V4"/><path d="M6 4h11l-2 4 2 4H6"/>',
};

export function icon(name, size = 20) {
  const span = document.createElement('span');
  span.className = `icon icon-${name}`;
  span.setAttribute('aria-hidden', 'true');
  span.innerHTML =
    `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
    `stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${PATHS[name]}</svg>`;
  return span;
}
