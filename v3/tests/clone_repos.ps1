# clone_repos.ps1
# Downloads all repositories for CodeTruth Agent V3 real scan
# Run: .\v3\tests\clone_repos.ps1
# From: C:\AI_Project\CodeTruthAgent

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CodeTruth Agent V3 — Repository Downloader" -ForegroundColor Cyan
Write-Host "  Downloading 14 repositories to C:\repos\v3\" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Create target directory
$repoDir = "C:\repos\v3"
if (-not (Test-Path $repoDir)) {
    New-Item -ItemType Directory -Force -Path $repoDir | Out-Null
    Write-Host "`n  Created directory: $repoDir" -ForegroundColor Green
}

Set-Location $repoDir

# Repository list
$repos = @(
    # Python Web
    @{ Name="Django";          Url="https://github.com/django/django";                        Category="Python Web"      },
    @{ Name="Flask";           Url="https://github.com/pallets/flask";                        Category="Python Web"      },
    @{ Name="FastAPI";         Url="https://github.com/tiangolo/fastapi";                     Category="Python Web"      },

    # Python ML
    @{ Name="Transformers";    Url="https://github.com/huggingface/transformers";             Category="Python ML"       },

    # C / Systems
    @{ Name="Redis";           Url="https://github.com/redis/redis";                          Category="C / Systems"     },
    @{ Name="Nginx";           Url="https://github.com/nginx/nginx";                          Category="C / Systems"     },

    # Java
    @{ Name="Spring Boot";     Url="https://github.com/spring-projects/spring-boot";         Category="Java"            },
    @{ Name="Elasticsearch";   Url="https://github.com/elastic/elasticsearch";               Category="Java"            },

    # JavaScript / TypeScript
    @{ Name="VSCode";          Url="https://github.com/microsoft/vscode";                    Category="JavaScript/TS"   },
    @{ Name="React";           Url="https://github.com/facebook/react";                      Category="JavaScript/TS"   },

    # Rust
    @{ Name="Rust";            Url="https://github.com/rust-lang/rust";                      Category="Rust"            },

    # Go
    @{ Name="Go";              Url="https://github.com/golang/go";                           Category="Go"              },

    # ERP
    @{ Name="Odoo";            Url="https://github.com/odoo/odoo";                           Category="ERP"             },
    @{ Name="SAP UI5";         Url="https://github.com/sap/ui5-webcomponents";              Category="ERP"             }
)

$total    = $repos.Count
$success  = 0
$skipped  = 0
$failed   = 0

Write-Host ""
Write-Host "  $total repositories to download" -ForegroundColor Yellow
Write-Host ""

foreach ($repo in $repos) {
    $folderName = ($repo.Url -split "/")[-1]
    $targetPath = Join-Path $repoDir $folderName

    Write-Host "  [$($repo.Category)] $($repo.Name)" -NoNewline

    if (Test-Path $targetPath) {
        Write-Host "  SKIPPED (already exists)" -ForegroundColor Yellow
        $skipped++
        continue
    }

    try {
        $result = git clone --depth=1 $repo.Url $targetPath 2>&1
        if ($LASTEXITCODE -eq 0) {
            $fileCount = (Get-ChildItem -Recurse -File $targetPath -ErrorAction SilentlyContinue).Count
            Write-Host "  DONE ($fileCount files)" -ForegroundColor Green
            $success++
        } else {
            Write-Host "  FAILED" -ForegroundColor Red
            Write-Host "    $result" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  DOWNLOAD SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Downloaded : $success" -ForegroundColor Green
Write-Host "  Skipped    : $skipped (already existed)" -ForegroundColor Yellow
Write-Host "  Failed     : $failed" -ForegroundColor Red
Write-Host "  Location   : $repoDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Next step:" -ForegroundColor White
Write-Host "  cd C:\AI_Project\CodeTruthAgent" -ForegroundColor White
Write-Host "  python v3/tests/scan_all_repos.py" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
