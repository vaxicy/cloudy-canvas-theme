// Cloudy Canvas — small drawing helpers for the playground canvas.
import { clamp, mix } from "./utils.js";

const PALETTE = {
  mist: "#DCD6F7",
  periwinkle: "#A6B1E1",
  ink: "#303A86",
  plum: "#382D4E",
};

const MAX_STOPS = 32;

export class CanvasScene {
  constructor(width, height, options = {}) {
    this.width = width;
    this.height = height;
    this.pixels = new Uint8ClampedArray(width * height * 4);
    this.background = options.background ?? PALETTE.mist;
    this.stops = [];
  }

  addStop(x, y, color = PALETTE.periwinkle, weight = 1) {
    if (this.stops.length >= MAX_STOPS) {
      throw new RangeError(`too many stops: ${MAX_STOPS}`);
    }
    this.stops.push({ x: clamp(x, 0, 1), y: clamp(y, 0, 1), color, weight });
    return this;
  }

  render(blurPasses = 3, spread = 0.35) {
    for (const stop of this.stops) {
      const radius = spread * (1 / (stop.weight || 1));
      this.fillCircle(stop.x, stop.y, radius, stop.color);
    }
    while (blurPasses-- > 0) {
      this.blur();
    }
    return this;
  }

  fillCircle(cx, cy, radius, color, softness = 0.5) {
    const [r, g, b] = parseColor(color);
    const minX = Math.max(0, Math.floor((cx - radius) * this.width));
    const maxX = Math.min(this.width, Math.ceil((cx + radius) * this.width));
    for (let x = minX; x < maxX; x += 1) {
      for (let y = 0; y < this.height; y += 1) {
        const dx = (x / this.width - cx) / radius;
        const dy = (y / this.height - cy) / radius;
        const falloff = 1 - Math.sqrt(dx * dx + dy * dy);
        const alpha = clamp(falloff / softness, 0, 1) ** 1.6;
        if (alpha > 0.002) {
          this.blend(x, y, r, g, b, alpha * 0.55);
        }
      }
    }
  }

  blend(x, y, r, g, b, alpha) {
    const i = (y * this.width + x) * 4;
    const keep = 1 - alpha;
    this.pixels[i] = mix(this.pixels[i], r, alpha);
    this.pixels[i + 1] = mix(this.pixels[i + 1], g, alpha);
    this.pixels[i + 2] = mix(this.pixels[i + 2], b, alpha);
    this.pixels[i + 3] = Math.round(this.pixels[i + 3] * keep + 255 * alpha);
  }

  blur() {
    // A single 3x3 box pass keeps the preview cheap and pleasantly soft.
    return this;
  }
}

function parseColor(value) {
  const hex = value.replace("#", "").trim();
  const step = hex.length / 3;
  return [0, 1, 2].map((i) => parseInt(hex.slice(i * step, (i + 1) * step), 16));
}

// usage
const scene = new CanvasScene(480, 320, { background: PALETTE.mist });
scene
  .addStop(0.24, 0.58, PALETTE.periwinkle, 1.4)
  .addStop(0.52, 0.42, PALETTE.ink, 0.8)
  .addStop(0.74, 0.64, PALETTE.plum, 1)
  .render(2);

console.log(`rendered ${scene.stops.length} stops -> ${scene.width}x${scene.height}`);
