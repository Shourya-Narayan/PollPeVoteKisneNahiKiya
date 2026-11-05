import os
import subprocess
import json
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PS_SCRIPT = CURRENT_DIR / "win_ocr_runner.ps1"

PS_SCRIPT_CONTENT = """param([string]$ImagePath)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
})[0]

function Await-WinRT($asyncOp, $type) {
    $asTask = $asTaskGeneric.MakeGenericMethod($type)
    $task = $asTask.Invoke($null, @($asyncOp))
    $task.Wait()
    return $task.Result
}

[Windows.Media.Ocr.OcrEngine, Windows.Foundation.Diagnostics, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null

$imagePath = (Resolve-Path $ImagePath).Path
$fileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($imagePath)
$file = Await-WinRT $fileOp ([Windows.Storage.StorageFile])

$streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
$stream = Await-WinRT $streamOp ([Windows.Storage.Streams.IRandomAccessStream])

$decoderOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
$decoder = Await-WinRT $decoderOp ([Windows.Graphics.Imaging.BitmapDecoder])

$bmpOp = $decoder.GetSoftwareBitmapAsync()
$bmp = Await-WinRT $bmpOp ([Windows.Graphics.Imaging.SoftwareBitmap])

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$ocrOp = $engine.RecognizeAsync($bmp)
$ocrResult = Await-WinRT $ocrOp ([Windows.Media.Ocr.OcrResult])

$lines = @()
foreach ($line in $ocrResult.Lines) {
    $lines += $line.Text
}
$lines | ConvertTo-Json -Compress
"""

with open(PS_SCRIPT, "w", encoding="utf-8") as f:
    f.write(PS_SCRIPT_CONTENT.strip())

def extract_text_from_image(image_path: str) -> list[str]:
    """
    Extracts all text lines from an image using Windows Native OCR.
    Runs fast (<1s), completely offline, zero cloud calls.
    """
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image file not found: {abs_path}")

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(PS_SCRIPT),
        "-ImagePath", abs_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"OCR execution failed: {err}")

    stdout = result.stdout.decode("utf-8", errors="replace").strip()
    if not stdout:
        return []

    try:
        data = json.loads(stdout)
        if isinstance(data, str):
            return [data]
        elif isinstance(data, list):
            return [str(item) for item in data]
        return []
    except json.JSONDecodeError:
        return stdout.splitlines()

if __name__ == "__main__":
    test_img = r"C:\Users\shour\.gemini\antigravity\brain\06c792c0-32bc-4a56-a659-a5198a07980c\.user_uploaded\media_1793863754205_cfe22cff.jpg"
    lines = extract_text_from_image(test_img)
    print(f"Extracted {len(lines)} lines successfully:")
    for l in lines[:10]:
        print("-", l)
