# Telegram sohbet botunu Cloudflare'e kurar. Tüm anahtarları SEN girersin; hiçbir yere kaydedilmez.
$ErrorActionPreference = "Stop"; Set-Location $PSScriptRoot
$repo = "aykutdemirer-cmyk/gozunuzun-onundeki-hileler"
function W($m, $c = "Cyan") { Write-Host "`n$m" -ForegroundColor $c }

W "1/6 Cloudflare girisi (tarayicida 'Allow' de)"
npx -y wrangler@latest login

W "2/6 Hafiza alani olusturuluyor"
if ((Get-Content wrangler.toml -Raw) -match 'id = "KV_ID"') {
  $o = npx -y wrangler@latest kv namespace create STATE 2>&1 | Out-String
  $id = [regex]::Match($o, '[0-9a-f]{32}').Value
  if (-not $id) { Write-Host $o; throw "KV olusturulamadi" }
  (Get-Content wrangler.toml -Raw) -replace 'KV_ID', $id | Set-Content wrangler.toml -Encoding utf8
}

W "3/6 Telegram"
$tok = Read-Host "Botun token'ini yapistir"
Write-Host "Simdi Telegram'da bu bota bir mesaj at (or. merhaba), sonra Enter'a bas." -ForegroundColor Yellow; Read-Host | Out-Null
Invoke-RestMethod "https://api.telegram.org/bot$tok/deleteWebhook" | Out-Null
$u = Invoke-RestMethod "https://api.telegram.org/bot$tok/getUpdates"
$chat = ($u.result | Where-Object { $_.message } | Select-Object -Last 1).message.chat.id
if (-not $chat) { throw "Mesaj bulunamadi. Bota mesaj atip scripti tekrar calistir." }
Write-Host "Chat ID: $chat" -ForegroundColor Green

W "4/6 Gemini anahtari (aistudio.google.com/apikey adresinden ucretsiz)"
$gem = Read-Host "Gemini API anahtarini yapistir"

W "5/6 Anahtarlar Cloudflare'e kaydediliyor"
$ghAns = Read-Host "Botun GitHub'a bolum ekleyebilmesi icin GitHub CLI oturumundaki token kullanilsin mi? (E/H)"
if ($ghAns -match '^[Ee]') { $gh = gh auth token } else { $gh = Read-Host "GitHub token'ini (repo yazma izinli) yapistir" }
$sec = -join ((48..57) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
$tok  | npx -y wrangler@latest secret put TELEGRAM_BOT_TOKEN
"$chat" | npx -y wrangler@latest secret put ALLOWED_CHAT_ID
$gem  | npx -y wrangler@latest secret put GEMINI_API_KEY
$gh   | npx -y wrangler@latest secret put GITHUB_TOKEN
$sec  | npx -y wrangler@latest secret put WEBHOOK_SECRET

W "6/6 Yayinlaniyor ve Telegram'a baglaniyor"
$o = npx -y wrangler@latest deploy 2>&1 | Out-String
$url = [regex]::Match($o, 'https://[^\s]+\.workers\.dev').Value
if (-not $url) { Write-Host $o; throw "Deploy URL bulunamadi" }
Invoke-RestMethod "https://api.telegram.org/bot$tok/setWebhook" -Method Post -Body @{ url = $url; secret_token = $sec; allowed_updates = '["message","callback_query"]' } | Out-Null
$tok  | gh secret set TELEGRAM_BOT_TOKEN -R $repo
"$chat" | gh secret set TELEGRAM_CHAT_ID -R $repo
W "Kurulum tamam! Telegram'da bota /start yaz." "Green"
