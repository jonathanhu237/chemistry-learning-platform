export const showcaseSlides = [
  {
    no: 14,
    layout: "chapter",
    section: "03 应用展示",
    title: "应用展示"
  },
  {
    no: 15,
    layout: "resourceShowcase",
    section: "03 应用展示",
    title: "海量实验数据管理与展示",
    lead: "后台按章节集中维护实验目录、点位资料、视频资源和题库覆盖；学生移动端首页直接呈现已发布实验视频，形成“资源管理—移动学习入口”的展示链路。",
    teacherImage: "/slide-assets/showcase-teacher-experiment-management.png",
    teacherCaption: "后台：按章节维护实验目录、点位资料、视频与题库覆盖",
    studentImage: "/slide-assets/showcase-student-home.png",
    studentCaption: "学生端：首页实验视频入口",
    notes: [
      ["统一管理", "后台把实验目录、点位原理、现象说明、安全提示和视频绑定集中到同一工作台。"],
      ["移动展示", "学生首页直接呈现实验视频入口，海量资源可以按实验、试剂、现象或点位名称检索。"]
    ]
  },
  {
    no: 16,
    layout: "studentLearningShowcase",
    section: "03 应用展示",
    title: "个性化学习推荐路径",
    lead: "学生进入学习章节后，系统优先推荐薄弱点位；打开推荐内容即可学习视频、原理、现象与安全提示。",
    images: [
      ["进入学习", "/slide-assets/showcase-student-learning-entry.png", "学生从元素周期表学习入口选择元素族与实验章节。"],
      ["推荐内容", "/slide-assets/showcase-student-learning-recommendation.png", "系统在章节目录中优先呈现推荐学习点位。"],
      ["知识学习", "/slide-assets/showcase-student-learning-knowledge.png", "进入点位后学习视频、实验原理、现象解释与安全提示。"]
    ],
    steps: [
      ["01", "学习入口", "学生进入学习界面，从元素周期表和章节目录定位当前学习范围。"],
      ["02", "推荐点位", "系统把薄弱或未充分学习的实验点位前置，减少学生自行筛选成本。"],
      ["03", "进入学习", "学生打开推荐内容后，围绕视频、原理、现象和安全提示完成知识学习。"]
    ],
    summary: "学习推荐把“进入学习界面—发现推荐内容—进入知识单元学习”串成可执行路径，为后续测评和学习报告提供学习证据。"
  },
  {
    no: 17,
    layout: "resourceShowcase",
    section: "03 应用展示",
    title: "智能组卷与定制化训练",
    lead: "教师在后台按班级调整组卷参数，控制题量、未测点位比例和薄弱点位倾向；学生在前台依据自身掌握度选择智能薄弱项测试或自选范围训练。",
    teacherImage: "/slide-assets/showcase-teacher-smart-strategy.png",
    teacherCaption: "教师端：按班级调整题量、未测点位比例、薄弱点位倾向和单实验题数",
    studentImage: "/slide-assets/showcase-student-smart-assessment.png",
    studentCaption: "学生端：按掌握度发起智能薄弱项训练，也可自选实验范围",
    notes: [
      ["后台调参", "教师可以按班级配置组卷策略，让系统更偏向薄弱点位、未测点位或指定题量。"],
      ["定制训练", "学生根据个人掌握度发起智能训练，也能按实验范围进行自选、随机或全范围练习。"]
    ]
  },
  {
    no: 18,
    layout: "resourceShowcase",
    section: "03 应用展示",
    title: "AI 学习报告生成",
    lead: "教师在后台维护报告总结和错题讲解 Prompt，配置可插入的学生、测评、得分、错题与掌握度变量；学生完成测评后进入报告页，看到 AI 学情总结、下一步复习建议和错题解析。",
    teacherImage: "/slide-assets/showcase-teacher-ai-report-prompt.png",
    teacherCaption: "教师端：维护报告总结 Prompt 与错题讲解 Prompt",
    studentImage: "/slide-assets/showcase-student-ai-report.png",
    studentCaption: "学生端：测评完成后查看 AI 学情总结与错题解析",
    notes: [
      ["Prompt 控制", "教师在后台定义报告总结和错题讲解的输出边界，并通过变量绑定学生、成绩、错题和掌握度变化。"],
      ["测后反馈", "学生提交测评后获得可读的学习报告，把得分、错题解析和下一步复习建议落到个人学习闭环。"]
    ]
  },
  {
    no: 19,
    layout: "resourceShowcase",
    section: "03 应用展示",
    title: "AI 答疑",
    lead: "教师在后台统一配置大语言模型，学生围绕实验知识单元发起课程内提问；系统结合点位上下文、实验现象、原理说明和安全边界，给出可追问的学习答疑。",
    teacherImage: "/slide-assets/showcase-teacher-ai-assistant-config.png",
    teacherCaption: "教师端：配置 AI 出题、AI 报告和学生答疑使用的大语言模型",
    studentImage: "/slide-assets/showcase-student-ai-assistant.png",
    studentCaption: "学生端：围绕当前知识单元进行课程内问答",
    notes: [
      ["统一配置", "后台统一维护模型接口、模型名称和密钥，支撑出题、报告和学生答疑等 AI 能力。"],
      ["课程内答疑", "学生问题绑定到实验点位与课程资料，回答聚焦原理解释、现象判断和安全提示。"]
    ]
  },
  {
    no: 20,
    layout: "questionShowcase",
    section: "03 应用展示",
    title: "大语言模型辅助出题",
    lead: "教师先选择实验点位和题型要求，系统基于点位原理、现象和安全资料生成候选题；候选题需教师审核后才能进入题库。",
    image: "/slide-assets/showcase-teacher-ai-question.png",
    notes: [
      ["点位绑定", "题目生成前先选择具体实验点位，保证题干、答案和解析都能回到知识单元。"],
      ["教师约束", "教师可限定题型、数量和命题要求，LLM 只负责生成可审核初稿。"],
      ["审核入库", "右侧展示待审题目与解析，教师确认后才发布到正式题库。"]
    ]
  }
];
