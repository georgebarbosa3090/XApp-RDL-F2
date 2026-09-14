$targets = @("Makefile", "README.md", "pytest.ini", "requirements.txt", "requirements-dev.txt", "requirements-ml.txt")
foreach ($t in $targets) {
    if (Test-Path $t) {
        $content = [System.IO.File]::ReadAllText($t)
        $content = $content -replace "`r`n", "`n"
        [System.IO.File]::WriteAllText($t, $content, [System.Text.UTF8Encoding]::new($false))
    }
}

$dirs = @("scripts", "simulations", "src", "deploy", "tests", "configs", "docs")
foreach ($d in $dirs) {
    if (Test-Path $d) {
        Get-ChildItem -Path $d -Recurse -File | ForEach-Object {
            $ext = $_.Extension.ToLower()
            if ($ext -notin @(".png", ".jpg", ".pdf", ".pyc", ".ico")) {
                $content = [System.IO.File]::ReadAllText($_.FullName)
                $content = $content -replace "`r`n", "`n"
                [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.UTF8Encoding]::new($false))
            }
        }
    }
}
Write-Host "LF normalization complete."
