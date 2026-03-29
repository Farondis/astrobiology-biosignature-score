param(
  [string]$ManifestPath = ".\\veri_manifest_sablonu.csv"
)

$rows = Import-Csv -Path $ManifestPath

foreach ($row in $rows) {
  if ([string]::IsNullOrWhiteSpace($row.local_path)) { continue }

  if (Test-Path -Path $row.local_path) {
    $hash = Get-FileHash -Path $row.local_path -Algorithm SHA256
    $row.sha256 = $hash.Hash.ToLower()
  }
}

$rows | Export-Csv -Path $ManifestPath -NoTypeInformation -Encoding UTF8
Write-Host "SHA256 alanlari guncellendi:" $ManifestPath
