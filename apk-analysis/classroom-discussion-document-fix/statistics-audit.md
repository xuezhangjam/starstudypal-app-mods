# 选择题全班统计可行性检查

检查对象是本次精确输入 APK 的 DEX4。未发送任何学校 HTTP / MQTT 请求；以下是客户端静态证据，不能证明服务器返回了这些模型以外的字段，也不能推定服务端授权。

1. `QuestionAskViewModel.getQuestionAskStatistic` 的原生请求包含 `classroomId` 和 `chainId`，通过原鉴权客户端访问 ApiService 的 `/tch-givelesson/v1/classroom/ask/answer_statistic`。
2. `QuestionAskStatistic` 声明 `answerList`、`answerTimeTotal`、`askNum`、`correctRate`；原生个人结果页使用这些字段。
3. `AnswerItem` 声明 `answerContent`、`answerOption`、`answerTime`、`askTitleId`、`correctAnswer`、`correctOption`、`type`。这些是题目与当前作答内容，未发现这里声明全班名单、各选项人数或每位同学的选项列表。
4. ApiService 另有 `queryAnswerRankList`，声明返回 `List<RankList>`，属于课堂排行，不能据此还原每道选择题的全班选项分布。
5. 现有提问 MQTT 处理用于开始／结束／展优等交互，未确认收到完整班级的逐人选择题答案数据。

结论：目前没有验证出可用于该学生端功能的全班选择题数据源。本轮不加入统计展示；若以后有教师正常共享的聚合统计数据或正式授权的数据接口，可据真实字段接入。排行榜和个人结果不冒充全班选择题统计。
