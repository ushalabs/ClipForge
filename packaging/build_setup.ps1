param(
    [string]$Version = "",
    [string]$OutputDir = "",
    [string]$NsisCompiler = "",
    [string]$PythonExe = "",
    [switch]$SkipPyInstaller,
    [switch]$BundleFfmpeg,
    [switch]$SkipZip,
    [string]$CertPfxPath = $env:CLIPFORGE_SIGNING_PFX,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if (-not $Version) {
    $initFile = Join-Path $projectRoot "studio\__init__.py"
    $initContent = Get-Content -LiteralPath $initFile -Raw
    $verMatch = [regex]::Match($initContent, '__version__\s*=\s*["'']([0-9]+\.[0-9]+\.[0-9]+)["'']')
    if ($verMatch.Success) {
        $Version = $verMatch.Groups[1].Value
    } else {
        $Version = "1.0.0"
    }
}

if (-not $OutputDir) {
    $OutputDir = Join-Path $projectRoot "dist"
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$OutputDir = (Resolve-Path $OutputDir).Path

# Locate NSIS compiler without machine-specific paths
if (-not $NsisCompiler) {
    $nsisCandidates = [System.Collections.Generic.List[string]]::new()
    $cmdNsis = Get-Command "makensis.exe" -ErrorAction SilentlyContinue
    if ($cmdNsis) {
        $nsisCandidates.Add($cmdNsis.Source)
    }
    if ($env:MAKENSIS) {
        $nsisCandidates.Add($env:MAKENSIS)
    }
    if ($env:NSIS_HOME) {
        $nsisCandidates.Add((Join-Path $env:NSIS_HOME "makensis.exe"))
    }
    if (${env:ProgramFiles(x86)}) {
        $nsisCandidates.Add((Join-Path ${env:ProgramFiles(x86)} "NSIS\makensis.exe"))
    }
    if ($env:ProgramFiles) {
        $nsisCandidates.Add((Join-Path $env:ProgramFiles "NSIS\makensis.exe"))
    }
    foreach ($searchRoot in @(
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"),
        (Join-Path $env:USERPROFILE "scoop\apps\nsis"),
        (Join-Path $env:ProgramData "chocolatey\lib")
    )) {
        if ($searchRoot -and (Test-Path -LiteralPath $searchRoot)) {
            Get-ChildItem -LiteralPath $searchRoot -Filter "makensis.exe" -Recurse -File -ErrorAction SilentlyContinue |
                ForEach-Object { $nsisCandidates.Add($_.FullName) }
        }
    }
    foreach ($candidate in $nsisCandidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            $NsisCompiler = $candidate
            break
        }
    }
}
if (-not $NsisCompiler -or -not (Test-Path -LiteralPath $NsisCompiler -PathType Leaf)) {
    throw "NSIS compiler (makensis.exe) not found. Install NSIS with: winget install -e --id NSIS.NSIS"
}

# Locate Python interpreter
if (-not $PythonExe) {
    $venvPy = Join-Path $projectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPy -PathType Leaf) {
        $PythonExe = $venvPy
    } else {
        $cmdPy = Get-Command "python" -ErrorAction SilentlyContinue
        if ($cmdPy) {
            $PythonExe = $cmdPy.Source
        }
    }
}
if (-not $PythonExe) {
    throw "Python interpreter not found. Pass -PythonExe or create .venv first."
}

# 1. Build PyInstaller desktop bundle unless skipped
$bundleDir = Join-Path $projectRoot "dist\ClipForge"
if (-not $SkipPyInstaller) {
    Write-Host "==> Running PyInstaller desktop build..."
    & $PythonExe (Join-Path $projectRoot "scripts\build-desktop.py")
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE"
    }
}

$clipForgeExe = Join-Path $bundleDir "ClipForge.exe"
if (-not (Test-Path -LiteralPath $clipForgeExe -PathType Leaf)) {
    throw "ClipForge.exe not found at $clipForgeExe. Run without -SkipPyInstaller first."
}

$iconPath = Join-Path $projectRoot "build\clipforge.ico"
if (-not (Test-Path -LiteralPath $iconPath -PathType Leaf)) {
    Write-Host "==> Generating ClipForge application icon..."
    $makeIconCode = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$projectRoot')
from studio.desktop import build_tray_icon
img = build_tray_icon()
if img is not None:
    b = Path(r'$projectRoot') / 'build'
    b.mkdir(parents=True, exist_ok=True)
    img.resize((256, 256)).save(b / 'clipforge.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
"@
    & $PythonExe -c $makeIconCode
}
if (-not (Test-Path -LiteralPath $iconPath -PathType Leaf)) {
    throw "Application icon not found at $iconPath."
}

function Resolve-RealExecutable([string]$toolName) {
    $cmd = Get-Command $toolName -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path -LiteralPath $cmd.Source -PathType Leaf)) {
        $item = Get-Item -LiteralPath $cmd.Source -Force
        if ($item.LinkType -and $item.Target) {
            $target = @($item.Target)[0]
            if ($target -and (Test-Path -LiteralPath $target -PathType Leaf)) {
                return (Resolve-Path -LiteralPath $target).Path
            }
        }
        if ($item.Length -gt 0) {
            return $item.FullName
        }
    }
    $pkgRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path -LiteralPath $pkgRoot) {
        $found = Get-ChildItem -LiteralPath $pkgRoot -Filter $toolName -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Length -gt 0 } |
            Select-Object -First 1
        if ($found) {
            return $found.FullName
        }
    }
    return $null
}

function Quote-Nsis([string]$val) {
    return $val.Replace("$", "$$").Replace('"', '$\"')
}

$stageDir = Join-Path $OutputDir "stage"
$installList = Join-Path $OutputDir "install-files.nsh"
$uninstallList = Join-Path $OutputDir "uninstall-files.nsh"

try {
    # 2. Prepare Staging Area
    if (Test-Path -LiteralPath $stageDir) {
        Remove-Item -Recurse -Force -LiteralPath $stageDir
    }
    New-Item -ItemType Directory -Force -Path $stageDir | Out-Null

    Write-Host "==> Staging ClipForge bundle into $stageDir..."
    Copy-Item -Path (Join-Path $bundleDir "*") -Destination $stageDir -Recurse -Force

    # 3. Optionally bundle ffmpeg & ffprobe (dereferencing WinGet symlinks)
    if ($BundleFfmpeg) {
        $ffBin = Join-Path $stageDir "ffmpeg\bin"
        New-Item -ItemType Directory -Force -Path $ffBin | Out-Null
        $copiedDirs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($tool in @("ffmpeg.exe", "ffprobe.exe")) {
            $realExe = Resolve-RealExecutable $tool
            if (-not $realExe) {
                throw "Cannot bundle $tool because it was not found on this machine."
            }
            Write-Host "==> Bundling $tool from $realExe..."
            Copy-Item -LiteralPath $realExe -Destination (Join-Path $ffBin $tool) -Force
            $srcDir = Split-Path -Parent $realExe
            if ($copiedDirs.Add($srcDir)) {
                Get-ChildItem -LiteralPath $srcDir -Filter "*.dll" -File -ErrorAction SilentlyContinue | ForEach-Object {
                    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $ffBin $_.Name) -Force
                }
            }
        }
    }

    # 4. Optional Authenticode signing
    $signtool = $null
    $certPassword = $null
    if ($CertPfxPath) {
        $certPassword = $env:CLIPFORGE_SIGNING_PASSWORD
        if (-not $certPassword) {
            throw "CLIPFORGE_SIGNING_PFX is set but CLIPFORGE_SIGNING_PASSWORD is not set."
        }
        $signtoolCmd = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
        $signtool = if ($signtoolCmd) { $signtoolCmd.Source } else {
            Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
                Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
        }
        if (-not $signtool) {
            throw "signtool.exe not found; cannot sign artifacts."
        }
        Write-Host "==> Authenticode signing staged ClipForge.exe..."
        & $signtool sign /fd SHA256 /tr $TimestampUrl /td SHA256 /f $CertPfxPath /p $certPassword (Join-Path $stageDir "ClipForge.exe")
        if ($LASTEXITCODE -ne 0) {
            throw "signtool failed on staged ClipForge.exe"
        }
    }

    # 5. Generate NSIS File Lists
    Write-Host "==> Generating installer file manifests..."
    $installLines = [System.Collections.Generic.List[string]]::new()
    $uninstallLines = [System.Collections.Generic.List[string]]::new()

    $files = @(Get-ChildItem -LiteralPath $stageDir -File -Recurse)
    foreach ($f in $files) {
        $rel = $f.FullName.Substring($stageDir.Length + 1)
        $parent = Split-Path $rel -Parent
        if ($parent) {
            $installLines.Add('SetOutPath "$INSTDIR\' + (Quote-Nsis $parent) + '"')
        } else {
            $installLines.Add('SetOutPath "$INSTDIR"')
        }
        $installLines.Add('File "' + (Quote-Nsis $f.FullName) + '"')
        $uninstallLines.Add('Delete "$INSTDIR\' + (Quote-Nsis $rel) + '"')
    }

    foreach ($d in (Get-ChildItem -LiteralPath $stageDir -Directory -Recurse | Sort-Object { $_.FullName.Length } -Descending)) {
        $rel = $d.FullName.Substring($stageDir.Length + 1)
        $uninstallLines.Add('RMDir "$INSTDIR\' + (Quote-Nsis $rel) + '"')
    }

    [System.IO.File]::WriteAllLines($installList, $installLines, [System.Text.UTF8Encoding]::new($true))
    [System.IO.File]::WriteAllLines($uninstallList, $uninstallLines, [System.Text.UTF8Encoding]::new($true))

    # 6. Compile Windows Setup Installer via NSIS
    $setupExe = Join-Path $OutputDir "ClipForge-v$Version-Setup-x64.exe"
    if (Test-Path -LiteralPath $setupExe) {
        Remove-Item -LiteralPath $setupExe -Force
    }
    Write-Host "==> Compiling NSIS Windows installer ($setupExe)..."
    $nsiScript = Join-Path $projectRoot "packaging\ClipForge.nsi"

    & $NsisCompiler `
        "/V2" `
        "/DVERSION=$Version" `
        "/DPROJECT_ROOT=$projectRoot" `
        "/DICON_PATH=$iconPath" `
        "/DSETUP_OUTPUT=$setupExe" `
        "/DINSTALL_FILES=$installList" `
        "/DUNINSTALL_FILES=$uninstallList" `
        $nsiScript

    if ($LASTEXITCODE -ne 0) {
        throw "NSIS compilation failed with code $LASTEXITCODE"
    }

    if ($CertPfxPath -and $signtool) {
        Write-Host "==> Authenticode signing Setup executable..."
        & $signtool sign /fd SHA256 /tr $TimestampUrl /td SHA256 /f $CertPfxPath /p $certPassword $setupExe
        if ($LASTEXITCODE -ne 0) {
            throw "signtool failed on $setupExe"
        }
    }

    # 7. Create Portable ZIP Distribution unless skipped
    $zipArchive = $null
    if (-not $SkipZip) {
        $zipArchive = Join-Path $OutputDir "ClipForge-v$Version-windows-x64.zip"
        Write-Host "==> Creating portable ZIP bundle ($zipArchive)..."
        if (Test-Path -LiteralPath $zipArchive) {
            Remove-Item -LiteralPath $zipArchive -Force
        }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory($stageDir, $zipArchive, [System.IO.Compression.CompressionLevel]::Optimal, $false)
    }

    # 8. Generate SHA256SUMS.txt
    $shaFile = Join-Path $OutputDir "SHA256SUMS.txt"
    $shaLines = Get-ChildItem -LiteralPath $OutputDir -File |
        Where-Object { $_.Name -match '^ClipForge-.*\.(exe|zip|msix)$' } |
        Sort-Object Name |
        ForEach-Object {
            $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
            "$hash  $($_.Name)"
        }
    Set-Content -LiteralPath $shaFile -Value $shaLines -Encoding ascii

    $setupSizeMb = [math]::Round(((Get-Item -LiteralPath $setupExe).Length / 1MB), 2)
    Write-Host "=========================================================="
    Write-Host "  ClipForge Windows NSIS Installer Built Successfully!"
    Write-Host "  Developer:  UshaLabs"
    Write-Host "  Version:    $Version (x64, Windows 10 & Windows 11)"
    Write-Host "  Installer:  $setupExe ($setupSizeMb MB)"
    if ($zipArchive) {
        $zipSizeMb = [math]::Round(((Get-Item -LiteralPath $zipArchive).Length / 1MB), 2)
        Write-Host "  Portable:   $zipArchive ($zipSizeMb MB)"
    }
    Write-Host "  SHA256:     $shaFile"
    Write-Host "=========================================================="
} finally {
    Remove-Item $installList -Force -ErrorAction SilentlyContinue
    Remove-Item $uninstallList -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $stageDir) {
        Remove-Item -Recurse -Force -LiteralPath $stageDir -ErrorAction SilentlyContinue
    }
}
