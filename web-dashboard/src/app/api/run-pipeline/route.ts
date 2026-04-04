import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(req: Request) {
  const body = await req.json();
  const mission = body.mission || {};
  
  const rootDir = path.resolve(process.cwd(), '..');
  const pythonCmd = path.join(rootDir, 'venv', 'Scripts', 'python.exe');
  const scriptPath = path.join(rootDir, 'main.py');
  const missionPath = path.join(rootDir, 'output', 'current_mission.json');
  const resultsPath = path.join(rootDir, 'output', 'results.json');

  if (!fs.existsSync(path.dirname(missionPath))) {
    fs.mkdirSync(path.dirname(missionPath), { recursive: true });
  }

  try {
    fs.writeFileSync(missionPath, JSON.stringify(mission, null, 2));
  } catch (e) {
    console.error("Failed to write mission.json", e);
  }

  return new Promise((resolve) => {
    console.log("🔍 SMARTRoute Diagnostic: Verify Mission Integrity...");
    console.log("   📂 Root:", rootDir);
    console.log("   🐍 Python:", pythonCmd);
    console.log("   📄 Script:", scriptPath);

    // 🛡️ Pre-flight: Check if Python environment is valid
    if (!fs.existsSync(pythonCmd)) {
      const msg = `CRITICAL FAILURE: Python executable not found at ${pythonCmd}. Please ensure your virtual environment is created.`;
      console.error(msg);
      resolve(NextResponse.json({ success: false, error: msg }, { status: 500 }));
      return;
    }

    if (!fs.existsSync(scriptPath)) {
      const msg = `CRITICAL FAILURE: Engine entry point missing at ${scriptPath}.`;
      console.error(msg);
      resolve(NextResponse.json({ success: false, error: msg }, { status: 500 }));
      return;
    }

    // 🚀 Using spawn for better path-handling on Windows (spaces)
    const pythonProcess = spawn(pythonCmd, [scriptPath, '--mission', 'output/current_mission.json'], {
      cwd: rootDir,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => { stdout += data.toString(); });
    pythonProcess.stderr.on('data', (data) => { stderr += data.toString(); });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        const errorMsg = [
            `CRITICAL: Engine exited with code ${code}`,
            `--- [STDERR] ---`,
            stderr.trim(),
            `--- [STDOUT] ---`,
            stdout.trim()
        ].filter(Boolean).join('\n');
        
        console.error(errorMsg);
        resolve(NextResponse.json({ success: false, error: errorMsg }, { status: 500 }));
        return;
      }
      
      let results = null;
      try {
        if (fs.existsSync(resultsPath)) {
          results = JSON.parse(fs.readFileSync(resultsPath, 'utf8'));
        }
      } catch (e) {
        console.error("Failed to read results.json", e);
      }

      resolve(NextResponse.json({ success: true, output: stdout, results }));
    });
  });
}
