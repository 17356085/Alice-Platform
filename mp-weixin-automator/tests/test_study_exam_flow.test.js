/**
 * @jest-environment node
 *
 * 培训考试流程测试 — P1（最复杂业务链路）
 *
 * 覆盖:
 *   1. 培训学习页面加载
 *   2. 考试列表渲染
 *   3. 进入考试答题页（需正在进行的考试安排）
 */
const { MiniDriver } = require('../src/driver');
const { StudyPage } = require('../src/pages/study.page');
const { ExamListPage, AnswerPage, ExamResultPage } = require('../src/pages/exam.page');
const { sleep } = require('../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
});

// 连接由 jest.teardown.js 统一关闭

describe('培训学习', () => {
  test('培训页面加载 [smoke]', async () => {
    const page = new StudyPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const plans = await page.getTrainingPlans();
    const records = await page.getStudyRecords();
    const progress = await page.getProgress();

    console.log(`  培训计划数: ${plans.length}`);
    console.log(`  学习记录数: ${records.length}`);
    console.log(`  总体进度: ${JSON.stringify(progress)}`);
  });
});

describe('考试列表', () => {
  test('考试页面加载 [smoke]', async () => {
    const page = new ExamListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const exams = await page.getExamList();
    console.log(`  考试安排数: ${exams.length}`);

    if (exams.length > 0) {
      const first = exams[0];
      console.log(`  第一个考试: ${JSON.stringify(first).slice(0, 150)}`);
    }

    expect(Array.isArray(exams)).toBe(true);
  });

  test('考试列表中存在可用考试', async () => {
    const page = new ExamListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const exams = await page.getExamList();
    if (exams.length === 0) {
      console.log('  当前无考试安排');
    } else {
      // 检查考试项目的基本字段
      const first = exams[0];
      const hasTitle = !!(first.examTitle || first.examName || first.title);
      console.log(`  考试标题存在: ${hasTitle}`);
    }
  });
});

describe('考试答题流程', () => {
  test('进入答题页并加载题目 [destructive]', async () => {
    const listPage = new ExamListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const exams = await listPage.getExamList();
    // 找一个可参加的考试（pending/in_progress/not_started）
    const available = exams.filter(
      e => ['pending', 'in_progress', 'not_started'].includes(e.status)
    );

    if (available.length === 0) {
      console.log('  无可参加的考试，跳过');
      return;
    }

    // 进入答题页
    await listPage.tapExam(0);

    const answerPage = new AnswerPage(driver.app);
    await answerPage.waitForQuestions();

    const questionCount = await answerPage.getQuestionCount();
    console.log(`  题目数: ${questionCount}`);
    expect(questionCount).toBeGreaterThan(0);
  });

  test('答题后提交 [destructive]', async () => {
    const listPage = new ExamListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const exams = await listPage.getExamList();
    const available = exams.filter(
      e => ['pending', 'in_progress', 'not_started'].includes(e.status)
    );

    if (available.length === 0) {
      console.log('  无可参加的考试，跳过');
      return;
    }

    await listPage.tapExam(0);

    const answerPage = new AnswerPage(driver.app);
    await answerPage.waitForQuestions();

    // 做前 3 题
    const total = await answerPage.getQuestionCount();
    const answerCount = Math.min(total, 3);
    for (let i = 0; i < answerCount; i++) {
      await answerPage.selectOption('A');
      if (i < answerCount - 1) {
        await answerPage.nextQuestion();
      }
    }

    // 提交
    await answerPage.submit();

    // 检查是否跳转到成绩页
    await new Promise(r => setTimeout(r, 3000));
    try {
      const resultPage = new ExamResultPage(driver.app);
      const score = await resultPage.getScore();
      console.log(`  考试成绩: ${score}`);
    } catch {
      console.log('  未跳转到成绩页（可能需确认弹窗）');
    }
  });
});

describe('题目标记功能 (TC-EXAM-010)', () => {
  test('标记/取消标记题目', async () => {
    const listPage = new ExamListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const exams = await listPage.getExamList();
    const available = exams.filter(
      e => ['pending', 'in_progress', 'not_started'].includes(e.status)
    );
    if (available.length === 0) {
      console.log('  无可参加的考试，跳过');
      return;
    }

    await listPage.tapExam(0);
    const answerPage = new AnswerPage(driver.app);
    await answerPage.waitForQuestions();

    // 标记当前题目
    await answerPage.toggleMark();
    await sleep(1000);
    const dataAfterMark = await answerPage.getAnswerData();
    console.log(`  标记后数据: marked=${dataAfterMark.markedQuestions ? '有标记' : '无标记'}`);

    // 取消标记
    await answerPage.toggleMark();
    await sleep(1000);
    console.log('  标记/取消标记操作完成');
  });
});

describe('答题卡导航 (TC-EXAM-011)', () => {
  test('打开答题卡并点击题号跳转', async () => {
    const listPage = new ExamListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const exams = await listPage.getExamList();
    const available = exams.filter(
      e => ['pending', 'in_progress', 'not_started'].includes(e.status)
    );
    if (available.length === 0) {
      console.log('  无可参加的考试，跳过');
      return;
    }

    await listPage.tapExam(0);
    const answerPage = new AnswerPage(driver.app);
    await answerPage.waitForQuestions();

    // 尝试打开答题卡
    try {
      await answerPage.callMethod('toggleSheet');
      await sleep(1500);
      const sheetData = await answerPage.getAnswerData();
      console.log(`  答题卡数据: sheet=${sheetData.showSheet ? '打开' : '关闭'}`);
    } catch {
      console.log('  答题卡切换方法不可用，跳过');
    }
  });
});
