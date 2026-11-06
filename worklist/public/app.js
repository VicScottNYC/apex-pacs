const byId = (id) => document.getElementById(id);
const values = (study, tag) => study[tag]?.Value ?? [];
const first = (study, tag) => values(study, tag)[0];
const search = byId('search');
const modality = byId('modality');
const refresh = byId('refresh');
let records = [];
let viewer = '';
let connected = false;

function render() {
  const query = search.value.trim().toLowerCase();
  const matches = records.filter((record) =>
    (!modality.value || record.modalities.includes(modality.value)) &&
    [record.title, record.patient, record.uid].some((value) => value.toLowerCase().includes(query)));
  const rows = byId('rows');
  rows.replaceChildren();
  for (const record of matches) {
    const row = rows.insertRow();
    for (const value of [record.title, record.patient, record.modalities.join(', ') || '—', record.images ?? '—']) {
      row.insertCell().textContent = value;
    }
    const link = document.createElement('a');
    const url = new URL(viewer);
    url.searchParams.set('StudyInstanceUIDs', record.uid);
    link.href = url.href;
    link.textContent = 'Open in OHIF ↗';
    link.setAttribute('aria-label', 'Open ' + record.title + ' in OHIF');
    row.insertCell().append(link);
  }
  if (connected) byId('status').textContent = matches.length
    ? 'Showing ' + matches.length + ' of ' + records.length + ' studies'
    : records.length ? 'No studies match these filters.' : 'The archive is empty.';
}

async function load() {
  refresh.disabled = true;
  byId('status').textContent = 'Loading archive…';
  try {
    const response = await fetch('/api/studies');
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error);
    viewer = payload.viewer;
    records = payload.studies.map((study) => ({
      uid: String(first(study, '0020000D') ?? ''),
      title: String(first(study, '00081030') ?? 'Untitled study'),
      patient: String(first(study, '00100020') ?? '—'),
      modalities: values(study, '00080061').map(String),
      images: first(study, '00201208'),
    })).filter(({ uid }) => /^[0-9]+(?:\.[0-9]+)+$/.test(uid));
    const selected = modality.value;
    modality.replaceChildren(new Option('All modalities', ''));
    for (const value of [...new Set(records.flatMap((record) => record.modalities))].sort()) {
      modality.add(new Option(value, value));
    }
    if ([...modality.options].some((option) => option.value === selected)) modality.value = selected;
    connected = true;
    byId('count').textContent = records.length;
    byId('instances').textContent = records.every(({ images }) => Number.isInteger(images))
      ? records.reduce((sum, { images }) => sum + images, 0) : '—';
    byId('connection').textContent = 'Online';
  } catch {
    connected = false;
    records = [];
    modality.replaceChildren(new Option('All modalities', ''));
    byId('count').textContent = byId('instances').textContent = '—';
    byId('connection').textContent = 'Offline';
    byId('status').textContent = 'Archive unavailable. Start the local Orthanc stack and refresh.';
  } finally {
    render();
    refresh.disabled = false;
  }
}

search.addEventListener('input', render);
modality.addEventListener('change', render);
refresh.addEventListener('click', load);
load();
