param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
    python .\business_prompt_lab\agent_room.py @Args
}
finally {
    Pop-Location
}
