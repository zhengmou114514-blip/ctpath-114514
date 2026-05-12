param(
  [string]$DocPath = 'C:\Users\挣谋\Downloads\毕设论文-修订版.doc'
)

$ErrorActionPreference = 'Stop'

function Normalize-Text {
  param([string]$Text)
  if ($null -eq $Text) { return '' }
  return $Text.Replace("`r", '').Replace([string][char]7, '').Trim()
}

function Set-ParagraphText {
  param(
    $Paragraph,
    [string]$NewText
  )
  $Paragraph.Range.Text = $NewText + "`r"
}

function Try-SetStyle {
  param(
    $Paragraph,
    [string]$StyleName
  )
  try {
    $Paragraph.Range.Style = $StyleName
    return $true
  }
  catch {
    return $false
  }
}

if (-not (Test-Path -LiteralPath $DocPath)) {
  throw "Document not found: $DocPath"
}

$backupPath = [System.IO.Path]::Combine(
  [System.IO.Path]::GetDirectoryName($DocPath),
  ([System.IO.Path]::GetFileNameWithoutExtension($DocPath) + '_自动修改前备份' + [System.IO.Path]::GetExtension($DocPath))
)
Copy-Item -LiteralPath $DocPath -Destination $backupPath -Force

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

$replaceMap = @{
  '5.2.1 登录与注册运行效果' = '5.2.1 登录与权限控制运行效果'
  '表5.1系统测试环境表' = '表5.1 系统测试环境表'
  '表5.2认证与角色权限功能测试用例' = '表5.2 认证与角色权限功能测试用例'
  '表5.4药事、模型与治理功能测试用例' = '表5.4 药事、模型与治理功能测试用例'
  '图4.3 核心数据ER图' = '图4.9 核心数据ER图'
  '图4.4 系统核心业务流程图' = '图4.10 系统核心交互架构图'
  '表4.3 医生用户表 doctor_users' = '表4.1 医生用户表 doctor_users'
  '表4.4 患者主档案表 patients' = '表4.2 患者主档案表 patients'
  '表4.5 病程事件表 patient_events' = '表4.3 病程事件表 patient_events'
  '表4.6 随访任务表 outpatient_tasks' = '表4.4 随访任务表 outpatient_tasks'
  '表4.7 药品目录表 drug_catalog' = '表4.5 药品目录表 drug_catalog'
  '表4.8 预测结果表 prediction_results' = '表4.6 预测结果表 prediction_results'
  '表4.9 审计日志表 system_audit_logs' = '表4.7 审计日志表 system_audit_logs'
}

$bodyReplaceMap = @{
  '系统核心业务流程如图4.10所示。' = '系统核心交互架构如图4.10所示。'
  '根据当前 MySQL 数据表结构，系统主要数据实体包括医生用户、患者主档案、病程事件、患者接诊状态、门诊与随访任务、任务处理日志、患者联系记录和患者审计日志。其中，患者主档案是核心实体，其他数据多数围绕患者展开。系统核心数据关系如图4.3所示。' = '根据当前 MySQL 数据表结构，系统主要数据实体包括医生用户、患者主档案、病程事件、患者接诊状态、门诊与随访任务、任务处理日志、患者联系记录和患者审计日志。其中，患者主档案是核心实体，其他数据多数围绕患者展开。系统核心数据关系如图4.9所示。'
  '由图4.3可以看出，系统数据库以患者主档案为中心，将病程事件、接诊状态、随访任务、联系记录和审计日志等数据组织在患者维度下。该设计能够较好支撑患者详情、病程时间线、护士随访和操作审计等核心功能。' = '由图4.9可以看出，系统数据库以患者主档案为中心，将病程事件、接诊状态、随访任务、联系记录和审计日志等数据组织在患者维度下。该设计能够较好支撑患者详情、病程时间线、护士随访和操作审计等核心功能。'
  '为了避免数据库设计部分过于冗长，本文选取与系统核心业务关系最密切的数据表进行说明，主要包括医生用户表、患者主档案表、病程事件表、随访任务表、药品目录表、预测结果表和审计日志表。核心数据表结构如表4.3至表4.9所示。' = '为了避免数据库设计部分过于冗长，本文选取与系统核心业务关系最密切的数据表进行说明，主要包括医生用户表、患者主档案表、病程事件表、随访任务表、药品目录表、预测结果表和审计日志表。核心数据表结构如表4.1至表4.7所示。'
  '医生用户表用于保存系统用户的登录账号、基本身份信息和角色信息，是系统身份认证和权限控制的基础，其结构如表4.3所示。' = '医生用户表用于保存系统用户的登录账号、基本身份信息和角色信息，是系统身份认证和权限控制的基础，其结构如表4.1所示。'
  '患者主档案表是系统数据库设计中的核心表，主要用于保存患者基础资料、诊疗摘要、风险等级和档案状态等信息，其结构如表4.4所示。' = '患者主档案表是系统数据库设计中的核心表，主要用于保存患者基础资料、诊疗摘要、风险等级和档案状态等信息，其结构如表4.2所示。'
  '病程事件表用于保存患者在不同时间点产生的诊疗、检查、用药、随访等事件信息，是病程时间线展示和模型辅助分析的重要数据来源，其结构如表4.5所示。' = '病程事件表用于保存患者在不同时间点产生的诊疗、检查、用药、随访等事件信息，是病程时间线展示和模型辅助分析的重要数据来源，其结构如表4.3所示。'
  '随访任务表用于记录慢病患者的随访任务信息，包括任务类别、负责人、截止日期、优先级和处理状态等内容，其结构如表4.6所示。' = '随访任务表用于记录慢病患者的随访任务信息，包括任务类别、负责人、截止日期、优先级和处理状态等内容，其结构如表4.4所示。'
  '药品目录表用于保存系统中的药品基础信息，包括通用名、商品名、剂型、规格、处方药标识和药品状态等内容，其结构如表4.7所示。' = '药品目录表用于保存系统中的药品基础信息，包括通用名、商品名、剂型、规格、处方药标识和药品状态等内容，其结构如表4.5所示。'
  '预测结果表用于保存模型预测输出结果和证据摘要等信息，为患者详情页和模型洞察页面提供数据支撑，其结构如表4.8所示。' = '预测结果表用于保存模型预测输出结果和证据摘要等信息，为患者详情页和模型洞察页面提供数据支撑，其结构如表4.6所示。'
  '审计日志表用于记录系统关键操作行为，包括操作结果、用户角色、请求路径、请求方法和客户端地址等信息，为系统安全追踪和问题排查提供依据，其结构如表4.9所示。' = '审计日志表用于记录系统关键操作行为，包括操作结果、用户角色、请求路径、请求方法和客户端地址等信息，为系统安全追踪和问题排查提供依据，其结构如表4.7所示。'
}

$heading2Texts = @(
  '4.2 系统功能模块设计',
  '4.3 数据库设计',
  '4.4 前后端交互与模块运行流程设计',
  '4.5 本章小结',
  '5.1 系统测试环境',
  '5.2 系统功能运行效果',
  '5.3 系统功能测试',
  '5.4 本章小结'
)

$heading3Texts = @(
  '4.2.1 用户入口模块',
  '4.2.2 临床业务模块',
  '4.2.3 随访管理模块',
  '4.2.4 药事管理模块',
  '4.2.5 模型辅助模块',
  '4.2.6 系统治理模块',
  '4.3.1 数据库概念结构设计',
  '4.3.2 核心数据表设计',
  '5.2.1 登录与权限控制运行效果',
  '5.2.2 医生工作台运行效果',
  '5.2.3 患者详情与模型辅助运行效果',
  '5.2.4 护士随访运行效果',
  '5.2.5 药品管理与药品权限运行效果',
  '5.2.6 模型看板与治理中心运行效果',
  '5.3.1 认证与角色权限测试'
)

try {
  $doc = $word.Documents.Open($DocPath)

  for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
    $paragraph = $doc.Paragraphs.Item($i)
    $text = Normalize-Text $paragraph.Range.Text
    if ([string]::IsNullOrWhiteSpace($text)) { continue }

    $styleName = ''
    try { $styleName = [string]$paragraph.Range.Style.NameLocal } catch { try { $styleName = [string]$paragraph.Range.Style } catch {} }
    if ($styleName -like 'TOC*') { continue }

    if ($replaceMap.ContainsKey($text)) {
      Set-ParagraphText -Paragraph $paragraph -NewText $replaceMap[$text]
      $text = $replaceMap[$text]
    }

    if ($bodyReplaceMap.ContainsKey($text)) {
      Set-ParagraphText -Paragraph $paragraph -NewText $bodyReplaceMap[$text]
      $text = $bodyReplaceMap[$text]
    }

    if ($heading2Texts -contains $text) {
      [void](Try-SetStyle -Paragraph $paragraph -StyleName '标题 2')
      continue
    }

    if ($heading3Texts -contains $text) {
      [void](Try-SetStyle -Paragraph $paragraph -StyleName '标题 3')
      continue
    }

    if ($text -eq '第4章 系统设计与实现' -or $text -eq '第5章 系统实现与测试' -or $text -eq '参考文献' -or $text -eq '致谢') {
      [void](Try-SetStyle -Paragraph $paragraph -StyleName '标题 1')
    }
  }

  for ($i = 1; $i -lt $doc.Paragraphs.Count; $i++) {
    $paragraph = $doc.Paragraphs.Item($i)
    $text = Normalize-Text $paragraph.Range.Text
    if ($text -eq '第4章 系统设计与实现' -or $text -eq '第5章 系统实现与测试') {
      [void](Try-SetStyle -Paragraph $paragraph -StyleName '标题 1')
      $next = $doc.Paragraphs.Item($i + 1)
      $nextText = Normalize-Text $next.Range.Text
      if ($nextText.StartsWith('本章在')) {
        [void](Try-SetStyle -Paragraph $next -StyleName '正文')
      }
    }
  }

  for ($i = 1; $i -lt $doc.Paragraphs.Count; $i++) {
    $paragraph = $doc.Paragraphs.Item($i)
    $text = Normalize-Text $paragraph.Range.Text
    if ($text -eq '如图5.1所示，登录页面主要包括账号输入、密码输入和登录按钮。用户登录成功后，系统会保存用户身份状态，并根据角色信息进入相应页面。该功能为后续患者信息查看、随访任务处理、药品维护和系统治理等操作提供了身份认证基础。') {
      $next = $doc.Paragraphs.Item($i + 1)
      if ([string]::IsNullOrWhiteSpace((Normalize-Text $next.Range.Text))) {
        Set-ParagraphText -Paragraph $next -NewText '图5.1 系统登录界面'
        [void](Try-SetStyle -Paragraph $next -StyleName '正文')
      }
    }
    if ($text -eq '如图5.2所示，医生工作台将患者列表和摘要信息集中展示，便于医生快速定位重点患者。通过该页面，医生可以进入患者详情、查看风险提示或进一步查看模型辅助分析结果，从而提高慢病诊疗过程中的信息获取效率。') {
      $next = $doc.Paragraphs.Item($i + 1)
      if ([string]::IsNullOrWhiteSpace((Normalize-Text $next.Range.Text))) {
        Set-ParagraphText -Paragraph $next -NewText '图5.2 医生工作台运行效果图'
        [void](Try-SetStyle -Paragraph $next -StyleName '正文')
      }
    }
    if ($text -like '【此处插入图5.*】') {
      Set-ParagraphText -Paragraph $paragraph -NewText ''
    }
  }

  $deleteStart = $null
  for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
    $paragraph = $doc.Paragraphs.Item($i)
    $text = Normalize-Text $paragraph.Range.Text
    if ($text -like '致谢二字一级标题*') {
      $deleteStart = $paragraph.Range.Start
      break
    }
  }

  if ($null -ne $deleteStart) {
    $deleteRange = $doc.Range($deleteStart, $doc.Content.End)
    $deleteRange.Delete()
  }

  foreach ($toc in $doc.TablesOfContents) {
    $toc.Update()
  }
  foreach ($table in $doc.TablesOfFigures) {
    $table.Update()
  }
  $doc.Fields.Update() | Out-Null

  $doc.Save()
  $doc.Close()
  Write-Output "updated=$DocPath"
  Write-Output "backup=$backupPath"
}
finally {
  if ($doc) {
    try { $doc.Close($false) } catch {}
  }
  $word.Quit()
}
