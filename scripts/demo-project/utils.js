// Tiny numeric helpers shared by the canvas scene.

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function mix(base, target, amount) {
  return Math.round(base + (target - base) * clamp(amount, 0, 1));
}

export function lerp(from, to, t) {
  return from + (to - from) * clamp(t, 0, 1);
}
