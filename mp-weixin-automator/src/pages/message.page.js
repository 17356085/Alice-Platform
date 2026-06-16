/**
 * 消息通知 Page Objects — pages-sub/message/index + detail
 *
 * 功能: 消息列表（未读标记、全部已读）、消息详情
 */
const { MiniPage } = require('../MiniPage');

class MessageListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/message/index';

  async waitForList(timeout = 10000) {
    await this.waitFor('.message-list, .notice-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getMessageList() {
    const data = await this.getData();
    return data.messageList || data.records || [];
  }

  async getUnreadCount() {
    const data = await this.getData();
    return data.unreadCount || 0;
  }

  /** 全部标为已读 */
  async markAllRead() {
    await this.callMethod('markAllRead');
    await this.waitForDataReady(3000);
  }
}

class MessageDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/message/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.message-detail, .notice-detail', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = { MessageListPage, MessageDetailPage };
