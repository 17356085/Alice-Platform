/**
 * ExamFlow — 培训考试完整业务流程编排
 *
 * 封装小程序最复杂的业务链路:
 *   培训首页 → 考试列表 → 点击开始考试 → 确认弹窗 →
 *   答题（逐题选择答案） → 提交 → 查看成绩 → 错题回顾
 *
 * 用法:
 *   const flow = new ExamFlow(app);
 *   await flow.loginAndGoToExam(credentials);
 *   const result = await flow.completeExam({ answerCount: 5 });
 */

const { LoginPage } = require('../pages/login.page');
const { StudyPage } = require('../pages/study.page');
const { ExamListPage, AnswerPage, ExamResultPage } = require('../pages/exam.page');
const { logger } = require('../utils/logger');
const { sleep } = require('../utils/helpers');

class ExamFlow {
  /**
   * @param {import('miniprogram-automator').MiniProgram} app
   */
  constructor(app) {
    this.app = app;
  }

  /**
   * 完整的考试流程（从已登录状态开始）
   *   1. 导航到考试列表
   *   2. 找到一个可用考试
   *   3. 开始考试（处理确认弹窗）
   *   4. 逐题作答
   *   5. 提交
   *   6. 获取成绩
   *
   * @param {object} opts
   * @param {number} [opts.examIndex]      考试列表索引（默认 0）
   * @param {number} [opts.answerCount]    答题数量（默认全部）
   * @param {boolean} [opts.submit]        是否提交（默认 true）
   * @returns {Promise<{score: number, isPass: boolean, wrongCount: number}>}
   */
  async fullExamCycle(opts = {}) {
    const { examIndex = 0, answerCount = 0, submit = true } = opts;

    logger.info('[ExamFlow] === 开始考试全流程 ===');

    // Step 1: 进入考试列表
    const examListPage = new ExamListPage(this.app);
    await examListPage.navigate();
    await examListPage.waitForList();
    await sleep(1000);

    const exams = await examListPage.getExamList();
    logger.info(`[ExamFlow] 考试安排数: ${exams.length}`);

    if (exams.length === 0) {
      logger.warn('[ExamFlow] 无可用考试，流程终止');
      return { score: 0, isPass: false, wrongCount: 0, skipped: true, reason: '无可用考试' };
    }

    // Step 2: 找一个可参加的考试（pending/in_progress/not_started）
    const available = exams.filter(
      e => ['pending', 'in_progress', 'not_started'].includes(e.status)
    );
    const targetExam = available.length > 0 ? available[Math.min(examIndex, available.length - 1)] : null;

    if (!targetExam) {
      logger.warn('[ExamFlow] 无可参加的考试（所有考试均已结束）');
      return { score: 0, isPass: false, wrongCount: 0, skipped: true, reason: '无可用考试' };
    }

    logger.info(`[ExamFlow] 选择考试: ${targetExam.examTitle || targetExam.examName}`);

    // Step 3: 点击考试，进入答题（处理确认弹窗）
    await examListPage.tapExam(examIndex);
    await sleep(2000);

    // 可能弹出确认窗，尝试点确认按钮
    try {
      const page = await this.app.currentPage();
      if (page) {
        const buttons = await page.$$('button');
        for (const btn of buttons) {
          try {
            const text = await btn.text();
            if (text && (text.includes('开始') || text.includes('确认') || text.includes('参加'))) {
              await btn.tap();
              logger.info('[ExamFlow] 已点击开始/确认按钮');
              break;
            }
          } catch {}
        }
      }
    } catch {}
    await sleep(2000);

    // Step 4: 答题页
    const answerPage = new AnswerPage(this.app);
    try {
      await answerPage.waitForQuestions(15000);
    } catch {
      logger.warn('[ExamFlow] 答题页加载超时，可能确认弹窗未处理');
      return { score: 0, isPass: false, wrongCount: 0, skipped: true, reason: '答题页加载失败' };
    }

    const totalQuestions = await answerPage.getQuestionCount();
    logger.info(`[ExamFlow] 题目总数: ${totalQuestions}`);
    const toAnswer = answerCount > 0 ? Math.min(answerCount, totalQuestions) : totalQuestions;

    // Step 5: 逐题作答
    for (let i = 0; i < toAnswer; i++) {
      // 选择第一个选项（A）
      await answerPage.selectOption('A');
      await sleep(300);

      if (i < toAnswer - 1) {
        await answerPage.nextQuestion();
        await sleep(500);
      }
    }
    logger.info(`[ExamFlow] 已完成 ${toAnswer}/${totalQuestions} 题`);

    // Step 6: 提交
    if (submit) {
      await answerPage.submit();
      await sleep(3000);

      // Step 7: 验证成绩页
      try {
        const resultPage = new ExamResultPage(this.app);
        await resultPage.waitForResult(10000);
        const score = await resultPage.getScore();
        const isPass = await resultPage.getIsPass();
        const wrong = await resultPage.getWrongQuestions();

        logger.info(`[ExamFlow] 成绩: ${score}, 通过: ${isPass}, 错题: ${wrong.length}`);
        return { score, isPass, wrongCount: wrong.length, skipped: false };
      } catch {
        logger.warn('[ExamFlow] 未跳转到成绩页（可能需确认弹窗）');
        return { score: 0, isPass: false, wrongCount: 0, skipped: false, reason: '成绩页未加载' };
      }
    }

    return { score: 0, isPass: false, wrongCount: 0, skipped: false };
  }

  /**
   * 从登录开始完整考试流程
   * @param {{phone:string, password:string}} credentials
   * @param {object} examOpts  — 同 fullExamCycle
   */
  async loginAndExam(credentials, examOpts = {}) {
    const { LoginFlow } = require('./LoginFlow');
    const loginFlow = new LoginFlow(this.app);
    const loginResult = await loginFlow.bypassLogin(credentials);
    if (!loginResult.success) {
      logger.warn('[ExamFlow] 登录失败，终止考试流程');
      return { score: 0, isPass: false, wrongCount: 0, skipped: true, reason: '登录失败' };
    }
    return this.fullExamCycle(examOpts);
  }
}

module.exports = { ExamFlow };
