$out = "C:\Users\ss80751\OneDrive - NK\デスクトップ\file_list.csv"
$paths = @(
    "\\nksv1359.ad.nkc.co.jp\share",
    "\\nksv569.ad.nkc.co.jp\Share",
    "\\nksv523.ad.nkc.co.jp\Backup",
    "\\nksv523.ad.nkc.co.jp\LOG",
    "C:\Users\ss80751\NK"
)
$result = foreach ($p in $paths) {
    Get-ChildItem -Path $p -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $owner = try { (Get-Acl $_.FullName).Owner } catch { "" }
        [PSCustomObject]@{
            Name          = $_.Name
            LastWriteTime = $_.LastWriteTime
            Owner         = $owner
            DirectoryName = $_.DirectoryName
            Length        = $_.Length
        }
    }
}
$result |
    Sort-Object LastWriteTime -Descending |
    Export-Csv $out -Encoding UTF8 -NoTypeInformation
Invoke-Item $out