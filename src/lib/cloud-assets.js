import { supabase } from './supabase';

export const ASSET_BUCKET = 'ai-editor-assets';

export async function uploadProjectFiles({ projectId, workspaceId, files, onProgress }) {
  if (!supabase) throw new Error('Supabase chưa cấu hình.');
  if (!projectId || !workspaceId) throw new Error('Project/workspace chưa sẵn sàng.');
  const uploaded = [];
  const list = Array.from(files || []);
  for (let index = 0; index < list.length; index += 1) {
    const file = list[index];
    const safe = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
    const storagePath = `${workspaceId}/${projectId}/source/${crypto.randomUUID()}-${safe}`;
    const { error: uploadError } = await supabase.storage.from(ASSET_BUCKET).upload(storagePath, file, {
      upsert: false,
      cacheControl: '3600',
      contentType: file.type || 'application/octet-stream',
    });
    if (uploadError) throw uploadError;
    const { data: row, error: insertError } = await supabase
      .from('assets')
      .insert({
        workspace_id: workspaceId,
        project_id: projectId,
        kind: file.type.startsWith('video/') ? 'video' : file.type.startsWith('image/') ? 'image' : 'audio',
        storage_path: storagePath,
        original_name: file.name,
        mime_type: file.type,
        size_bytes: file.size,
        metadata: { client_uploaded_at: new Date().toISOString() },
      })
      .select('id,workspace_id,project_id,kind,storage_path,original_name,mime_type,size_bytes')
      .single();
    if (insertError) throw insertError;
    uploaded.push({ ...row, file });
    onProgress?.(Math.round(((index + 1) / Math.max(1, list.length)) * 100));
  }
  return uploaded;
}

export async function createSignedAssetUrl(storagePath, expiresIn = 3600) {
  if (!supabase) throw new Error('Supabase chưa cấu hình.');
  const { data, error } = await supabase.storage.from(ASSET_BUCKET).createSignedUrl(storagePath, expiresIn);
  if (error) throw error;
  return data.signedUrl;
}
