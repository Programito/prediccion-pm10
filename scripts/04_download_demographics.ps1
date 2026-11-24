$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$folder = Join-Path $root 'data\raw\demographics'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$name = 'ine_poblacion_provincias_edad_56945.csv'
$url = 'https://www.ine.es/jaxiT3/files/t/csv_bdsc/56945.csv'
$path = Join-Path $folder $name
if (-not (Test-Path -LiteralPath $path)) {
    Invoke-WebRequest -Uri $url -OutFile "$path.part" -TimeoutSec 60
    Move-Item -LiteralPath "$path.part" -Destination $path
}
@{retrieved_on=(Get-Date -Format 'yyyy-MM-dd');file=$name;source_url=$url;catalog_url='https://www.ine.es/jaxiT3/Tabla.htm?t=56945';bytes=(Get-Item -LiteralPath $path).Length;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower();note='Serie histórica oficial revisada ECP; no son versiones publicadas en cada fecha histórica.'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'source.json') -Encoding utf8
