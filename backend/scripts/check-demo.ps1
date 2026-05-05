$ErrorActionPreference = "Stop"

$baseUrl = "http://127.0.0.1:8000"

Write-Host "Checking backend health..." -ForegroundColor Cyan
$health = Invoke-RestMethod "$baseUrl/api/health"
$health | ConvertTo-Json -Depth 4

Write-Host "`nLogging in with demo doctor account..." -ForegroundColor Cyan
$login = Invoke-RestMethod -Method POST "$baseUrl/api/login" `
  -ContentType "application/json" `
  -Body '{"username":"demo_clinic","password":"demo123456"}'
$token = $login.token
$headers = @{ Authorization = "Bearer $token" }

Write-Host "`nFetching patient list..." -ForegroundColor Cyan
$patients = Invoke-RestMethod "$baseUrl/api/patients" -Headers $headers
$patients | ConvertTo-Json -Depth 5

$patientId = if ($patients.items.Count -gt 0) { $patients.items[0].patientId } else { "PID0248" }

Write-Host "`nFetching patient detail for $patientId ..." -ForegroundColor Cyan
$patient = Invoke-RestMethod "$baseUrl/api/patient/$patientId" -Headers $headers
$patient | ConvertTo-Json -Depth 6

Write-Host "`nFetching timeline for $patientId ..." -ForegroundColor Cyan
$timeline = Invoke-RestMethod "$baseUrl/api/timeline/$patientId" -Headers $headers
$timeline | ConvertTo-Json -Depth 6

Write-Host "`nRequesting prediction for $patientId ..." -ForegroundColor Cyan
$predict = Invoke-RestMethod -Method POST "$baseUrl/api/predict" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body (@{ patientId = $patientId; topk = 3 } | ConvertTo-Json)
$predict | ConvertTo-Json -Depth 6
