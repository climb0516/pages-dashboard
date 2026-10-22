// Created by 青云 on 2026/10/21.
// 全部站点清单（大屏、健康点都从这里读）。新增站点：在对应分组里加一行；大屏没有专属卡片的站点会自动显示为通用入口卡。
// kind: 'data' = 有 data.json 的数据站，'tool' = 静态工具页（只放入口）
window.PAGES_SITES = [
  // 财经
  { repo: 'market-board', name: '市场看板', group: '财经', kind: 'data' },
  { repo: 'earnings-calendar', name: '财报宏观', group: '财经', kind: 'data' },
  { repo: 'savings-rates', name: '存款与国债', group: '财经', kind: 'data' },
  { repo: 'nasdaq-dca', name: '纳指定投', group: '财经', kind: 'data' },
  // 资讯
  { repo: 'hot-news', name: '全网热榜', group: '资讯', kind: 'data' },
  { repo: 'tech-news', name: '科技动态', group: '资讯', kind: 'data' },
  { repo: 'ios-dev-news', name: 'iOS 开发动态', group: '资讯', kind: 'data' },
  { repo: 'appstore-tracker', name: 'AppWatch 竞品', group: '资讯', kind: 'data' },
  // 生活
  { repo: 'hz-weekend', name: '杭州周末', group: '生活', kind: 'data' },
  { repo: 'recall-watch', name: '消费避坑', group: '生活', kind: 'data' },
  { repo: 'food-prices', name: '菜价物价', group: '生活', kind: 'data' },
  { repo: 'home-prices', name: '70 城房价', group: '生活', kind: 'data' },
  { repo: 'health-weekly', name: '呼吸道周报', group: '生活', kind: 'data' },
  { repo: 'new-rules', name: '每月新规', group: '生活', kind: 'data' },
  // 出行 · 娱乐
  { repo: 'holiday-planner', name: '拼假攻略', group: '出行娱乐', kind: 'data' },
  { repo: 'ticket-calendar', name: '抢票日历', group: '出行娱乐', kind: 'data' },
  { repo: 'exam-calendar', name: '考试日历', group: '出行娱乐', kind: 'data' },
  { repo: 'match-day', name: '赛程', group: '出行娱乐', kind: 'data' },
  { repo: 'weekly-new', name: '本周上新', group: '出行娱乐', kind: 'data' },
  { repo: 'short-drama', name: '短剧', group: '出行娱乐', kind: 'data' },
  { repo: 'game-deals', name: 'PS 港服 · 喜加一', group: '出行娱乐', kind: 'data' },
  { repo: 'car-deals', name: '车市行情', group: '出行娱乐', kind: 'data' },
  // 工具
  { repo: 'img2doc', name: '图片转文档', group: '工具', kind: 'tool', desc: '图片转 Word / Markdown' },
  { repo: 'poker-score', name: '德扑计分器', group: '工具', kind: 'tool', desc: '牌局记账与结算' },
  { repo: 'Climb0516.github.io', name: "Climb's Zone", group: '工具', kind: 'tool', desc: '个人主页', url: 'https://climb0516.github.io/' },
];
