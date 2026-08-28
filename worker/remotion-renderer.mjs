/* Optional Remotion adapter. The production MVP currently uses FFmpeg for cuts/concat.
   This module is intentionally isolated so we can move motion graphics/captions into Remotion
   without changing the queue contract. */

export function buildRemotionComposition({ scenes = [], width = 1080, height = 1920, fps = 30 }) {
  return {
    id: 'GQRealEstateComposition',
    width,
    height,
    fps,
    durationInFrames: Math.max(1, Math.ceil(scenes.reduce((sum, s) => sum + Math.max(0.2, Number(s.end || 0) - Number(s.start || 0)), 0) * fps)),
    inputProps: { scenes },
  };
}

export function supportsRemotion(plan = {}) {
  return Array.isArray(plan.scenes) && plan.scenes.length > 0;
}
