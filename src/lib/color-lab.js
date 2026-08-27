export const LUT_PRESETS = [
  { id: 'clean', name: 'Clean BĐS', filter: 'eq=contrast=1.04:brightness=0.02:saturation=1.06:gamma=1.02' },
  { id: 'luxury', name: 'Luxury Warm', filter: 'eq=contrast=1.05:brightness=0.025:saturation=1.10:gamma=1.03,colorbalance=rs=.025:gs=.005:bs=-.015' },
  { id: 'fresh', name: 'Fresh Daylight', filter: 'eq=contrast=1.02:brightness=0.035:saturation=1.13:gamma=1.05,colorbalance=rs=.00:gs=.01:bs=.02' },
  { id: 'cinematic', name: 'Cinematic', filter: 'eq=contrast=1.10:brightness=0.01:saturation=0.92:gamma=.98,colorbalance=rs=.01:gs=-.005:bs=.025' },
  { id: 'golden', name: 'Golden Hour', filter: 'eq=contrast=1.06:brightness=0.025:saturation=1.16:gamma=1.02,colorbalance=rs=.045:gs=.015:bs=-.035' },
];

const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

export function buildColorFilter({ exposure = 0, contrast = 1, saturation = 1, temperature = 0, tint = 0, sharpen = 0.2, lut = 'clean' } = {}) {
  const preset = LUT_PRESETS.find((item) => item.id === lut) || LUT_PRESETS[0];
  const exposureValue = clamp(Number(exposure), -1, 1) * 0.18;
  const contrastValue = clamp(Number(contrast), 0.7, 1.5);
  const saturationValue = clamp(Number(saturation), 0.5, 1.5);
  const temp = clamp(Number(temperature), -1, 1) * 0.03;
  const tintValue = clamp(Number(tint), -1, 1) * 0.02;
  const sharp = clamp(Number(sharpen), 0, 1);
  return `${preset.filter},eq=brightness=${exposureValue.toFixed(4)}:contrast=${contrastValue.toFixed(3)}:saturation=${saturationValue.toFixed(3)},colorbalance=rs=${temp.toFixed(4)}:gs=${tintValue.toFixed(4)}:bs=${(-temp).toFixed(4)},unsharp=5:5:${sharp.toFixed(2)}:5:5:0`;
}

export function analyzeFrameForAutoColor(ctx, width, height) {
  const image = ctx.getImageData(0, 0, width, height).data;
  let r = 0; let g = 0; let b = 0; let count = 0;
  for (let i = 0; i < image.length; i += 16) {
    r += image[i]; g += image[i + 1]; b += image[i + 2]; count += 1;
  }
  const meanR = r / (count * 255);
  const meanG = g / (count * 255);
  const meanB = b / (count * 255);
  return {
    exposure: clamp(0.55 - (meanR * 0.2126 + meanG * 0.7152 + meanB * 0.0722), -0.35, 0.35),
    temperature: clamp(meanR - meanB, -0.3, 0.3),
    tint: clamp(meanG - ((meanR + meanB) / 2), -0.3, 0.3),
  };
}
