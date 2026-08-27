export function createSpeechRecognizer({
  language = 'vi-VN',
  onText,
  onFinal,
  onError,
  onStart,
  onEnd,
} = {}) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) throw new Error('Trình duyệt hiện tại không hỗ trợ SpeechRecognition.');

  const recognition = new Recognition();
  recognition.lang = language;
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onstart = () => onStart?.();
  recognition.onerror = event => onError?.(event.error || 'speech-error');
  recognition.onend = () => onEnd?.();
  recognition.onresult = event => {
    let interim = '';
    let finalText = '';
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const phrase = event.results[i][0]?.transcript?.trim() || '';
      if (event.results[i].isFinal) finalText += `${phrase} `;
      else interim += `${phrase} `;
    }
    if (interim) onText?.(interim.trim(), false);
    if (finalText) onFinal?.(finalText.trim());
  };
  return recognition;
}

export function captionLinesFromTranscript(transcript = '', maxChars = 38) {
  const words = transcript.trim().split(/\s+/).filter(Boolean);
  const lines = [];
  let current = '';
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) lines.push(current);
  return lines;
}

export const CAPTION_STYLES = {
  premium: { fontSize: 58, weight: 800, position: 'bottom', uppercase: false },
  bold: { fontSize: 64, weight: 900, position: 'center', uppercase: true },
  minimal: { fontSize: 48, weight: 700, position: 'bottom', uppercase: false },
};
