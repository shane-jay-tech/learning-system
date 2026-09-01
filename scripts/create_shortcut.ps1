# 生成桌面快捷方式：优先用项目自带的 .venv（依赖都在里面），
# 否则回退到用户级 Python。路径全部由 $PSScriptRoot 推导，仓库移动后依然有效。
$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot | Split-Path -Parent
$launcher = Join-Path $repo 'launcher.pyw'
$icon = Join-Path $repo 'assets\app.ico'
$venvPythonw = Join-Path $repo '.venv\Scripts\pythonw.exe'

if (-not (Test-Path -LiteralPath $launcher)) {
    Write-Error "找不到 $launcher"
    exit 1
}

# 1) 项目 venv 的 pythonw（依赖齐全，最可靠）
$pythonw = $null
if (Test-Path -LiteralPath $venvPythonw) {
    $pythonw = $venvPythonw
} else {
    # 2) 用户级 Python 安装
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\pythonw.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { $pythonw = $c; break }
    }
    if (-not $pythonw) {
        $cmd = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)
        if ($cmd) { $pythonw = $cmd.Source }
    }
}
if (-not $pythonw) {
    Write-Error "找不到 pythonw.exe（请先安装 Python 或创建 .venv）"
    exit 1
}

$desktop = [Environment]::GetFolderPath('Desktop')

# 文件名"编程学习平台"用 codepoint 防 UTF-8/GBK 编码错乱
$nameChars = 0x7F16, 0x7A0B, 0x5B66, 0x4E60, 0x5E73, 0x53F0
$name = -join ($nameChars | ForEach-Object { [char]$_ })
$shortcutPath = Join-Path $desktop ($name + '.lnk')

# 删除旧版本
if (Test-Path -LiteralPath $shortcutPath) { Remove-Item -LiteralPath $shortcutPath -Force }

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = $pythonw
$sc.Arguments = '"' + $launcher + '"'
$sc.WorkingDirectory = $repo
if (Test-Path -LiteralPath $icon) { $sc.IconLocation = $icon + ',0' }
$descChars = 0x56DB, 0x8BED, 0x7F16, 0x7A0B, 0x5B66, 0x4E60, 0x5E73, 0x53F0,
             0x0020, 0x002D, 0x0020, 0x684C, 0x9762, 0x7AEF, 0x5E94, 0x7528
$sc.Description = -join ($descChars | ForEach-Object { [char]$_ })
$sc.WindowStyle = 1
$sc.Save()

[Console]::OutputEncoding = [Text.Encoding]::UTF8
Write-Host ('Created: ' + $shortcutPath)
Write-Host ('Target:  ' + $pythonw)
Write-Host ('Args:    "' + $launcher + '"')
Write-Host ('Working: ' + $repo)
Write-Host ('Icon:    ' + $icon)
Write-Host ('Exists:  ' + (Test-Path -LiteralPath $shortcutPath))
