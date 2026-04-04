import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path: pathSegments } = await context.params;
  const filePath = path.join(process.cwd(), '..', 'output', ...pathSegments);

  if (!fs.existsSync(filePath)) {
    return new NextResponse('File not found', { status: 404 });
  }

  const fileBuffer = fs.readFileSync(filePath);
  const ext = path.extname(filePath).toLowerCase();
  
  let contentType = 'application/octet-stream';
  if (ext === '.html') contentType = 'text/html';
  else if (ext === '.png') contentType = 'image/png';
  else if (ext === '.jpg' || ext === '.jpeg') contentType = 'image/jpeg';
  else if (ext === '.json') contentType = 'application/json';
  else if (ext === '.csv') contentType = 'text/csv';

  return new NextResponse(fileBuffer, {
    headers: {
      'Content-Type': contentType,
    },
  });
}
