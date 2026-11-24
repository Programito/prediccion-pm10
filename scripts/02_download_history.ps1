# Descarga fuentes oficiales sin modificar su contenido. Ejecutar desde PowerShell.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$rawRoot = Join-Path $projectRoot 'data\raw\health_air_history'
New-Item -ItemType Directory -Path $rawRoot -Force | Out-Null
$inventory = [System.Collections.Generic.List[object]]::new()

function Get-PageLinks([string]$Url) {
    $html = (Invoke-WebRequest -Uri $Url -TimeoutSec 40).Content
    foreach ($match in [regex]::Matches($html, '<a\b[^>]*href="(?<href>[^"]+)"[^>]*>(?<text>.*?)</a>', 'Singleline')) {
        $text = [System.Net.WebUtility]::HtmlDecode(($match.Groups['text'].Value -replace '<[^>]+>', '')).Trim()
        $href = [System.Net.WebUtility]::HtmlDecode($match.Groups['href'].Value)
        [pscustomobject]@{Text=$text; Url=([uri]::new([uri]$Url, $href)).AbsoluteUri}
    }
}

function Save-Source([int]$Year, [string]$Kind, [string]$Url, [string]$Page, [string]$Extension) {
    $fileName = "${Kind}_${Year}.${Extension}"
    $filePath = Join-Path $rawRoot $fileName
    try {
        if (-not (Test-Path -LiteralPath $filePath)) {
            $partialPath = "$filePath.part"
            Invoke-WebRequest -Uri $Url -OutFile $partialPath -TimeoutSec 50
            Move-Item -LiteralPath $partialPath -Destination $filePath -Force
        }
        $inventory.Add([pscustomobject]@{year=$Year;kind=$Kind;file=$fileName;source_url=$Url;catalog_url=$Page;bytes=(Get-Item -LiteralPath $filePath).Length;sha256=(Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLower();status='downloaded'})
        Write-Output "Descargado: $fileName"
    } catch {
        $inventory.Add([pscustomobject]@{year=$Year;kind=$Kind;source_url=$Url;status='error';error=$_.Exception.Message})
        Write-Output "Error: $fileName - $($_.Exception.Message)"
    }
}

$ineIndex = 'https://www.ine.es/dynt3/inebase/es/index.htm?capsel=8593&padre=2590'
$yearLinks = @(Get-PageLinks $ineIndex | Where-Object {$_.Text -match '^(Año 20\d\d|Encuesta de morbilidad hospitalaria\. Año 20\d\d)$'})
foreach ($yearLink in $yearLinks) {
    $year = [int]([regex]::Match($yearLink.Text, '20\d\d').Value)
    # Desde 2016 se trabaja con CIE-10-MC. Los cambios internos también se revisarán.
    if ($year -lt 2016 -or $year -gt 2024) { continue }
    try {
        $links = @(Get-PageLinks $yearLink.Url)
        $table = @($links | Where-Object {$_.Text -like 'Tasas de Morbilidad Hospitalaria*' -and $_.Text -like '*de residencia*'})
        if ($table.Count -eq 0) {
            $provincePage = $links | Where-Object {$_.Text -eq 'Resultados por comunidades autónomas y provincias'} | Select-Object -First 1
            if ($provincePage) {
                $links = @(Get-PageLinks $provincePage.Url)
                $table = @($links | Where-Object {$_.Text -like 'Tasas de Morbilidad Hospitalaria*' -and $_.Text -like '*de residencia*'})
            }
        }
        if ($table.Count -ne 1 -or $table[0].Url -notmatch 'tpx=(\d+)') { throw 'No se ha encontrado una única tabla de tasas por residencia.' }
        $tableId = $Matches[1]
        Save-Source $year 'ine_tasas_residencia' "https://www.ine.es/jaxi/files/tpx/csv_bdsc/$tableId.csv" $table[0].Url 'csv'
    } catch {
        $inventory.Add([pscustomobject]@{year=$year;kind='ine_tasas_residencia';status='discovery_error';error=$_.Exception.Message;catalog_url=$yearLink.Url})
        Write-Output "Pendiente INE $year : $($_.Exception.Message)"
    }
}

$mitecoIndex = 'https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/evaluacion-y-datos-de-calidad-del-aire/datos/datos-historicos.html'
$airYears = @(Get-PageLinks $mitecoIndex | Where-Object {$_.Text -match '^Datos 20\d\d$'})
$airYears += [pscustomobject]@{Text='Datos 2024';Url='https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/evaluacion-y-datos-de-calidad-del-aire/datos/datos-oficiales-2024.html'}
foreach ($airYear in $airYears) {
    $year = [int]([regex]::Match($airYear.Text, '20\d\d').Value)
    if ($year -lt 2016 -or $year -gt 2024) { continue }
    try {
        $links = @(Get-PageLinks $airYear.Url)
        $daily = $links | Where-Object {$_.Text -match '^Datos diarios'} | Select-Object -First 1
        if (-not $daily) { throw 'No se ha localizado un enlace separado de datos diarios; revisar el formato histórico.' }
        Save-Source $year 'miteco_diarios' $daily.Url $airYear.Url 'zip'
        $hourly = $links | Where-Object {$_.Text -match '^Datos horarios'} | Select-Object -First 1
        if ($hourly) { Save-Source $year 'miteco_horarios' $hourly.Url $airYear.Url 'zip' }
        $meta = $links | Where-Object {$_.Text -match '^Metainformación' -and $_.Url -match '\.xlsx?$'} | Select-Object -First 1
        if ($meta) { Save-Source $year 'miteco_estaciones' $meta.Url $airYear.Url ([IO.Path]::GetExtension(([uri]$meta.Url).AbsolutePath).TrimStart('.')) }
    } catch {
        $inventory.Add([pscustomobject]@{year=$year;kind='miteco_diarios';status='discovery_error';error=$_.Exception.Message;catalog_url=$airYear.Url})
        Write-Output "Pendiente MITECO $year : $($_.Exception.Message)"
    }
}
@{retrieved_on='2026-11-15';note='Originales sin transform. downloaded confirma descarga; el contenido se valida por separado.';sources=$inventory.ToArray()} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'sources.json') -Encoding utf8
