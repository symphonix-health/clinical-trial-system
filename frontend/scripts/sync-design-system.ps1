# Sync minimal Symphonix Health design system assets from submodule to public/
# Run from frontend/scripts/.
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$sourceRoot = Join-Path (Join-Path (Join-Path $repoRoot '.agents') 'skills') 'symphonix-health-design'
$destRoot = Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'public') 'design-system'

$files = @(
  'colors_and_type.css',
  'healthcare/tokens.css'
)
foreach ($f in $files) {
  $src = Join-Path $sourceRoot $f
  $dst = Join-Path $destRoot $f
  New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
  Copy-Item $src $dst -Force
}

$fontSrc = Join-Path (Join-Path $sourceRoot 'assets') 'fonts'
$fontDst = Join-Path (Join-Path $destRoot 'assets') 'fonts'
New-Item -ItemType Directory -Path $fontDst -Force | Out-Null
Copy-Item (Join-Path $fontSrc '*') $fontDst -Recurse -Force
