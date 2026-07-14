$desktop = [Environment]::GetFolderPath('Desktop')

# 文件名"编程学习平台"用 codepoint 防 UTF-8/GBK 编码错乱
$nameChars = 0x7F16, 0x7A0B, 0x5B66, 0x4E60, 0x5E73, 0x53F0
$name = -join ($nameChars | ForEach-Object { [char]$_ })
$shortcutPath = Join-Path $desktop ($name + '.lnk')

# 删除旧版本
if (Test-Path -LiteralPath $shortcutPath) { Remove-Item -LiteralPath $shortcutPath -Force }

# 找 pythonw.exe（优先用户级 Python 安装）
$pythonw = $null
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
if (-not $pythonw) {
    Write-Error "找不到 pythonw.exe"
    exit 1
}

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = $pythonw
$sc.Arguments = '"D:\code\learning-system\launcher.pyw"'
$sc.WorkingDirectory = 'D:\code\learning-system'
$sc.IconLocation = 'D:\code\learning-system\assets\app.ico,0'
$descChars = 0x56DB, 0x8BED, 0x7F16, 0x7A0B, 0x5B66, 0x4E60, 0x5E73, 0x53F0,
             0x0020, 0x002D, 0x0020, 0x684C, 0x9762, 0x7AEF, 0x5E94, 0x7528
$sc.Description = -join ($descChars | ForEach-Object { [char]$_ })
$sc.WindowStyle = 1
$sc.Save()

[Console]::OutputEncoding = [Text.Encoding]::UTF8
Write-Host ('Created: ' + $shortcutPath)
Write-Host ('Target:  ' + $pythonw)
Write-Host ('Args:    "D:\code\learning-system\launcher.pyw"')
Write-Host ('Icon:    D:\code\learning-system\assets\app.ico')
Write-Host ('Exists:  ' + (Test-Path -LiteralPath $shortcutPath))
