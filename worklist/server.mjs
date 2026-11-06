import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';

const orthancPort = process.env.APEX_ORTHANC_PORT ?? '8043';
if (!['8042', '8043'].includes(orthancPort)) throw new Error('Use Orthanc port 8042 or 8043');
const orthanc = 'http://127.0.0.1:' + orthancPort;
const assets = {
  '/': ['index.html', 'text/html'],
  '/app.js': ['app.js', 'text/javascript'],
  '/style.css': ['style.css', 'text/css'],
};

createServer(async (request, response) => {
  response.setHeader('Cache-Control', 'no-store');
  response.setHeader('X-Content-Type-Options', 'nosniff');
  const reply = (status, type, body) => {
    response.writeHead(status, { 'Content-Type': type + '; charset=utf-8' });
    response.end(body);
  };
  if (request.method !== 'GET') return reply(405, 'text/plain', 'GET only');
  const route = request.url.split('?')[0];
  if (route === '/api/studies') {
    try {
      const result = await fetch(orthanc + '/dicom-web/studies?includefield=00081030', {
        headers: { Accept: 'application/dicom+json' },
        signal: AbortSignal.timeout(5000),
        redirect: 'error',
      });
      if (!result.ok) throw new Error('DICOMweb unavailable');
      const studies = await result.json();
      if (!Array.isArray(studies)) throw new Error('Unexpected study list');
      return reply(200, 'application/json', JSON.stringify({ viewer: orthanc + '/ohif/viewer', studies }));
    } catch {
      return reply(503, 'application/json', JSON.stringify({ error: 'Start the local Orthanc stack and try again.' }));
    }
  }
  if (!Object.hasOwn(assets, route)) return reply(404, 'text/plain', 'Not found');
  const [file, type] = assets[route];
  try {
    return reply(200, type, await readFile(new URL('./public/' + file, import.meta.url)));
  } catch {
    return reply(500, 'text/plain', 'Worklist asset unavailable');
  }
}).listen(8080, '127.0.0.1', () => console.log('APEX PACS worklist: http://127.0.0.1:8080'));
