# Amazon Search Ranking System - 100 unique-query benchmark
# Works with Windows PowerShell 5.1+ and PowerShell 7+.
# Does not upload results anywhere. The API must already be running locally.
param(
    [string]$BaseUrl = 'http://127.0.0.1:8000',
    [int]$TopK = 5,
    [int]$CandidateK = 100,
    [string]$OutputDir = (Join-Path $PSScriptRoot 'benchmark_results'),
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
$BaseUrl = $BaseUrl.TrimEnd('/')
if ($TopK -lt 1 -or $CandidateK -lt $TopK) {
    throw 'Invalid request settings: CandidateK must be >= TopK >= 1.'
}

function Invoke-Search([string]$Query) {
    $payload = @{ query = $Query; top_k = $TopK; candidate_k = $CandidateK } | ConvertTo-Json -Compress
    $clock = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $result = Invoke-RestMethod -Uri "$BaseUrl/search" -Method Post -ContentType 'application/json' -Body $payload -TimeoutSec $TimeoutSeconds
        $clock.Stop()
        return [pscustomobject]@{ response = $result; client_ms = $clock.Elapsed.TotalMilliseconds }
    } catch {
        $clock.Stop()
        throw
    }
}

function Get-Stats([double[]]$Values) {
    if ($Values.Count -eq 0) { return $null }
    $sorted = @($Values | Sort-Object)
    $sum = 0.0
    foreach ($value in $Values) { $sum += $value }
    $p50 = [math]::Max(0, [math]::Ceiling(0.50 * $Values.Count) - 1)
    $p95 = [math]::Max(0, [math]::Ceiling(0.95 * $Values.Count) - 1)
    $p99 = [math]::Max(0, [math]::Ceiling(0.99 * $Values.Count) - 1)
    return [pscustomobject]@{
        count = $Values.Count
        mean = [math]::Round($sum / $Values.Count, 2)
        p50 = [math]::Round([double]$sorted[$p50], 2)
        p95 = [math]::Round([double]$sorted[$p95], 2)
        p99 = [math]::Round([double]$sorted[$p99], 2)
        min = [math]::Round([double]$sorted[0], 2)
        max = [math]::Round([double]$sorted[$sorted.Count-1], 2)
    }
}

# Twenty product themes x five unique natural-language variants = 100 distinct queries.
# This measures runtime, NOT relevance scores or NDCG.
$products = @(
    'lip stain', 'lip balm', 'lip gloss', 'matte lipstick', 'waterproof mascara',
    'black eyeliner', 'eye shadow palette', 'liquid foundation',
    'under eye concealer', 'powder blush', 'vitamin c serum',
    'hyaluronic acid serum', 'daily face moisturizer', 'gentle facial cleanser',
    'mineral sunscreen', 'hair shampoo', 'hair conditioner',
    'body lotion', 'perfume', 'makeup remover'
)
$patterns = @(
    'best {0} for everyday use',
    'affordable {0} for beginners',
    'long lasting {0} with good reviews',
    'lightweight {0} for sensitive skin',
    'high quality {0} without strong fragrance'
)
$queries = @(
    foreach ($pattern in $patterns) {
        foreach ($product in $products) {
            $pattern -f $product
        }
    }
)
if (($queries.Count -ne 100) -or ((@($queries | Select-Object -Unique)).Count -ne 100)) {
    throw 'Benchmark must have exactly 100 distinct queries.'
}

Write-Host "Checking API: $BaseUrl/health" -ForegroundColor Cyan
try { $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 40 }
catch { Write-Host 'API is unreachable. Start FastAPI first (see RUN_ME_ZH.md).' -ForegroundColor Red; throw }
if ($health.status -ne 'ok') { throw 'API /health did not return status=ok.' }
Write-Host "Healthy. Catalog: $($health.catalog_products); FAISS: $($health.faiss_products); ranker features: $($health.ranker_features)."

# Warm up framework/model once, not included in measured count.
Write-Host 'Sending one unmeasured warm-up request ...'
try { $null = Invoke-Search 'basic skin care gift set' }
catch { Write-Host 'Warm-up failed. Verify artifacts and server logs.' -ForegroundColor Red; throw }

$rows = New-Object 'System.Collections.Generic.List[object]'
for ($i=0; $i -lt $queries.Count; $i++) {
    $query = $queries[$i]
    try {
        $res = Invoke-Search $query
        $r = $res.response
        $returned = @($r.results).Count
        if ($null -eq $r.latency_ms -or $null -eq $r.latency_ms.total) {
            throw 'Missing latency_ms.total in server response.'
        }
        $success = ($returned -eq $TopK)
        $errorText = if ($success) { '' } else { "Expected $TopK results, got $returned" }
        $row = [pscustomobject]@{
            request_id = $i + 1
            query = $query
            success = $success
            returned_count = $returned
            pipeline_ms = [math]::Round([double]$r.latency_ms.total, 3)
            client_ms = [math]::Round([double]$res.client_ms, 3)
            embedding_ms = [math]::Round([double]$r.latency_ms.embedding, 3)
            retrieval_ms = [math]::Round([double]$r.latency_ms.retrieval, 3)
            features_ms = [math]::Round([double]$r.latency_ms.features, 3)
            ranking_ms = [math]::Round([double]$r.latency_ms.ranking, 3)
            error = $errorText
        }
    } catch {
        $row = [pscustomobject]@{
            request_id = $i + 1
            query = $query
            success = $false
            returned_count = 0
            pipeline_ms = $null
            client_ms = $null
            embedding_ms = $null
            retrieval_ms = $null
            features_ms = $null
            ranking_ms = $null
            error = [string]$_.Exception.Message
        }
        Write-Host "FAIL $($i + 1)/100 : $query : $($row.error)" -ForegroundColor Red
    }
    $rows.Add($row)
    if ((($i + 1) % 10) -eq 0) {
        Write-Host ("Completed {0}/100 requests" -f ($i + 1)) -ForegroundColor Yellow
    }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$csvPath = Join-Path $OutputDir 'benchmark_100_queries.csv'
$mdPath = Join-Path $OutputDir 'benchmark_100_queries_summary.md'
$rows | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

$good = @($rows | Where-Object { $_.success -eq $true })
$failCount = $rows.Count - $good.Count
$pipeline = Get-Stats ([double[]]@($good | ForEach-Object { [double]$_.pipeline_ms }))
$client = Get-Stats ([double[]]@($good | ForEach-Object { [double]$_.client_ms }))
$under200 = @($good | Where-Object { $_.pipeline_ms -lt 200 }).Count
$timeStamp = [DateTimeOffset]::Now.ToString('yyyy-MM-dd HH:mm:ss zzz')
$summary = @(
    '# Local FastAPI Benchmark - 100 Distinct Queries',
    '',
    "- Executed at: $timeStamp",
    "- API: $BaseUrl/search (local machine)",
    "- Catalog / FAISS index: $($health.catalog_products) / $($health.faiss_products)",
    "- LambdaMART feature count: $($health.ranker_features)",
    "- Request setting: Top-K=$TopK, Candidate-K=$CandidateK",
    "- Requests: $($rows.Count), successes: $($good.Count), failures: $failCount",
    "- Successful requests under 200ms pipeline target: $under200 / $($good.Count)",
    '',
    '| Latency statistic | Pipeline (server-reported) | Client round-trip (PowerShell) |',
    '|---|---:|---:|'
)
if ($null -ne $pipeline) {
    $summary += "| Mean | $($pipeline.mean) ms | $($client.mean) ms |"
    $summary += "| P50 | $($pipeline.p50) ms | $($client.p50) ms |"
    $summary += "| P95 | $($pipeline.p95) ms | $($client.p95) ms |"
    $summary += "| P99 | $($pipeline.p99) ms | $($client.p99) ms |"
    $summary += "| Min | $($pipeline.min) ms | $($client.min) ms |"
    $summary += "| Max | $($pipeline.max) ms | $($client.max) ms |"
}
$summary += ''
$summary += '**Methodology:** One warm-up request followed by 100 distinct product queries, sent sequentially (concurrency=1). Percentiles use the nearest-rank method on successful requests only. An already-running API and a warm model mean these are NOT clean cold-start measurements. Server-reported pipeline time and PowerShell HTTP round-trip time are different metrics. Results are local smoke/latency evidence, not a production load test, statistical guarantee, or ranking-quality benchmark.'
$summary += ''
$summary += 'Review and rerun independently before citing these numbers in a resume or README.'
$summary | Set-Content -Path $mdPath -Encoding UTF8

Write-Host ''
Write-Host '==== Benchmark Results ====' -ForegroundColor Cyan
Write-Host "Success: $($good.Count)/100 ; failures: $failCount"
if ($null -ne $pipeline) {
    Write-Host "Pipeline: Mean=$($pipeline.mean) ms, P50=$($pipeline.p50) ms, P95=$($pipeline.p95) ms, P99=$($pipeline.p99) ms"
    Write-Host "HTTP round-trip: Mean=$($client.mean) ms, P50=$($client.p50) ms, P95=$($client.p95) ms, P99=$($client.p99) ms"
    Write-Host "Pipeline under 200 ms: $under200 / $($good.Count) successful requests"
}
Write-Host "CSV: $csvPath"
Write-Host "GitHub-ready summary: $mdPath"
if ($failCount -gt 0) { Write-Warning 'Some searches failed; inspect CSV before claiming success.' }
