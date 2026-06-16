const { MiniPage } = require('../MiniPage');

/**
 * 考试答题页 — pages-sub/study/exam + answer + result
 *
 * 完整的考试流程：列表 → 答题 → 提交 → 查看成绩
 */
class ExamListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/exam';

  async waitForList(timeout = 15000) {
    await this.waitFor('.exam-item, .exam-list', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 获取考试列表 */
  async getExamList() {
    const data = await this.getData();
    return data.examList || data.list || [];
  }

  /** 点击考试项进入答题 */
  async tapExam(index = 0) {
    const items = await this.$$('.exam-item, .exam-card');
    if (items.length > index) {
      await items[index].tap();
      console.log(`  [Exam] 点击考试项: index=${index}`);
    }
  }
}

/**
 * 答题页 — pages-sub/study/answer
 */
class AnswerPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/answer';

  async waitForQuestions(timeout = 15000) {
    await this.waitFor('.question-card, .question-item', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 获取题目数量 */
  async getQuestionCount() {
    const data = await this.getData();
    return data.questions?.length || data.totalQuestions || 0;
  }

  /** 获取当前题目索引 */
  async getCurrentIndex() {
    const data = await this.getData();
    return data.currentIndex || 0;
  }

  /**
   * 选择选项（单选/多选）
   * @param {string|number} optionLetter  如 'A', 'B'
   */
  async selectOption(optionLetter) {
    const options = await this.$$('.option-item, .option');
    for (const opt of options) {
      const text = (await opt.text()) || '';
      if (text.trim().startsWith(optionLetter)) {
        await opt.tap();
        console.log(`  [Exam] 选择: ${optionLetter}`);
        return;
      }
    }
  }

  /** 下一题 */
  async nextQuestion() {
    const nextBtn = await this.$('.next-btn, .btn-next');
    if (nextBtn) {
      await nextBtn.tap();
    }
  }

  /** 上一题 */
  async prevQuestion() {
    const prevBtn = await this.$('.prev-btn, .btn-prev');
    if (prevBtn) {
      await prevBtn.tap();
    }
  }

  /** 标记题目 */
  async toggleMark() {
    await this.callMethod('toggleMark');
  }

  /** 提交试卷 */
  async submit() {
    const submitBtn = await this.$('.submit-btn, .btn-submit');
    if (submitBtn) {
      await submitBtn.tap();
      console.log('  [Exam] 提交试卷');
    }
  }

  /** 获取答题数据 */
  async getAnswerData() {
    return this.getData();
  }
}

/**
 * 考试成绩页 — pages-sub/study/result
 */
class ExamResultPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/result';

  async waitForResult(timeout = 15000) {
    await this.waitFor('.result-card, .score-display', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 获取成绩 */
  async getScore() {
    const data = await this.getData();
    return data.score ?? data.examScore ?? 0;
  }

  /** 是否通过 */
  async getIsPass() {
    const data = await this.getData();
    return data.isPass ?? data.passed ?? false;
  }

  /** 获取错题 */
  async getWrongQuestions() {
    const data = await this.getData();
    return data.wrongQuestions || [];
  }
}

module.exports = { ExamListPage, AnswerPage, ExamResultPage };
