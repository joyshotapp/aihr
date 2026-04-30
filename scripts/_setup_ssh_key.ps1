Import-Module Posh-SSH
$password = ConvertTo-SecureString "Bravomix0715" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("root", $password)
$pubkey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ6kReElllH3KwSEYJOts3Rv0Wep91ZS3bA6dyxhe1jq y.c.chen1112@gmail.com"

Write-Host "Connecting to 172.235.216.122..."
try {
    $session = New-SSHSession -ComputerName "172.235.216.122" -Credential $cred -AcceptKey -Force -ConnectionTimeout 15 -ErrorAction Stop
    Write-Host "Connected! Session ID: $($session.SessionId)"

    $cmd = "mkdir -p /root/.ssh && chmod 700 /root/.ssh && grep -qF '$pubkey' /root/.ssh/authorized_keys 2>/dev/null || echo '$pubkey' >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys && echo 'KEY_ADDED_OK'"
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command $cmd
    Write-Host "Result: $($result.Output)"

    Remove-SSHSession -SessionId $session.SessionId | Out-Null
    Write-Host "Session closed."
} catch {
    Write-Host "ERROR: $_"
}
