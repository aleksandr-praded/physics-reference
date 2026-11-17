param(
    [Parameter(Mandatory)]
    [string]$InputFile
)

if (-not (Test-Path -LiteralPath $InputFile)) {
    Write-Error "Файл '$InputFile' не найден."
    exit 1
}

$OutputPdf = [IO.Path]::GetFileNameWithoutExtension($InputFile) + '.pdf'

Write-Host "🚀 Сборка: $InputFile -> $OutputPdf" -ForegroundColor Cyan

pandoc $InputFile -o $OutputPdf `
    --pdf-engine=xelatex `
    --template=my_template.tex `
    --highlight-style=tango

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Ошибка сборки: pandoc вернул код $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "✅ Успех! Открываю $OutputPdf..." -ForegroundColor Green
Start-Process $OutputPdf