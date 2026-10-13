########################################################################### 
#    Version 1.0 - 07/16/2018
#    Version 1.1 - 07/20/2018
#
#    ti_update_status.ps1: 
#
#    This script is designed to parse the most recent ThinInstaller log 
#    file and populate the Lenovo_Updates WMI class with status of updates
#    processed by ThinInstaller.  This class can then be inventoried by 
#    SCCM. 
#
#    Copyright Lenovo. All Rights Reserved.
########################################################################### 

###########################################################################
#    Functions
###########################################################################

#####################################
# Function to create class.
#####################################
function createclass {
    #make sure the Lenovo namespace exists
    $ns = [wmiclass]'root:__namespace'
    $sc = $ns.CreateInstance()
    $sc.Name = 'Lenovo'
    $sc.Put()

    #create Lenovo_Updates class insance in the Lenovo namespace 
    $myclass = New-Object System.Management.ManagementClass ("root\Lenovo", [string]::Empty, $null)
    $myclass["__CLASS"] = "Lenovo_Updates"
    $myclass.Qualifiers.Add("SMS_Report", $true)
    $myclass.Qualifiers.Add("SMS_Group_Name", "Lenovo_Updates")
    $myclass.Qualifiers.Add("SMS_Class_Id", "Lenovo_Updates")

    $myclass.Properties.Add("PackageID", [System.Management.CimType]::String, $false)
    $myclass.Properties.Add("Title", [System.Management.CimType]::String, $false)
    $myclass.Properties.Add("Status", [System.Management.CimType]::String, $false)
    $myclass.Properties.Add("AdditionalInfo", [System.Management.CimType]::String, $false)
	$myclass.Properties.Add("Version", [System.Management.CimType]::String, $false)
    $myclass.Properties.Add("Severity", [System.Management.CimType]::String, $false)
	$myclass.Properties.Add("InstallDate", [System.Management.CimType]::String, $false)
    
    $myclass.Properties["PackageID"].Qualifiers.Add("Key", $true)
    $myclass.Properties["PackageID"].Qualifiers.Add("SMS_Report", $true)
    $myclass.Properties["Title"].Qualifiers.Add("SMS_Report", $true)
    $myclass.Properties["Status"].Qualifiers.Add("SMS_Report", $true)
    $myclass.Properties["AdditionalInfo"].Qualifiers.Add("SMS_Report", $true)
	$myclass.Properties["Version"].Qualifiers.Add("SMS_Report", $true)
	$myclass.Properties["Severity"].Qualifiers.Add("SMS_Report", $true)
	$myclass.Properties["InstallDate"].Qualifiers.Add("SMS_Report", $true)

    $myclass.Put()
}

#####################################
# Function to add all update statuses 
# from log file to the WMI class
#####################################
function addstatus {
    # get current log file and parse

    # following path will need to be modified before implementing in production
    $updateHistory = "update_history.txt"

    Get-Content $updateHistory | ForEach-Object {
        $oneRecord = $_ -split " %-% "
        $packageid = $oneRecord[0]
        $title = $oneRecord[1]
        $status = $oneRecord[2]
        $additionalInfo = $oneRecord[3]
        $version = $oneRecord[4]
        $Severity = $oneRecord[5]
		$InstallDate = $oneRecord[6]
        try {
            $update = Get-WmiObject -Namespace root\Lenovo -Class Lenovo_Updates -Filter "PackageID = '$packageid'"
            if ($update.PackageID -eq $packageid) {
                if ($update.Status -ne $status -or $update.Title -ne $title -or $update.AdditionalInfo -ne $additionalInfo -or $update.Version -ne $version -or $update.Severity -ne $Severity -or $update.InstallDate -ne $InstallDate) {
                    $update.Status = $status
                    $update.Title = $title
                    $update.AdditionalInfo = $additionalInfo
                    $update.Version = $version
                    $update.Severity = $Severity
					$update.InstallDate = $InstallDate
                    $update.Put()
                }
            }
            else {
                Set-WmiInstance -Namespace root\Lenovo -Class Lenovo_updates -Arguments @{PackageID = $packageid; Title = $title; Status = $status; AdditionalInfo = $additionalInfo; Version = $version; Severity = $Severity; InstallDate = $InstallDate} -PutType CreateOnly
            }
        }
        catch {
            "Did not add"
            $packageid + " " + $title + " " + $status
        }
    }

}

##########################################
# Function to check whether old WMI exist
# If yes backup
##########################################
function backup {
    Get-WmiObject -Class lenovo_updates -Namespace root\lenovo -Filter "InstallDate=''" -ErrorAction SilentlyContinue -ErrorVariable isoldwmi
    if ($isoldwmi) {
        try {
            $oldWmi = Get-WmiObject -Class Lenovo_Updates -Namespace root\Lenovo
            Remove-WmiObject -Class Lenovo_Updates -Namespace root\Lenovo
            createclass
            $oldWmi | ForEach-Object {
                $packageid = $_.PackageID
                $title = $_.Title
                $status = $_.Status
                $additionalInfo = $_.AdditionalInfo
                $version = $_.Version
                $Severity = $_.Severity
                Set-WmiInstance -Class Lenovo_Updates -Namespace root\Lenovo -Arguments @{PackageID = $packageid; Title = $title; Status = $status; AdditionalInfo = $additionalInfo; Version = $version; Severity = $Severity; InstallDate = ''} -PutType CreateOnly
            }
        }
        catch {
            "Backup WMI class failed"
        }
    }
}

###########################################################################
#    Main
###########################################################################

# Create custom class if needed
[void](Get-WMIObject -Namespace root\Lenovo Lenovo_Updates -ErrorAction SilentlyContinue -ErrorVariable wmiclasserror)
if ($wmiclasserror) {
    try { 
        createclass 
    }
    catch {
        "Could not create WMI class"
        Exit 1
    }
}
backup
addstatus

# Optional to execute a H/W inventory cycle - requires CM Client installed
#$SMSCli = [wmiclass] "\\.\root\ccm:SMS_Client"
#$SMSCli.TriggerSchedule("{00000000-0000-0000-0000-000000000001}")

# SIG # Begin signature block
# MIItqAYJKoZIhvcNAQcCoIItmTCCLZUCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCDb8kbueNSuRyhw
# Z3D9qL2cbPD/0ZRX5BmQExWoSLOUTaCCJqswggWNMIIEdaADAgECAhAOmxiO+dAt
# 5+/bUOIIQBhaMA0GCSqGSIb3DQEBDAUAMGUxCzAJBgNVBAYTAlVTMRUwEwYDVQQK
# EwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xJDAiBgNV
# BAMTG0RpZ2lDZXJ0IEFzc3VyZWQgSUQgUm9vdCBDQTAeFw0yMjA4MDEwMDAwMDBa
# Fw0zMTExMDkyMzU5NTlaMGIxCzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxEaWdpQ2Vy
# dCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xITAfBgNVBAMTGERpZ2lD
# ZXJ0IFRydXN0ZWQgUm9vdCBHNDCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoC
# ggIBAL/mkHNo3rvkXUo8MCIwaTPswqclLskhPfKK2FnC4SmnPVirdprNrnsbhA3E
# MB/zG6Q4FutWxpdtHauyefLKEdLkX9YFPFIPUh/GnhWlfr6fqVcWWVVyr2iTcMKy
# unWZanMylNEQRBAu34LzB4TmdDttceItDBvuINXJIB1jKS3O7F5OyJP4IWGbNOsF
# xl7sWxq868nPzaw0QF+xembud8hIqGZXV59UWI4MK7dPpzDZVu7Ke13jrclPXuU1
# 5zHL2pNe3I6PgNq2kZhAkHnDeMe2scS1ahg4AxCN2NQ3pC4FfYj1gj4QkXCrVYJB
# MtfbBHMqbpEBfCFM1LyuGwN1XXhm2ToxRJozQL8I11pJpMLmqaBn3aQnvKFPObUR
# WBf3JFxGj2T3wWmIdph2PVldQnaHiZdpekjw4KISG2aadMreSx7nDmOu5tTvkpI6
# nj3cAORFJYm2mkQZK37AlLTSYW3rM9nF30sEAMx9HJXDj/chsrIRt7t/8tWMcCxB
# YKqxYxhElRp2Yn72gLD76GSmM9GJB+G9t+ZDpBi4pncB4Q+UDCEdslQpJYls5Q5S
# UUd0viastkF13nqsX40/ybzTQRESW+UQUOsxxcpyFiIJ33xMdT9j7CFfxCBRa2+x
# q4aLT8LWRV+dIPyhHsXAj6KxfgommfXkaS+YHS312amyHeUbAgMBAAGjggE6MIIB
# NjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBTs1+OC0nFdZEzfLmc/57qYrhwP
# TzAfBgNVHSMEGDAWgBRF66Kv9JLLgjEtUYunpyGd823IDzAOBgNVHQ8BAf8EBAMC
# AYYweQYIKwYBBQUHAQEEbTBrMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdp
# Y2VydC5jb20wQwYIKwYBBQUHMAKGN2h0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNv
# bS9EaWdpQ2VydEFzc3VyZWRJRFJvb3RDQS5jcnQwRQYDVR0fBD4wPDA6oDigNoY0
# aHR0cDovL2NybDMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0QXNzdXJlZElEUm9vdENB
# LmNybDARBgNVHSAECjAIMAYGBFUdIAAwDQYJKoZIhvcNAQEMBQADggEBAHCgv0Nc
# Vec4X6CjdBs9thbX979XB72arKGHLOyFXqkauyL4hxppVCLtpIh3bb0aFPQTSnov
# Lbc47/T/gLn4offyct4kvFIDyE7QKt76LVbP+fT3rDB6mouyXtTP0UNEm0Mh65Zy
# oUi0mcudT6cGAxN3J0TU53/oWajwvy8LpunyNDzs9wPHh6jSTEAZNUZqaVSwuKFW
# juyk1T3osdz9HNj0d1pcVIxv76FQPfx2CWiEn2/K2yCNNWAcAgPLILCsWKAOQGPF
# mCLBsln1VWvPJ6tsds5vIy30fnFqI2si/xK4VC0nftg62fC2h5b9W9FcrBjDTZ9z
# twGpn1eqXijiuZQwggWQMIIDeKADAgECAhAFmxtXno4hMuI5B72nd3VcMA0GCSqG
# SIb3DQEBDAUAMGIxCzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMx
# GTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xITAfBgNVBAMTGERpZ2lDZXJ0IFRy
# dXN0ZWQgUm9vdCBHNDAeFw0xMzA4MDExMjAwMDBaFw0zODAxMTUxMjAwMDBaMGIx
# CzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3
# dy5kaWdpY2VydC5jb20xITAfBgNVBAMTGERpZ2lDZXJ0IFRydXN0ZWQgUm9vdCBH
# NDCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAL/mkHNo3rvkXUo8MCIw
# aTPswqclLskhPfKK2FnC4SmnPVirdprNrnsbhA3EMB/zG6Q4FutWxpdtHauyefLK
# EdLkX9YFPFIPUh/GnhWlfr6fqVcWWVVyr2iTcMKyunWZanMylNEQRBAu34LzB4Tm
# dDttceItDBvuINXJIB1jKS3O7F5OyJP4IWGbNOsFxl7sWxq868nPzaw0QF+xembu
# d8hIqGZXV59UWI4MK7dPpzDZVu7Ke13jrclPXuU15zHL2pNe3I6PgNq2kZhAkHnD
# eMe2scS1ahg4AxCN2NQ3pC4FfYj1gj4QkXCrVYJBMtfbBHMqbpEBfCFM1LyuGwN1
# XXhm2ToxRJozQL8I11pJpMLmqaBn3aQnvKFPObURWBf3JFxGj2T3wWmIdph2PVld
# QnaHiZdpekjw4KISG2aadMreSx7nDmOu5tTvkpI6nj3cAORFJYm2mkQZK37AlLTS
# YW3rM9nF30sEAMx9HJXDj/chsrIRt7t/8tWMcCxBYKqxYxhElRp2Yn72gLD76GSm
# M9GJB+G9t+ZDpBi4pncB4Q+UDCEdslQpJYls5Q5SUUd0viastkF13nqsX40/ybzT
# QRESW+UQUOsxxcpyFiIJ33xMdT9j7CFfxCBRa2+xq4aLT8LWRV+dIPyhHsXAj6Kx
# fgommfXkaS+YHS312amyHeUbAgMBAAGjQjBAMA8GA1UdEwEB/wQFMAMBAf8wDgYD
# VR0PAQH/BAQDAgGGMB0GA1UdDgQWBBTs1+OC0nFdZEzfLmc/57qYrhwPTzANBgkq
# hkiG9w0BAQwFAAOCAgEAu2HZfalsvhfEkRvDoaIAjeNkaA9Wz3eucPn9mkqZucl4
# XAwMX+TmFClWCzZJXURj4K2clhhmGyMNPXnpbWvWVPjSPMFDQK4dUPVS/JA7u5iZ
# aWvHwaeoaKQn3J35J64whbn2Z006Po9ZOSJTROvIXQPK7VB6fWIhCoDIc2bRoAVg
# X+iltKevqPdtNZx8WorWojiZ83iL9E3SIAveBO6Mm0eBcg3AFDLvMFkuruBx8lbk
# apdvklBtlo1oepqyNhR6BvIkuQkRUNcIsbiJeoQjYUIp5aPNoiBB19GcZNnqJqGL
# FNdMGbJQQXE9P01wI4YMStyB0swylIQNCAmXHE/A7msgdDDS4Dk0EIUhFQEI6FUy
# 3nFJ2SgXUE3mvk3RdazQyvtBuEOlqtPDBURPLDab4vriRbgjU2wGb2dVf0a1TD9u
# KFp5JtKkqGKX0h7i7UqLvBv9R0oN32dmfrJbQdA75PQ79ARj6e/CVABRoIoqyc54
# zNXqhwQYs86vSYiv85KZtrPmYQ/ShQDnUBrkG5WdGaG5nLGbsQAe79APT0JsyQq8
# 7kP6OnGlyE0mpTX9iV28hWIdMtKgK1TtmlfB2/oQzxm3i0objwG2J5VT6LaJbVu8
# aNQj6ItRolb58KaAoNYes7wPD1N1KarqE3fk3oyBIa0HEEcRrYc9B9F1vM/zZn4w
# ggauMIIElqADAgECAhAHNje3JFR82Ees/ShmKl5bMA0GCSqGSIb3DQEBCwUAMGIx
# CzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3
# dy5kaWdpY2VydC5jb20xITAfBgNVBAMTGERpZ2lDZXJ0IFRydXN0ZWQgUm9vdCBH
# NDAeFw0yMjAzMjMwMDAwMDBaFw0zNzAzMjIyMzU5NTlaMGMxCzAJBgNVBAYTAlVT
# MRcwFQYDVQQKEw5EaWdpQ2VydCwgSW5jLjE7MDkGA1UEAxMyRGlnaUNlcnQgVHJ1
# c3RlZCBHNCBSU0E0MDk2IFNIQTI1NiBUaW1lU3RhbXBpbmcgQ0EwggIiMA0GCSqG
# SIb3DQEBAQUAA4ICDwAwggIKAoICAQDGhjUGSbPBPXJJUVXHJQPE8pE3qZdRodbS
# g9GeTKJtoLDMg/la9hGhRBVCX6SI82j6ffOciQt/nR+eDzMfUBMLJnOWbfhXqAJ9
# /UO0hNoR8XOxs+4rgISKIhjf69o9xBd/qxkrPkLcZ47qUT3w1lbU5ygt69OxtXXn
# HwZljZQp09nsad/ZkIdGAHvbREGJ3HxqV3rwN3mfXazL6IRktFLydkf3YYMZ3V+0
# VAshaG43IbtArF+y3kp9zvU5EmfvDqVjbOSmxR3NNg1c1eYbqMFkdECnwHLFuk4f
# sbVYTXn+149zk6wsOeKlSNbwsDETqVcplicu9Yemj052FVUmcJgmf6AaRyBD40Nj
# gHt1biclkJg6OBGz9vae5jtb7IHeIhTZgirHkr+g3uM+onP65x9abJTyUpURK1h0
# QCirc0PO30qhHGs4xSnzyqqWc0Jon7ZGs506o9UD4L/wojzKQtwYSH8UNM/STKvv
# mz3+DrhkKvp1KCRB7UK/BZxmSVJQ9FHzNklNiyDSLFc1eSuo80VgvCONWPfcYd6T
# /jnA+bIwpUzX6ZhKWD7TA4j+s4/TXkt2ElGTyYwMO1uKIqjBJgj5FBASA31fI7tk
# 42PgpuE+9sJ0sj8eCXbsq11GdeJgo1gJASgADoRU7s7pXcheMBK9Rp6103a50g5r
# mQzSM7TNsQIDAQABo4IBXTCCAVkwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4E
# FgQUuhbZbU2FL3MpdpovdYxqII+eyG8wHwYDVR0jBBgwFoAU7NfjgtJxXWRM3y5n
# P+e6mK4cD08wDgYDVR0PAQH/BAQDAgGGMBMGA1UdJQQMMAoGCCsGAQUFBwMIMHcG
# CCsGAQUFBwEBBGswaTAkBggrBgEFBQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQu
# Y29tMEEGCCsGAQUFBzAChjVodHRwOi8vY2FjZXJ0cy5kaWdpY2VydC5jb20vRGln
# aUNlcnRUcnVzdGVkUm9vdEc0LmNydDBDBgNVHR8EPDA6MDigNqA0hjJodHRwOi8v
# Y3JsMy5kaWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkUm9vdEc0LmNybDAgBgNV
# HSAEGTAXMAgGBmeBDAEEAjALBglghkgBhv1sBwEwDQYJKoZIhvcNAQELBQADggIB
# AH1ZjsCTtm+YqUQiAX5m1tghQuGwGC4QTRPPMFPOvxj7x1Bd4ksp+3CKDaopafxp
# wc8dB+k+YMjYC+VcW9dth/qEICU0MWfNthKWb8RQTGIdDAiCqBa9qVbPFXONASIl
# zpVpP0d3+3J0FNf/q0+KLHqrhc1DX+1gtqpPkWaeLJ7giqzl/Yy8ZCaHbJK9nXzQ
# cAp876i8dU+6WvepELJd6f8oVInw1YpxdmXazPByoyP6wCeCRK6ZJxurJB4mwbfe
# Kuv2nrF5mYGjVoarCkXJ38SNoOeY+/umnXKvxMfBwWpx2cYTgAnEtp/Nh4cku0+j
# Sbl3ZpHxcpzpSwJSpzd+k1OsOx0ISQ+UzTl63f8lY5knLD0/a6fxZsNBzU+2QJsh
# IUDQtxMkzdwdeDrknq3lNHGS1yZr5Dhzq6YBT70/O3itTK37xJV77QpfMzmHQXh6
# OOmc4d0j/R0o08f56PGYX/sr2H7yRp11LB4nLCbbbxV7HhmLNriT1ObyF5lZynDw
# N7+YAN8gFk8n+2BnFqFmut1VwDophrCYoCvtlUG3OtUVmDG0YgkPCr2B2RP+v6TR
# 81fZvAT6gt4y3wSJ8ADNXcL50CN/AAvkdgIm2fBldkKmKYcJRyvmfxqkhQ/8mJb2
# VVQrH4D6wPIOK+XW+6kvRBVK5xMOHds3OBqhK/bt1nz8MIIGsDCCBJigAwIBAgIQ
# CK1AsmDSnEyfXs2pvZOu2TANBgkqhkiG9w0BAQwFADBiMQswCQYDVQQGEwJVUzEV
# MBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3d3cuZGlnaWNlcnQuY29t
# MSEwHwYDVQQDExhEaWdpQ2VydCBUcnVzdGVkIFJvb3QgRzQwHhcNMjEwNDI5MDAw
# MDAwWhcNMzYwNDI4MjM1OTU5WjBpMQswCQYDVQQGEwJVUzEXMBUGA1UEChMORGln
# aUNlcnQsIEluYy4xQTA/BgNVBAMTOERpZ2lDZXJ0IFRydXN0ZWQgRzQgQ29kZSBT
# aWduaW5nIFJTQTQwOTYgU0hBMzg0IDIwMjEgQ0ExMIICIjANBgkqhkiG9w0BAQEF
# AAOCAg8AMIICCgKCAgEA1bQvQtAorXi3XdU5WRuxiEL1M4zrPYGXcMW7xIUmMJ+k
# jmjYXPXrNCQH4UtP03hD9BfXHtr50tVnGlJPDqFX/IiZwZHMgQM+TXAkZLON4gh9
# NH1MgFcSa0OamfLFOx/y78tHWhOmTLMBICXzENOLsvsI8IrgnQnAZaf6mIBJNYc9
# URnokCF4RS6hnyzhGMIazMXuk0lwQjKP+8bqHPNlaJGiTUyCEUhSaN4QvRRXXegY
# E2XFf7JPhSxIpFaENdb5LpyqABXRN/4aBpTCfMjqGzLmysL0p6MDDnSlrzm2q2AS
# 4+jWufcx4dyt5Big2MEjR0ezoQ9uo6ttmAaDG7dqZy3SvUQakhCBj7A7CdfHmzJa
# wv9qYFSLScGT7eG0XOBv6yb5jNWy+TgQ5urOkfW+0/tvk2E0XLyTRSiDNipmKF+w
# c86LJiUGsoPUXPYVGUztYuBeM/Lo6OwKp7ADK5GyNnm+960IHnWmZcy740hQ83eR
# Gv7bUKJGyGFYmPV8AhY8gyitOYbs1LcNU9D4R+Z1MI3sMJN2FKZbS110YU0/EpF2
# 3r9Yy3IQKUHw1cVtJnZoEUETWJrcJisB9IlNWdt4z4FKPkBHX8mBUHOFECMhWWCK
# ZFTBzCEa6DgZfGYczXg4RTCZT/9jT0y7qg0IU0F8WD1Hs/q27IwyCQLMbDwMVhEC
# AwEAAaOCAVkwggFVMBIGA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0OBBYEFGg34Ou2
# O/hfEYb7/mF7CIhl9E5CMB8GA1UdIwQYMBaAFOzX44LScV1kTN8uZz/nupiuHA9P
# MA4GA1UdDwEB/wQEAwIBhjATBgNVHSUEDDAKBggrBgEFBQcDAzB3BggrBgEFBQcB
# AQRrMGkwJAYIKwYBBQUHMAGGGGh0dHA6Ly9vY3NwLmRpZ2ljZXJ0LmNvbTBBBggr
# BgEFBQcwAoY1aHR0cDovL2NhY2VydHMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0VHJ1
# c3RlZFJvb3RHNC5jcnQwQwYDVR0fBDwwOjA4oDagNIYyaHR0cDovL2NybDMuZGln
# aWNlcnQuY29tL0RpZ2lDZXJ0VHJ1c3RlZFJvb3RHNC5jcmwwHAYDVR0gBBUwEzAH
# BgVngQwBAzAIBgZngQwBBAEwDQYJKoZIhvcNAQEMBQADggIBADojRD2NCHbuj7w6
# mdNW4AIapfhINPMstuZ0ZveUcrEAyq9sMCcTEp6QRJ9L/Z6jfCbVN7w6XUhtldU/
# SfQnuxaBRVD9nL22heB2fjdxyyL3WqqQz/WTauPrINHVUHmImoqKwba9oUgYftzY
# gBoRGRjNYZmBVvbJ43bnxOQbX0P4PpT/djk9ntSZz0rdKOtfJqGVWEjVGv7XJz/9
# kNF2ht0csGBc8w2o7uCJob054ThO2m67Np375SFTWsPK6Wrxoj7bQ7gzyE84FJKZ
# 9d3OVG3ZXQIUH0AzfAPilbLCIXVzUstG2MQ0HKKlS43Nb3Y3LIU/Gs4m6Ri+kAew
# Q3+ViCCCcPDMyu/9KTVcH4k4Vfc3iosJocsL6TEa/y4ZXDlx4b6cpwoG1iZnt5Lm
# Tl/eeqxJzy6kdJKt2zyknIYf48FWGysj/4+16oh7cGvmoLr9Oj9FpsToFpFSi0HA
# SIRLlk2rREDjjfAVKM7t8RhWByovEMQMCGQ8M4+uKIw8y4+ICw2/O/TOHnuO77Xr
# y7fwdxPm5yg/rBKupS8ibEH5glwVZsxsDsrFhsP2JjMMB0ug0wcCampAMEhLNKhR
# ILutG4UI4lkNbcoFUCvqShyepf2gpx8GdOfy1lKQ/a+FSCH5Vzu0nAPthkX0tGFu
# v2jiJmCG6sivqf6UHedjGzqGVnhOMIIGwjCCBKqgAwIBAgIQBUSv85SdCDmmv9s/
# X+VhFjANBgkqhkiG9w0BAQsFADBjMQswCQYDVQQGEwJVUzEXMBUGA1UEChMORGln
# aUNlcnQsIEluYy4xOzA5BgNVBAMTMkRpZ2lDZXJ0IFRydXN0ZWQgRzQgUlNBNDA5
# NiBTSEEyNTYgVGltZVN0YW1waW5nIENBMB4XDTIzMDcxNDAwMDAwMFoXDTM0MTAx
# MzIzNTk1OVowSDELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDkRpZ2lDZXJ0LCBJbmMu
# MSAwHgYDVQQDExdEaWdpQ2VydCBUaW1lc3RhbXAgMjAyMzCCAiIwDQYJKoZIhvcN
# AQEBBQADggIPADCCAgoCggIBAKNTRYcdg45brD5UsyPgz5/X5dLnXaEOCdwvSKOX
# ejsqnGfcYhVYwamTEafNqrJq3RApih5iY2nTWJw1cb86l+uUUI8cIOrHmjsvlmbj
# aedp/lvD1isgHMGXlLSlUIHyz8sHpjBoyoNC2vx/CSSUpIIa2mq62DvKXd4ZGIX7
# ReoNYWyd/nFexAaaPPDFLnkPG2ZS48jWPl/aQ9OE9dDH9kgtXkV1lnX+3RChG4PB
# uOZSlbVH13gpOWvgeFmX40QrStWVzu8IF+qCZE3/I+PKhu60pCFkcOvV5aDaY7Mu
# 6QXuqvYk9R28mxyyt1/f8O52fTGZZUdVnUokL6wrl76f5P17cz4y7lI0+9S769Sg
# LDSb495uZBkHNwGRDxy1Uc2qTGaDiGhiu7xBG3gZbeTZD+BYQfvYsSzhUa+0rRUG
# FOpiCBPTaR58ZE2dD9/O0V6MqqtQFcmzyrzXxDtoRKOlO0L9c33u3Qr/eTQQfqZc
# ClhMAD6FaXXHg2TWdc2PEnZWpST618RrIbroHzSYLzrqawGw9/sqhux7UjipmAmh
# cbJsca8+uG+W1eEQE/5hRwqM/vC2x9XH3mwk8L9CgsqgcT2ckpMEtGlwJw1Pt7U2
# 0clfCKRwo+wK8REuZODLIivK8SgTIUlRfgZm0zu++uuRONhRB8qUt+JQofM604qD
# y0B7AgMBAAGjggGLMIIBhzAOBgNVHQ8BAf8EBAMCB4AwDAYDVR0TAQH/BAIwADAW
# BgNVHSUBAf8EDDAKBggrBgEFBQcDCDAgBgNVHSAEGTAXMAgGBmeBDAEEAjALBglg
# hkgBhv1sBwEwHwYDVR0jBBgwFoAUuhbZbU2FL3MpdpovdYxqII+eyG8wHQYDVR0O
# BBYEFKW27xPn783QZKHVVqllMaPe1eNJMFoGA1UdHwRTMFEwT6BNoEuGSWh0dHA6
# Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRHNFJTQTQwOTZTSEEy
# NTZUaW1lU3RhbXBpbmdDQS5jcmwwgZAGCCsGAQUFBwEBBIGDMIGAMCQGCCsGAQUF
# BzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wWAYIKwYBBQUHMAKGTGh0dHA6
# Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRHNFJTQTQwOTZT
# SEEyNTZUaW1lU3RhbXBpbmdDQS5jcnQwDQYJKoZIhvcNAQELBQADggIBAIEa1t6g
# qbWYF7xwjU+KPGic2CX/yyzkzepdIpLsjCICqbjPgKjZ5+PF7SaCinEvGN1Ott5s
# 1+FgnCvt7T1IjrhrunxdvcJhN2hJd6PrkKoS1yeF844ektrCQDifXcigLiV4JZ0q
# BXqEKZi2V3mP2yZWK7Dzp703DNiYdk9WuVLCtp04qYHnbUFcjGnRuSvExnvPnPp4
# 4pMadqJpddNQ5EQSviANnqlE0PjlSXcIWiHFtM+YlRpUurm8wWkZus8W8oM3NG6w
# QSbd3lqXTzON1I13fXVFoaVYJmoDRd7ZULVQjK9WvUzF4UbFKNOt50MAcN7MmJ4Z
# iQPq1JE3701S88lgIcRWR+3aEUuMMsOI5ljitts++V+wQtaP4xeR0arAVeOGv6wn
# LEHQmjNKqDbUuXKWfpd5OEhfysLcPTLfddY2Z1qJ+Panx+VPNTwAvb6cKmx5Adza
# ROY63jg7B145WPR8czFVoIARyxQMfq68/qTreWWqaNYiyjvrmoI1VygWy2nyMpqy
# 0tg6uLFGhmu6F/3Ed2wVbK6rr3M66ElGt9V/zLY4wNjsHPW2obhDLN9OTH0eaHDA
# dwrUAuBcYLso/zjlUlrWrBciI0707NMX+1Br/wd3H3GXREHJuEbTbDJ8WC9nR2Xl
# G3O2mflrLAZG70Ee8PBf4NvZrZCARK+AEEGKMIIHVjCCBT6gAwIBAgIQDDoJVxfW
# FyISC6r4ZQDp8TANBgkqhkiG9w0BAQsFADBpMQswCQYDVQQGEwJVUzEXMBUGA1UE
# ChMORGlnaUNlcnQsIEluYy4xQTA/BgNVBAMTOERpZ2lDZXJ0IFRydXN0ZWQgRzQg
# Q29kZSBTaWduaW5nIFJTQTQwOTYgU0hBMzg0IDIwMjEgQ0ExMB4XDTI0MDIwNzAw
# MDAwMFoXDTI1MDIwNjIzNTk1OVowXjELMAkGA1UEBhMCVVMxFzAVBgNVBAgTDk5v
# cnRoIENhcm9saW5hMRQwEgYDVQQHEwtNb3JyaXN2aWxsZTEPMA0GA1UEChMGTGVu
# b3ZvMQ8wDQYDVQQDEwZMZW5vdm8wggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIK
# AoICAQCJ/2wEEjI2Fith3vWY9xlzKNcMQm2Rhc+o8R/n4aYVN4esXj1Fq+n+HX6Y
# HPuD8N8cDNxwgCqWYSplQji41PYoYLypV+AtahYvzyD33Z6Qv4cRXDIwZKbzbOgl
# kE4CT0PolwzEvvuOsubro9oPKZVBZny46CVdq9wyplH0KDvbhBHqfT4OPqDo7cCd
# uBoSHHfe1fInaETldz8KF3fN4yt97OS1lm+2b7sIDEOxSwNpBvARtUY2B/Hw0v7u
# YTm32psDPhT/ViLnyDz+//ltD/5TMBk5hG93r/tA4fN7WxmjXozLge37OcEkIQVe
# cSUFU74Ds+zx7MySAXOzS2cScfVsjI6dsEXr3Y2TsrbU6MNJ73bEnnTnrlC80zm4
# f28ztOaB+utZcUkP1WW85eXwDPosH5McIGJ/PFS646UxjM736p8CxQ2ugxwqlJTs
# DOFnoww2gOEsGCqghaiZwhcjbmS1kP36ezL4buYPtySdViBjrkhcHgeuQimSb27g
# Af8Po/syqzZHhk2Yu8433CxH8syVXasB3g5XYUrzgVfoMwXs8TU27hjZTSlW5qLh
# ycNQ2bIzGZOGSXdJtx9waqJOShlRQdAnnjpUo3c/VQYHAMgtDGZws39S3w9WpaRr
# t7aKeAnb3lToRBOPDJgaE9IwsDoKt7u8zMB5lulJIymWhoECBwIDAQABo4ICAzCC
# Af8wHwYDVR0jBBgwFoAUaDfg67Y7+F8Rhvv+YXsIiGX0TkIwHQYDVR0OBBYEFNXN
# bjmeamzHeoCP13Pmbf7yfwReMD4GA1UdIAQ3MDUwMwYGZ4EMAQQBMCkwJwYIKwYB
# BQUHAgEWG2h0dHA6Ly93d3cuZGlnaWNlcnQuY29tL0NQUzAOBgNVHQ8BAf8EBAMC
# B4AwEwYDVR0lBAwwCgYIKwYBBQUHAwMwgbUGA1UdHwSBrTCBqjBToFGgT4ZNaHR0
# cDovL2NybDMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0VHJ1c3RlZEc0Q29kZVNpZ25p
# bmdSU0E0MDk2U0hBMzg0MjAyMUNBMS5jcmwwU6BRoE+GTWh0dHA6Ly9jcmw0LmRp
# Z2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRHNENvZGVTaWduaW5nUlNBNDA5NlNI
# QTM4NDIwMjFDQTEuY3JsMIGUBggrBgEFBQcBAQSBhzCBhDAkBggrBgEFBQcwAYYY
# aHR0cDovL29jc3AuZGlnaWNlcnQuY29tMFwGCCsGAQUFBzAChlBodHRwOi8vY2Fj
# ZXJ0cy5kaWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkRzRDb2RlU2lnbmluZ1JT
# QTQwOTZTSEEzODQyMDIxQ0ExLmNydDAJBgNVHRMEAjAAMA0GCSqGSIb3DQEBCwUA
# A4ICAQCl35iBbcmzr6+4HRgJBHAZMDkpxHjLnKdcosGX6culcNp+4Oq8sOHIydS2
# ZOCwJ0pxRffgaaGpKmlc3v2myw+7pj0ztiUGfsvS3zS0fFeIk6D9izlwFKaCb5/E
# kWlgvp4Thvt85GiRZDI1zcY7hXN+Gz0h+T0tRz3vLJ2lMf4L+I07W+QjoeyMmbKk
# bCoLdPvUjEk5871V+spp0AQH4LNQuSfAxAwXwYhq5B9eA+iUOk1qdvwcwaRMUG1i
# C/ivPN/XaWjfMYUn9MXivkUJnwGfThb8tU6BxvfHJnesigYT5LsZTYTLgsbN9bfk
# 3x8ccSCzxJAZberP9hTRm7PW0+dBzEv3KWxUwuhmuIdRsiXjDy2KLCksAi06ARRk
# cul7phrRaU1GuYg75xMLP+CQ7AfyIJN6kOj5aSEQblBPmQVR6W04WxQPjJRDd7pe
# yVKe3QLVYVeTPR9D8C8herfj2KX19q5xTG9GrzUyoMVEpiisr8q6O/Gp+rTHJ60O
# kenwjrkKDlnudfP4MlZsTTSe8JFxdQlWCbotp25OdJP4Dy7sLKGrGZvkhAbWDsjr
# u6KHWCLncbNc7mWdFHC1cLh7jXqaYEgppOsf11E0wQtVkO/G/7JWn2fyEGfN6u0q
# jFZRkNz4YJm/H/UmnjEKn9xj/iPiJW4Ou+F2q7ISN60HbYB6qTGCBlMwggZPAgEB
# MH0waTELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYD
# VQQDEzhEaWdpQ2VydCBUcnVzdGVkIEc0IENvZGUgU2lnbmluZyBSU0E0MDk2IFNI
# QTM4NCAyMDIxIENBMQIQDDoJVxfWFyISC6r4ZQDp8TANBglghkgBZQMEAgEFAKCB
# hDAYBgorBgEEAYI3AgEMMQowCKACgAChAoAAMBkGCSqGSIb3DQEJAzEMBgorBgEE
# AYI3AgEEMBwGCisGAQQBgjcCAQsxDjAMBgorBgEEAYI3AgEVMC8GCSqGSIb3DQEJ
# BDEiBCCwJIP0VkpIz7QPJ532X/zVm5gKkB/bvokY/XIIqPlSKjANBgkqhkiG9w0B
# AQEFAASCAgB0zRIXAppL16fSnyMVqbf5CjhLlYn03tvIgmH6mBBAvwM6GUsUtovt
# Zh2YN5A4oUYIWvDJI3n1grDob5dJqfayfnxAlOnoEDlYqGKhbOo4ormLm/Xttli5
# HStaaBQ96bZe4UicUb5zowGR+yMyNAVrZGjJSDBHl+n2t7I7WbLsEzXpnkZGPGXX
# oa7E+8Xwmvuceusy+PCi56mTxWsGgMTrK4FjdMA1RIrmUFblg46Rf9c25pMrsrfW
# OQpcKAhRssDu3jxTyxeOtVSr9ZTzjnXFxDBxMosB0/snn6dzWoENoXA+JihfZA6+
# QK63W49oNy2zRytGExqGsg09mPK0aAqrlc0IhpHV+3I4neXypYAcoV7NWMt5MYdV
# ChIIYKvN5Fro+/FwLwIcp+//CzHMNoI5cweaZyxbz4CLpTtgw7hLtcnosRcP6nYB
# H6xV1D6id3m+MDjU+aOARxYlW4LFmjQx2GBiBKYZRDRCzhk/BP0Jgf9Ke59Qz1On
# AKxzU7Et3Hx7Wyw8dpn74rf/y1lWNH4X3KvTsXaZLVSinQdeUueblGh1CQJsTdKR
# /xpVRNJKpNyW6xExwetpn76r5+kJ/VtNY9dsHim/Q4SslX6g1IXeHalz3Absy12r
# WdQmtfhjyTnVG90Cfx9ax2pVl8l1pJe6kRKywJ37fPY3VR2nsBQeHqGCAyAwggMc
# BgkqhkiG9w0BCQYxggMNMIIDCQIBATB3MGMxCzAJBgNVBAYTAlVTMRcwFQYDVQQK
# Ew5EaWdpQ2VydCwgSW5jLjE7MDkGA1UEAxMyRGlnaUNlcnQgVHJ1c3RlZCBHNCBS
# U0E0MDk2IFNIQTI1NiBUaW1lU3RhbXBpbmcgQ0ECEAVEr/OUnQg5pr/bP1/lYRYw
# DQYJYIZIAWUDBAIBBQCgaTAYBgkqhkiG9w0BCQMxCwYJKoZIhvcNAQcBMBwGCSqG
# SIb3DQEJBTEPFw0yNDA3MTUwNjIyNTlaMC8GCSqGSIb3DQEJBDEiBCAMKQgGyOy1
# 0O8SqVe1HotbYLEmvcDAS6Ru9VQteh6JZjANBgkqhkiG9w0BAQEFAASCAgArDHSs
# X2yxOmCZA+x5aP4BTzyYspT1Hh0Ys8kbm6aq5xYXnGx/84A10tk9+OJIMPzPajDC
# gyoQpwDqCnul+GN1Zl10vU/jaPRZDqgaTpHwez0S0AwREOVN6OaabPZEk+b20Xbf
# X/Y8QEu9wC2n7p1ECMdebUg/MrfUpxxcDq3I0yOUW5xmI3Q/MfEx2E43mBbwaxz/
# pSEPlxdyMHhJBJwdHlWydFo7d8Mb04WAzAqx9Ogk/MvwHOXg0L1h/u0bYaMPhhq1
# mtwCpAG8XqqIgo1oSwUlnJVrUmXjMEvyUu9Tb41NS+lPXX9HCVq+AAdSOiWHPE2P
# KtC/fwue6aGGsvKBbktW3sgXEI7H4dC6bP8ksd9yOUv/X49zpK4s2WLciuydQNKV
# khp1aoHWI1SglHKi/A6CbvBb/nw9jJRsOPdE/qP0v9INitmRo4JrBRamTswl/5v0
# Nlk4gbyxQ59wagH3nVvyC4f/a8oVKZ6iQCKDww+/KFLYjoVRuuqS8FCnw9z7do+7
# N1dlIKStsyTR2OFf1ZMWi69sl6k/MDjV7vb+4PjQgAWJw/FKoYmC2QETB6f8Wp1p
# ztt2VkVekZp2a/feCM6sTaCk0nFI4igHABrkU0VipDDMYKE+7SY302mzFLkHtAi1
# eiELFmV4n7M4pWWcaidC3NtN5J0Yb5ho4E+Apw==
# SIG # End signature block
