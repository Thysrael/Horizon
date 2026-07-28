[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [string]$Distro,

    [Parameter(Mandatory = $true)]
    [string]$LinuxRepoPath,

    [string]$LinuxEnvFile = ".env.notion-agent",

    [string]$TaskName = "Horizon Notion Codex Agent",

    [string]$CloudflaredTunnelName = "",

    [string]$TunnelTaskName = "Horizon Notion Cloudflare Tunnel",

    [switch]$StartNow
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command "wsl.exe" -ErrorAction SilentlyContinue)) {
    throw "wsl.exe is required."
}

$escapedRepo = $LinuxRepoPath.Replace("'", "'\''")
$escapedEnv = $LinuxEnvFile.Replace("'", "'\''")
$command = @(
    "-d", $Distro,
    "--",
    "bash", "-lc",
    "cd '$escapedRepo' && exec uv run horizon-notion-agent --env-file '$escapedEnv' serve"
)

$argumentParts = $command | ForEach-Object {
        if ($_ -match "\s") { '"' + $_.Replace('"', '\"') + '"' } else { $_ }
    }
$action = New-ScheduledTaskAction `
    -Execute "wsl.exe" `
    -Argument ($argumentParts -join " ")
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

if ($PSCmdlet.ShouldProcess($TaskName, "Register local Notion Codex agent")) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Runs the Horizon Notion webhook listener and local Codex worker." `
        -Force | Out-Null

    if ($StartNow) {
        Start-ScheduledTask -TaskName $TaskName
    }

    Write-Host "Registered scheduled task: $TaskName"
}

if ($CloudflaredTunnelName) {
    $escapedTunnel = $CloudflaredTunnelName.Replace("'", "'\''")
    $tunnelArguments = @(
        "-d", $Distro,
        "--",
        "bash", "-lc",
        "exec cloudflared tunnel run '$escapedTunnel'"
    ) | ForEach-Object {
        if ($_ -match "\s") { '"' + $_.Replace('"', '\"') + '"' } else { $_ }
    }
    $tunnelAction = New-ScheduledTaskAction `
        -Execute "wsl.exe" `
        -Argument ($tunnelArguments -join " ")

    if ($PSCmdlet.ShouldProcess(
        $TunnelTaskName,
        "Register Cloudflare Tunnel for the local Notion Codex agent"
    )) {
        Register-ScheduledTask `
            -TaskName $TunnelTaskName `
            -Action $tunnelAction `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Runs the stable Cloudflare Tunnel for Horizon's Notion webhook." `
            -Force | Out-Null

        if ($StartNow) {
            Start-ScheduledTask -TaskName $TunnelTaskName
        }

        Write-Host "Registered scheduled task: $TunnelTaskName"
    }
}
