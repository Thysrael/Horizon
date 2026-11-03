<#
    Horizon 每日简报 —— 由 Windows 计划任务调用（每天 18:00）

    用法：
      powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_daily.ps1
      powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_daily.ps1 -Hours 12

    说明：
      - 工作目录固定为 Horizon 仓库根，config.json 里的相对路径（profiles/、data/）才能正确解析
      - AI provider 为 minimax / MiniMax-M3.1-Flash（国内站 api.minimaxi.com），密钥取自 .env
      - 日志写入 data\logs\horizon-<时间戳>.log
#>
[CmdletBinding()]
param(
    [string]$Hours = '24',
    [switch]$DryRun,
    [switch]$SkipQuotaCheck,
    [switch]$NoEmail,
    [switch]$MailOnly
)

$ErrorActionPreference = 'Continue'

$HorizonHome = 'E:\DeepSeek Harness\Horizon'

$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { $uv = 'C:\Users\weant\.local\bin\uv.exe' }
if (-not (Test-Path -LiteralPath $uv)) {
    Write-Error "uv 未找到（查找路径：$uv）"
    exit 127
}

Set-Location -LiteralPath $HorizonHome

$logDir = Join-Path $HorizonHome 'data\logs'
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}
# MailOnly 只补发邮件、不采集，用独立前缀，避免被当成采集日志。
$logPrefix = if ($MailOnly) { 'horizon-mailonly' } else { 'horizon' }
$logFile = Join-Path $logDir ("{0}-{1}.log" -f $logPrefix, (Get-Date -Format 'yyyyMMdd-HHmmss'))

$env:UV_CACHE_DIR = Join-Path $env:LOCALAPPDATA 'uv\cache'
# ---- MiniMax 配额预检 ------------------------------------------------------------
# 若套餐用量已耗尽（HTTP 429 + 错误码 2056），直接中止，避免跑完整管线后
# 把当天已有的完整日报覆盖成"增强失败"的残缺版。其它错误（超时、网络抖动）
# 不中止，照常运行。
$envFile = Join-Path $HorizonHome '.env'
$apiKey = $null
if (Test-Path -LiteralPath $envFile) {
    $keyLine = Select-String -LiteralPath $envFile -Pattern '^MINIMAX_API_KEY=' | Select-Object -First 1
    if ($keyLine) { $apiKey = ($keyLine.Line -replace '^MINIMAX_API_KEY=', '').Trim() }
}

if ($apiKey -and -not $SkipQuotaCheck -and -not $MailOnly) {
    $probeBody = '{"model":"MiniMax-M3.1-Flash","messages":[{"role":"user","content":"ping"}],"max_tokens":16}'
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $probe = Invoke-WebRequest -Uri 'https://api.minimaxi.com/v1/chat/completions' `
            -Method Post -Headers @{ Authorization = "Bearer $apiKey" } `
            -ContentType 'application/json' -Body $probeBody -TimeoutSec 30 -UseBasicParsing
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] quota precheck: OK (HTTP $($probe.StatusCode))" |
            Tee-Object -FilePath $logFile -Append
    } catch {
        $code = $null
        try { $code = [int]$_.Exception.Response.StatusCode } catch { }
        $body = $_.ErrorDetails.Message
        if ($code -eq 429 -and ($body -match '2056' -or $body -match 'Token Plan')) {
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] quota precheck: EXHAUSTED (HTTP 429, error 2056) - aborting; existing summary left untouched" |
                Tee-Object -FilePath $logFile -Append
            exit 3
        }
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] quota precheck: inconclusive (HTTP $code) - continuing" |
            Tee-Object -FilePath $logFile -Append
    }
}
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ===== Horizon daily run start (hours=$Hours) =====" |
    Tee-Object -FilePath $logFile

# ---- DryRun：不写任何文件 ---------------------------------------------------------
# 必须放在备份段之前：否则会先复制出 .prev 再直接退出，留下一批孤儿 .prev。
if ($DryRun) {
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] DRY-RUN: would execute -> $uv run horizon --hours $Hours (cwd=$(Get-Location))" |
        Tee-Object -FilePath $logFile -Append
    exit 0
}

# ---- 运行前备份当天日报 -----------------------------------------------------------
# Horizon 按 UTC 日期命名产物（北京时间 18:00 = UTC 10:00，仍是同一天）。
# 若同一天跑了两次而第二次因配额/网络失败，残缺版会覆盖已有的完整版。
# 这里先留一份 .prev，运行后再按质量决定是否回滚。
$utcDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$summaryFile = Join-Path $HorizonHome ("data\summaries\horizon-{0}-zh.md" -f $utcDate)
$postsFile = Join-Path $HorizonHome ("docs\_posts\{0}-summary-zh.md" -f $utcDate)
$backedUp = $false

if ($MailOnly) {
    # 只补发通知邮件：复用当天已生成的日报，不重新采集，也不改动任何日报文件。
    $code = 0
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] MAIL-ONLY: skipping collection, reusing existing digest for $utcDate" |
        Tee-Object -FilePath $logFile -Append
} else {
    if (Test-Path -LiteralPath $summaryFile) {
        Copy-Item -LiteralPath $summaryFile -Destination "$summaryFile.prev" -Force
        $backedUp = $true
    }
    if (Test-Path -LiteralPath $postsFile) {
        Copy-Item -LiteralPath $postsFile -Destination "$postsFile.prev" -Force
    }

    & $uv run horizon --hours $Hours *>&1 | Tee-Object -FilePath $logFile -Append
    $code = $LASTEXITCODE
}

# ---- 运行后校验：增强失败过多则回滚 -------------------------------------------------
# 日志里的 "Enriched X/Y items" 说明有多少条拿到了背景补充。增强失败意味着
# 该条目在日报里只剩一行摘要、没有背景/社区讨论/参考链接，质量明显下降。
# 失败超过三分之一时，宁可保留上一版完整日报，也不要用残缺版覆盖它。
if ($code -eq 0) {
    # 逐行取最后一条 "Enriched X/Y items"，避免整份日志读进内存
    $lastEnrich = Select-String -LiteralPath $logFile -Pattern 'Enriched (\d+)/(\d+) items' |
        Select-Object -Last 1
    if ($lastEnrich) {
        $ok = [int]$lastEnrich.Matches[0].Groups[1].Value
        $total = [int]$lastEnrich.Matches[0].Groups[2].Value
        $failed = $total - $ok
        # 运行中途撞上配额上限（HTTP 429 / error 2056）同样是质量事故：预检只能
        # 证明"此刻能调用"，证明不了"额度够跑完整轮"。分析阶段被 429 打断会让
        # 条目缺失评分，增强阶段被打断会让条目只剩一行摘要。
        $quotaHit = Select-String -LiteralPath $logFile -Pattern '429 Too Many Requests|error..2056|Token Plan' -Quiet
        if ($quotaHit) {
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARNING: quota hit mid-run (HTTP 429) - digest is incomplete" |
                Tee-Object -FilePath $logFile -Append
        }
        # 失败超过 1/3 即视为质量不可接受（用乘法比较，避免依赖 [math]）
        if ($quotaHit -or ($total -gt 0 -and ($failed * 3) -gt $total)) {
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARNING: enrichment failed for $failed/$total items - digest quality degraded" |
                Tee-Object -FilePath $logFile -Append
            if ($backedUp -and (Test-Path -LiteralPath "$summaryFile.prev")) {
                Move-Item -LiteralPath "$summaryFile.prev" -Destination $summaryFile -Force
                if (Test-Path -LiteralPath "$postsFile.prev") {
                    Move-Item -LiteralPath "$postsFile.prev" -Destination $postsFile -Force
                }
                "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] rolled back to previous complete digest for $utcDate" |
                    Tee-Object -FilePath $logFile -Append
            } else {
                "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] no previous digest to roll back to; partial digest kept" |
                    Tee-Object -FilePath $logFile -Append
            }
        }
        # 无论质量是否达标，清理本次备份，避免 .prev 残留
        Remove-Item -LiteralPath "$summaryFile.prev" -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath "$postsFile.prev" -Force -ErrorAction SilentlyContinue
    }
}
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ===== Horizon daily run finished, exit code: $code =====" |
    Tee-Object -FilePath $logFile -Append

# ---- 邮件通知 ----------------------------------------------------------------------
# SMTP 配置写在 .env（已被 .gitignore 忽略）：
#   SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD / SMTP_TO / SMTP_SENDER_NAME
# 缺任何一项都只是跳过发送，不影响日报产出与退出码。
function Get-EnvValue([string]$Name) {
    $envFile = Join-Path $HorizonHome '.env'
    if (-not (Test-Path -LiteralPath $envFile)) { return $null }
    foreach ($line in (Get-Content -LiteralPath $envFile -ErrorAction SilentlyContinue)) {
        if ($line -match "^\s*$Name\s*=") {
            $v = ($line -split '=', 2)[1].Trim()
            $v = $v -replace '^"(.*)"$', '$1'
            $v = $v -replace "^'(.*)'$", '$1'
            return $v
        }
    }
    return $null
}

$smtpHost = Get-EnvValue 'SMTP_HOST'
$smtpUser = Get-EnvValue 'SMTP_USERNAME'
$smtpPass = Get-EnvValue 'SMTP_PASSWORD'
$smtpTo = Get-EnvValue 'SMTP_TO'
$smtpPort = Get-EnvValue 'SMTP_PORT'
if (-not $smtpPort) { $smtpPort = '465' }
$senderName = Get-EnvValue 'SMTP_SENDER_NAME'
if (-not $senderName) { $senderName = 'Horizon Daily Briefing' }

# 统计信息来自本次运行日志；MAIL-ONLY 模式下本次日志为空，改用最近一次采集日志。
$statsLog = $logFile
if ($MailOnly) {
    # 统计必须来自真正跑过采集的日志：排除本次新建的日志，并要求日志里
    # 含 "Fetched N items from all sources"，否则会选到只发过邮件的空日志。
    $latestLog = Get-ChildItem -LiteralPath $logDir -Filter 'horizon-*.log' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -ne $logFile } |
        Sort-Object LastWriteTime -Descending |
        Where-Object {
            (Select-String -LiteralPath $_.FullName -Pattern 'Fetched (\d+) items from all sources' -Quiet)
        } |
        Select-Object -First 1
    if ($latestLog) { $statsLog = $latestLog.FullName }
}

$emailSent = $false
$emailNote = ''
if ($NoEmail) {
    $emailNote = 'skipped (-NoEmail)'
} elseif (-not ($smtpHost -and $smtpUser -and $smtpPass -and $smtpTo)) {
    $emailNote = 'skipped (SMTP config incomplete in .env)'
} else {
    try {
        # 从日志里抽统计（只用纯 ASCII 模式，日志里的 emoji 是 GBK 乱码，不能匹配）
        $fetched = 0
        $m = Select-String -LiteralPath $statsLog -Pattern 'Fetched (\d+) items from all sources' | Select-Object -Last 1
        if ($m) { $fetched = [int]$m.Matches[0].Groups[1].Value }
        $selected = 0
        $m = Select-String -LiteralPath $statsLog -Pattern '(\d+) unique items' | Select-Object -Last 1
        if ($m) { $selected = [int]$m.Matches[0].Groups[1].Value }
        $enrichOk = 0
        $enrichTotal = 0
        $m = Select-String -LiteralPath $statsLog -Pattern 'Enriched (\d+)/(\d+) items' | Select-Object -Last 1
        if ($m) {
            $enrichOk = [int]$m.Matches[0].Groups[1].Value
            $enrichTotal = [int]$m.Matches[0].Groups[2].Value
        }

        # 条目标题与评分
        $entries = @()
        if (Test-Path -LiteralPath $summaryFile) {
            foreach ($l in (Get-Content -LiteralPath $summaryFile -Encoding UTF8 -ErrorAction SilentlyContinue)) {
                if ($l -match '^###\s+\[(.+?)\]\(.+?\)\s*(.*?)\s*(\d+\.\d+)/10') {
                    $entries += ,@($Matches[1], $Matches[3])
                }
            }
        }

        $sb = New-Object System.Text.StringBuilder
        if ($code -eq 0) {
            $subject = "Horizon Daily Briefing - $utcDate"
            [void]$sb.AppendLine("Horizon 每日速递 - $utcDate")
            [void]$sb.AppendLine()
            [void]$sb.AppendLine("采集 $fetched 条 -> 筛选入选 $selected 条（背景增强 $enrichOk/$enrichTotal 条完成）")
            [void]$sb.AppendLine("生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
            [void]$sb.AppendLine("文件：$summaryFile")
            [void]$sb.AppendLine()
            if ($entries.Count -gt 0) {
                [void]$sb.AppendLine("本期条目：")
                $i = 0
                foreach ($e in $entries) {
                    $i++
                    [void]$sb.AppendLine("$i. [$($e[1])/10] $($e[0])")
                }
                [void]$sb.AppendLine()
            }
            [void]$sb.AppendLine('完整日报见附件（Markdown）。')
        } else {
            $subject = "Horizon Daily Briefing FAILED - $utcDate"
            [void]$sb.AppendLine("Horizon 每日速递运行失败 - $utcDate")
            [void]$sb.AppendLine()
            [void]$sb.AppendLine("退出码：$code")
            [void]$sb.AppendLine("时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
            [void]$sb.AppendLine("日志：$logFile")
            [void]$sb.AppendLine("采集 $fetched 条 -> 入选 $selected 条，背景增强 $enrichOk/$enrichTotal")
            [void]$sb.AppendLine()
            [void]$sb.AppendLine('常见原因：MiniMax 套餐用量上限（HTTP 429 / error 2056）。')
        }

        # 用 Python 的 smtplib 发送（scripts\send_mail.py）：
        # Windows PowerShell 5.1 的 System.Net.Mail.SmtpClient 在认证阶段会被
        # 阿里企业邮箱断开（net_io_connectionclosed / SmtpException GeneralFailure），
        # 同样的凭据用 Python 正常认证并发送成功。
        # 正文先写成 UTF-8 临时文件再传路径，避开 Windows 命令行的中文编码问题。
        # 正文同时落盘到 data\logs，方便事后复核邮件到底发了什么。
        $bodyFile = Join-Path $logDir ("mail-body-{0}.txt" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
        $bodyText = $sb.ToString()
        [System.IO.File]::WriteAllText($bodyFile, $bodyText, (New-Object System.Text.UTF8Encoding($false)))
        [System.IO.File]::WriteAllText($bodyFile, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
        try {
            $mailArgs = @(
                'run', 'python', (Join-Path $HorizonHome 'scripts\send_mail.py'),
                '--env', $envFile,
                '--subject', $subject,
                '--body', $bodyFile,
                '--to', $smtpTo,
                '--from-name', $senderName
            )
            if (Test-Path -LiteralPath $summaryFile) {
                # --markdown 渲染成 HTML 正文（Outlook 优先显示），--attach 保留原文。
                $mailArgs += @('--markdown', $summaryFile)
                $mailArgs += @('--attach', $summaryFile)
            }
            $mailOutput = & $uv @mailArgs 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw ("send_mail.py failed (exit {0}): {1}" -f $LASTEXITCODE, ($mailOutput -join ' '))
            }
            # 把 send_mail.py 的输出（含 dkim=signed:... 签名状态）落到日志里。
            foreach ($line in $mailOutput) {
                $lineText = "$line"
                Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] mail: $lineText"
                if ($logFile) {
                    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] mail: $lineText" | Tee-Object -FilePath $logFile -Append
                }
            }
            $emailSent = $true
            $emailNote = "sent to $smtpTo"
        } finally {
            # 正文副本保留在 data\logs\mail-body-*.txt，临时文件不再需要。
            Remove-Item -LiteralPath ($bodyFile + '.tmp') -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # 展开异常链，并解出 SmtpException 的服务器应答，否则只能看到
        # "Failure sending mail." 这种没有信息量的提示。
        $detail = $_.Exception.Message
        $ex = $_.Exception
        while ($ex.InnerException) {
            $ex = $ex.InnerException
            $detail = "$detail | $($ex.Message)"
        }
        if ($ex.PSObject.Properties.Name -contains 'Response' -and $ex.Response) {
            $detail = "$detail | server: $([System.Text.Encoding]::UTF8.GetString($ex.Response))"
        }
        $emailNote = "send failed: $detail"
    }
}
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] email: $emailNote" | Tee-Object -FilePath $logFile -Append

exit $code
