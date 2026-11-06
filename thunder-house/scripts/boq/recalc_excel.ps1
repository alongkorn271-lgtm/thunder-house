param([string]$Path)
# Open the workbook in Excel, recalculate, save (so cached values exist), and list any error cells.
$x = New-Object -ComObject Excel.Application
$x.Visible = $false; $x.DisplayAlerts = $false
try {
  $wb = $x.Workbooks.Open($Path)
  $x.CalculateFull()
  $errs = @(); $nf = 0
  foreach ($ws in $wb.Worksheets) {
    $ur = $ws.UsedRange
    foreach ($c in $ur.Cells) {
      if ($c.HasFormula) {
        $nf++
        if ($c.Text -match '^#') { $errs += "$($ws.Name)!$($c.Address(0,0)) $($c.Text) $($c.Formula)" }
      }
    }
  }
  $wb.Save()
  "formulas: $nf  errors: $($errs.Count)"
  $errs
  $s = $wb.Worksheets.Item("สรุป")
  foreach ($r in 4..11) { "{0} = {1}" -f $s.Cells.Item($r,1).Text, $s.Cells.Item($r,2).Text }
  $n = $wb.Worksheets.Item("ต่อรอง")
  foreach ($r in 5..24) { "{0} | {1} | {2}" -f $n.Cells.Item($r,1).Text, $n.Cells.Item($r,9).Text, $n.Cells.Item($r,11).Text }
  $wb.Close($true)
} finally { $x.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($x) }
