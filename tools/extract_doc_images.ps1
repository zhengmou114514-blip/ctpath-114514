$ErrorActionPreference = 'Stop'

$docPath = 'C:\Users\挣谋\Downloads\毕设论文.doc'
$workRoot = 'E:\CTpath-master'
$outDir = Join-Path $workRoot '_tmp_doc_images'
$htmlDir = Join-Path $outDir 'html'
$tempRoot = Join-Path $env:TEMP 'ctpath_doc_extract'
$docxPath = Join-Path $tempRoot 'thesis.docx'
$unzipDir = Join-Path $outDir 'docx_unzip'
$metaPath = Join-Path $outDir 'image_map.json'

if (Test-Path $outDir) {
  Remove-Item -LiteralPath $outDir -Recurse -Force
}
New-Item -ItemType Directory -Path $htmlDir -Force | Out-Null
New-Item -ItemType Directory -Path $unzipDir -Force | Out-Null
if (Test-Path $tempRoot) {
  Remove-Item -LiteralPath $tempRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

function Normalize-Text {
  param([string]$Text)
  if ($null -eq $Text) { return '' }
  return $Text.Replace("`r", [string]::Empty).Replace([string][char]7, [string]::Empty).Trim()
}

try {
  $doc = $word.Documents.Open($docPath, $false, $true)
  $wdFormatXMLDocument = 12
  $doc.SaveAs2($docxPath, $wdFormatXMLDocument)

  $paragraphs = $doc.Paragraphs
  $items = @()

  for ($i = 1; $i -le $doc.InlineShapes.Count; $i++) {
    $shape = $doc.InlineShapes.Item($i)
    $range = $shape.Range
    $caption = Normalize-Text $range.Paragraphs.Item(1).Range.Text
    $prev = ''
    $next = ''
    $wdParagraph = 4
    try { $prev = Normalize-Text $range.Previous($wdParagraph, 1).Text } catch {}
    try { $next = Normalize-Text $range.Next($wdParagraph, 1).Text } catch {}
    $items += [pscustomobject]@{
      shapeIndex   = $i
      captionText  = $caption
      previousText = $prev
      nextText     = $next
      width        = [int]$shape.Width
      height       = [int]$shape.Height
    }
  }

  for ($i = 1; $i -le $doc.Shapes.Count; $i++) {
    $shape = $doc.Shapes.Item($i)
    if (-not $shape.Anchor) { continue }
    $anchorText = Normalize-Text $shape.Anchor.Paragraphs.Item(1).Range.Text
    $prev = ''
    $next = ''
    $wdParagraph = 4
    try { $prev = Normalize-Text $shape.Anchor.Previous($wdParagraph, 1).Text } catch {}
    try { $next = Normalize-Text $shape.Anchor.Next($wdParagraph, 1).Text } catch {}
    $items += [pscustomobject]@{
      shapeIndex   = $i
      shapeType    = 'floating'
      captionText  = $anchorText
      previousText = $prev
      nextText     = $next
      width        = [int]$shape.Width
      height       = [int]$shape.Height
    }
  }

  $doc.Close($false)
  $doc = $null

  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::ExtractToDirectory($docxPath, $unzipDir)

  $mediaDir = Join-Path $unzipDir 'word\media'
  $exported = @()
  if (Test-Path $mediaDir) {
    Get-ChildItem -LiteralPath $mediaDir -File | ForEach-Object {
      if ($_.Extension -match '^\.(png|jpg|jpeg|gif|bmp|wmf|emf)$') {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $outDir $_.Name) -Force
        $exported += $_.Name
      }
    }
  }

  $payload = [pscustomobject]@{
    docPath        = $docPath
    exportedImages = $exported
    inlineShapes   = $items
  }
  $payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $metaPath -Encoding UTF8
  Write-Output $metaPath
  Write-Output ("exported_images={0}" -f $exported.Count)
  Write-Output ("inline_shapes={0}" -f $items.Count)
}
finally {
  if ($doc) { $doc.Close($false) }
  $word.Quit()
}
