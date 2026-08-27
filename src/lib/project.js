const STORAGE_KEY = 'gq-video-editor:projects:v1';

export function readProjects() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

export function saveProjects(projects) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
  return projects;
}

export function saveProject(project) {
  const projects = readProjects();
  const normalized = {
    id: project.id || crypto.randomUUID(),
    name: project.name || 'Video BĐS mới',
    updatedAt: new Date().toISOString(),
    ...project,
  };
  const next = [normalized, ...projects.filter(item => item.id !== normalized.id)];
  saveProjects(next);
  return normalized;
}

export function deleteProject(id) {
  saveProjects(readProjects().filter(project => project.id !== id));
}

export function exportProjectJson(project) {
  const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${(project.name || 'gq-video-project').replace(/[^a-z0-9-_]+/gi, '-').toLowerCase()}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function importProjectJson(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result));
        if (!parsed || typeof parsed !== 'object') throw new Error('Invalid project');
        resolve(parsed);
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(reader.error || new Error('Cannot read file'));
    reader.readAsText(file);
  });
}

export const DEFAULT_EXPORT = {
  format: 'mp4',
  codec: 'h264',
  audioCodec: 'aac',
  preset: 'medium',
  crf: 18,
  audioBitrate: '192k',
  fps: 30,
  colorSpace: 'bt709',
};
