param(
  [ValidateSet("no_path", "no_cl")]
  [string]$Mode = "no_path"
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "models")

$pythonExe = "python"
if ($env:CONDA_PREFIX) {
  $candidate = Join-Path $env:CONDA_PREFIX "python.exe"
  if (Test-Path $candidate) {
    $pythonExe = $candidate
  }
}

$args = @(
  "learner.py",
  "--dataset", "CHRONIC",
  "--rank", "800",
  "--valid_freq", "2",
  "--max_epochs", "20",
  "--learning_rate", "0.1",
  "--batch_size", "50",
  "--n_hidden", "160",
  "--num_walks", "1",
  "--walk_len", "8",
  "--gpu", "0",
  "--cuda", "cpu",
  "--save_root", (Join-Path $env:TEMP "ctpath_main_results")
)

if ($Mode -eq "no_path") {
  $args += "--disable_path"
}

if ($Mode -eq "no_cl") {
  $args += "--disable_cl"
}

Write-Host "Running CHRONIC ablation: $Mode"
& $pythonExe @args
