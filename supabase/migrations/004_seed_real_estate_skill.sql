insert into public.skills (workspace_id, name, slug, description, rules, version, is_public)
values (
  null,
  'Real Estate Pro',
  'real-estate-pro',
  'Production skill for short-form Vietnamese real-estate sales videos.',
  '{"hook_seconds":3,"target_aspects":["9:16","1:1","16:9"],"remove_silence":true,"max_pause_seconds":0.5,"priorities":["hook","property_visuals","price","legal","location","cta"],"captions":{"enabled":true,"styles":["premium","bold","minimal"],"keyword_highlight":true},"audio":{"voice_enhance":true,"duck_music":true,"target_lufs":-16},"color":{"preset":"luxury","auto":true},"fact_safety":{"never_invent_property_facts":true,"use_placeholder_when_missing":true},"cta":"GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ"}'::jsonb,
  1,
  true
)
on conflict (workspace_id, slug) do update set rules = excluded.rules, version = excluded.version, updated_at = now();
