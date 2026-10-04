// 用最小 DOM 桩执行看板脚本，验证渲染 / 状态流转 / 筛选 / 增删 / 撤销 / 同步等行为
// 用法：node tests/dashboard.test.js      期望输出「全部通过」
// 说明：断言与数据量无关（示例数据只有 6 条也能跑），便于开源后随示例数据回归
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'dashboard.html'), 'utf8');
const script = html.slice(html.lastIndexOf('<script>') + 8, html.lastIndexOf('</script>'));

function El(id) {
  return { id, innerHTML: '', textContent: '', value: '', dataset: {}, style: {},
    classList: { add() {}, remove() {}, contains() { return false; }, toggle() {} },
    addEventListener() {}, appendChild() {}, click() {},
    querySelectorAll() { return []; }, closest() { return null; }, files: [] };
}
const els = {};
global.document = {
  getElementById(id) { return els[id] || (els[id] = El(id)); },
  querySelectorAll() { return []; },
  createElement() { return El('a'); },
  addEventListener() {}
};
global.localStorage = { getItem() { return null; }, setItem() {}, removeItem() {} };
global.window = global;
global.alert = m => { global.__lastAlert = m; };
global.confirm = () => true;
global.URL = { createObjectURL() { return ''; }, revokeObjectURL() {} };
global.Blob = function () {};
global.FileReader = function () {};

let err = null;
try { new Function(script)(); } catch (e) { err = e; }
const A = global.__app;
const ok = [], bad = [];
const t = (name, cond, extra) => (cond ? ok : bad).push(name + (extra ? ' → ' + extra : ''));
t('脚本无运行时错误', !err, err ? err.name + ': ' + err.message : '');
if (err) { console.log('FATAL:', err); process.exit(1); }

const N = A.state.applications.length;
const first = A.state.applications[0];
const firstCo = first['企业'];

// 1. 初始渲染（看板）
const board = els['boardView'].innerHTML || '';
t('看板渲染 7 列', (board.match(/class="col"/g) || []).length === 7, (board.match(/class="col"/g) || []).length + ' 列');
t('看板渲染全部卡片', (board.match(/class="kcard/g) || []).length >= N, (board.match(/class="kcard/g) || []).length + '/' + N);
t('含企业数据', board.includes(firstCo), firstCo);
t('漏斗统计已渲染（英文）', (els['funnel'].innerHTML || '').includes('Applied'));
t('计数与数据量一致（英文界面）', els['count'].textContent === N + ' companies', els['count'].textContent);
t('梯队下拉已渲染（英文）', (els['tier'].innerHTML || '').includes('All tiers'), (els['tier'].innerHTML||'').slice(0,40));
t('状态筛选 pills 已移除', !html.includes('id="pills"'));
t('默认展示全部', A.filtered().length === N, A.filtered().length + '');

// 2. 列表视图
A.setView('list');
const list = els['listView'].innerHTML || '';
t('列表渲染 table', list.includes('<table>'));
t('列表行数一致', (list.match(/<tr data-ci=/g) || []).length === N, (list.match(/<tr data-ci=/g) || []).length + '/' + N);
t('列表含企业数据', list.includes(firstCo));
A.setView('board');

// 3. 状态流转
const a0 = A.state.applications[0];
const before = a0['投递状态'];
A.setStatus(a0, '已投递', '测试投递');
t('状态已流转', a0['投递状态'] === '已投递', before + '→' + a0['投递状态']);
t('自动补投递日期', !!a0['投递日期'], a0['投递日期']);
t('写入状态历史', (a0['状态历史'] || []).length === 1 && a0['状态历史'][0]['到'] === '已投递');
A.setStatus(a0, '综合素质评测', '测试测评');
t('历史累积 2 条', (a0['状态历史'] || []).length === 2);
t('nextStatus(已投递)=综合素质评测', A.nextStatus('已投递') === '综合素质评测');
t('nextStatus(综合素质评测)=笔试', A.nextStatus('综合素质评测') === '笔试');
t('nextStatus(笔试)=一面', A.nextStatus('笔试') === '一面');
t('nextStatus(offer)=null', A.nextStatus('offer') === null);
t('nextStatus(已拒)=null', A.nextStatus('已拒') === null);

// 4. 停滞计算
const a1 = A.addApp(Object.assign(A.blank(), { 企业: '停滞测试' }));
A.setStatus(a1, '已投递', 't');
a1['投递日期'] = '2026-09-01';
a1['状态历史'] = [{ 日期: '2026-09-01', 从: '未投递', 到: '已投递', 备注: '' }];
const sd = A.staleDays(a1);
t('停滞天数计算正确', typeof sd === 'number' && sd > 30, String(sd));
const a2 = A.addApp(Object.assign(A.blank(), { 企业: '未投递测试' }));
t('未投递不算停滞', A.staleDays(a2) === null);

// 5. 筛选
const tier0 = first['梯队'];
const tierCount = A.state.applications.filter(x => x['梯队'] === tier0).length;
A.setFilter({ group: 'all', q: firstCo.slice(0, 2) });
t('按企业名搜索命中', A.filtered().length >= 1, A.filtered().length + '');
A.setFilter({ q: '', tier: tier0 });
t('按梯队筛选正确', A.filtered().length === tierCount, A.filtered().length + '/' + tierCount);
A.setFilter({ tier: '' });
t('清空筛选=全部', A.filtered().length === N + 2, A.filtered().length + '');
A.setFilter({ q: '绝不可能存在的公司名ZZZ' });
t('无匹配时为空', A.filtered().length === 0, A.filtered().length + '');
A.setFilter({ q: '' });

// 6. 增删
const n0 = A.state.applications.length;
A.addApp(Object.assign(A.blank(), { 企业: '测试公司', 投递状态: '已投递', 投递日期: '2026-10-04' }));
t('新增后 +1', A.state.applications.length === n0 + 1, A.state.applications.length + '');
A.save();
const removed = A.delApp(A.state.applications.length - 1);
t('删除返回被删对象', removed && removed['企业'] === '测试公司');
A.save();
t('删除后恢复原数量', A.state.applications.length === n0, A.state.applications.length + '');

// 7. 数据完整性
const missing = A.state.applications.filter(x => !x['企业'] || !x['投递状态']).length;
t('无缺字段记录', missing === 0, missing + ' 条');
const ids = new Set(A.state.applications.map(x => x.id));
t('id 唯一', ids.size === A.state.applications.length, ids.size + '/' + A.state.applications.length);

// 8. 状态历史去噪
const h1 = A.addApp(Object.assign(A.blank(), { 企业: '历史测试A' }));
A.setStatus(h1, '已投递', '拖拽');
t('正向流转记 1 条', h1['状态历史'].length === 1, h1['状态历史'].length + ' 条');
A.setStatus(h1, '未投递', '拖拽');
t('拖回后历史清空（抵消）', h1['状态历史'].length === 0, h1['状态历史'].length + ' 条');
t('拖回后状态回到未投递', h1['投递状态'] === '未投递');
for (let i = 0; i < 3; i++) { A.setStatus(h1, '已投递', '拖拽'); A.setStatus(h1, '未投递', '拖拽'); }
t('反复拖 3 轮后仍无历史', h1['状态历史'].length === 0, h1['状态历史'].length + ' 条');

const h2 = A.addApp(Object.assign(A.blank(), { 企业: '历史测试B' }));
A.setStatus(h2, '已投递', ''); A.setStatus(h2, '综合素质评测', ''); A.setStatus(h2, '笔试', '');
t('连续推进保留 3 条', h2['状态历史'].length === 3, h2['状态历史'].length + ' 条');
A.setStatus(h2, '综合素质评测', '回退');
t('部分回退抵消最后一段', h2['状态历史'].length === 2, h2['状态历史'].length + ' 条');

const h3 = A.addApp(Object.assign(A.blank(), { 企业: '历史测试C', 投递状态: '笔试' }));
h3['状态历史'] = [
  { 日期: '2026-10-04', 从: '已投递', 到: '未投递', 备注: '看板拖拽' },
  { 日期: '2026-10-04', 从: '未投递', 到: '已投递', 备注: '看板拖拽' },
  { 日期: '2026-10-04', 从: '已投递', 到: '未投递', 备注: '看板拖拽' },
  { 日期: '2026-10-04', 从: '未投递', 到: '已投递', 备注: '看板拖拽' },
  { 日期: '2026-10-04', 从: '笔试', 到: '未投递', 备注: '看板拖拽' },
  { 日期: '2026-10-04', 从: '未投递', 到: '笔试', 备注: '看板拖拽' },
];
t('既有噪音被清空', A.compactHistory(h3).length === 0, A.compactHistory(h3).length + ' 条');
t('整理不改动当前状态', h3['投递状态'] === '笔试', h3['投递状态']);

const h4 = A.addApp(Object.assign(A.blank(), { 企业: '历史测试D' }));
h4['状态历史'] = [
  { 日期: '2026-09-01', 从: '未投递', 到: '已投递', 备注: '' },
  { 日期: '2026-09-02', 从: '已投递', 到: '未投递', 备注: '' },
];
t('跨天记录不被合并', A.compactHistory(h4).length === 2, A.compactHistory(h4).length + ' 条');

// 9. 企业库自动补齐
const libCo = A.state.applications.find(x => x['企业'] && x['岗位']) || first;
const libHit = A.lookupCompany(libCo['企业']);
t('企业库命中自身', !!libHit && libHit['企业'] === libCo['企业']);
t('模糊匹配可用', !!A.lookupCompany(libCo['企业'].slice(0, 2)), libCo['企业'].slice(0, 2));
t('未知企业返回 null', A.lookupCompany('不存在的公司XYZ') === null);
const b = A.blank();
t('新建默认日期=今天', b['投递日期'] === new Date().toISOString().slice(0, 10), b['投递日期']);
t('新建默认渠道=官网', b['渠道'] === '官网', b['渠道']);
t('新建默认优先级=3', b['优先级'] === 3, String(b['优先级']));
t('blank 含岗位列表', Array.isArray(b['岗位列表']));

// 10. 投递链接
const board2 = els['boardView'].innerHTML || '';
t('看板链接含 target=_blank', board2.includes('target="_blank"'));
t('看板链接含 rel=noopener', board2.includes('rel="noopener'));
t('看板链接带 stopPropagation', board2.includes('event.stopPropagation()'));
const linkA = A.state.applications.find(x => x['链接状态'] === '可访问') || first;
t('可访问 → 徽章为 ok', A.linkClass(linkA) === 'ok', A.linkClass(linkA));
t('无链接 → off 样式', A.linkAnchor(Object.assign(A.blank(), { 投递链接: '' })).includes('gotolink off'));
const issueCount = A.state.applications.filter(x => A.linkIssue(x)).length;
A.setFilter({ issue: true });
t('只看链接异常过滤生效', A.filtered().length === issueCount, A.filtered().length + '/' + issueCount);
A.setFilter({ issue: false });

// 11. 岗位解析（批量粘贴）
const SAMPLE = [
  '全部在招职位（362）',
  'AI应用算法工程师', '更新于 2026-09-03', '技术类', '北京 / 广州 / 杭州 / 上海',
  '在招业务', '示例事业群 A / 示例事业群 B',
  'Agent Infra工程师', '更新于 2026-09-03', '技术类', '北京 / 深圳',
  '在招业务', '示例事业群 A',
  'AI Agent优化工程师-训练/数据/评测', '展开详情', '更新于 2026-08-24', '技术类', '北京 / 杭州',
  '在招业务', '示例事业群 A / 示例事业群 C',
].join('\n');
const parsed = A.parsePositions(SAMPLE);
t('解析出 3 个岗位', parsed.length === 3, parsed.length + ' 个');
t('岗位名正确', parsed[0]['岗位'] === 'AI应用算法工程师', parsed[0]['岗位']);
t('更新日期正确', parsed[0]['更新日期'] === '2026-09-03', parsed[0]['更新日期']);
t('类型正确', parsed[0]['类型'] === '技术类', parsed[0]['类型']);
t('城市正确', parsed[0]['城市'] === '北京 / 广州 / 杭州 / 上海', parsed[0]['城市']);
t('在招业务正确', parsed[0]['在招业务'].indexOf('示例事业群') >= 0, parsed[0]['在招业务'].slice(0, 16));
t('带斜杠标题不被误判为城市', parsed[2]['岗位'] === 'AI Agent优化工程师-训练/数据/评测', parsed[2]['岗位']);
t('解析结果默认未投递', parsed[0]['投递状态'] === '未投递', parsed[0]['投递状态']);

// 12. 一家公司多个岗位：状态聚合 + 分组卡
const gco = A.addApp(Object.assign(A.blank(), { 企业: '多岗位测试公司' }));
gco['岗位列表'] = [
  Object.assign(A.blankPosition(), { 岗位: '岗位甲', 投递状态: '已投递', 投递日期: '2026-09-20' }),
  Object.assign(A.blankPosition(), { 岗位: '岗位乙', 投递状态: '笔试', 类型: '技术类', 城市: '杭州' }),
];
A.syncCompanyFromPositions(gco);
t('公司状态聚合为最靠前进度(笔试)', gco['投递状态'] === '笔试', gco['投递状态']);
t('公司投递日期取最早', gco['投递日期'] === '2026-09-20', gco['投递日期']);
t('effStatus 用聚合值', A.effStatus(gco) === '笔试', A.effStatus(gco));
gco['岗位列表'] = [
  Object.assign(A.blankPosition(), { 岗位: '岗位甲', 投递状态: '已拒' }),
  Object.assign(A.blankPosition(), { 岗位: '岗位乙', 投递状态: '已拒' }),
];
t('全部终止时取终止态', A.aggStatus(gco) === '已拒', A.aggStatus(gco));

gco['岗位列表'] = [
  Object.assign(A.blankPosition(), { 岗位: '岗位甲', 投递状态: '已投递' }),
  Object.assign(A.blankPosition(), { 岗位: '岗位乙', 投递状态: '已投递' }),
];
A.syncCompanyFromPositions(gco);
A.setUnit('position');
A.save();
const gb = els['boardView'].innerHTML || '';
const groupedCards = (gb.match(/class="kcard grouped"/g) || []).length;
t('按岗位视图渲染分组卡', groupedCards >= 1, groupedCards + ' 张');
const gcHtml = A.kcardGroup(gco, 0);
t('分组卡内含 2 个岗位行', (gcHtml.match(/class="prow"/g) || []).length === 2, (gcHtml.match(/class="prow"/g) || []).length + ' 行');
t('岗位行含状态下拉', gcHtml.includes('data-posstatus="1"'));
t('岗位行含推进/编辑', gcHtml.includes('data-posadv="1"') && gcHtml.includes('data-posedit="1"'));
t('分组卡自身不可拖拽', gcHtml.includes('draggable="false"'));
t('分组卡显示岗位数（英文，经 localize）', A.localize(gcHtml).includes('2 positions'), A.localize(gcHtml).slice(0, 60));
A.setUnit('company');
A.save();

// 13. 备份快照 / 恢复
const lsStore = {};
global.localStorage = {
  get length() { return Object.keys(lsStore).length; },
  key(i) { return Object.keys(lsStore)[i] || null; },
  getItem(k) { return Object.prototype.hasOwnProperty.call(lsStore, k) ? lsStore[k] : null; },
  setItem(k, v) { lsStore[k] = String(v); },
  removeItem(k) { delete lsStore[k]; }
};
t('快照写入成功', A.snapshot('测试快照') === true);
t('快照可列出', A.listBackups().length >= 1, A.listBackups().length + ' 份');
const snapKey = A.listBackups()[0].key;
const beforeCount = A.state.applications.length;
A.state.applications = [];
A.save();
t('清空后为 0 条', A.state.applications.length === 0);
t('恢复快照成功', A.restoreBackup(snapKey) === true);
t('恢复后条数一致', A.state.applications.length === beforeCount, A.state.applications.length + '/' + beforeCount);

// 14. 撤销
const undoBefore = A.state.applications[0]['投递状态'];
A.setStatus(A.state.applications[0], '已投递', '撤销测试');
A.save();
t('操作后状态已变', A.state.applications[0]['投递状态'] === '已投递');
A.undo();
t('撤销后回到原状态', A.state.applications[0]['投递状态'] === undoBefore,
  A.state.applications[0]['投递状态'] + ' (期望 ' + undoBefore + ')');
const st0 = A.state.applications[0]['投递状态'];
A.setStatus(A.state.applications[0], '综合素质评测', 'a'); A.save();
const st1 = A.state.applications[0]['投递状态'];
A.setStatus(A.state.applications[0], '笔试', 'b'); A.save();
A.undo();
t('撤销 1 次 → 上一步', A.state.applications[0]['投递状态'] === st1, A.state.applications[0]['投递状态']);
A.undo();
t('撤销 2 次 → 再上一步', A.state.applications[0]['投递状态'] === st0, A.state.applications[0]['投递状态']);

// 15. 界面只保留指定操作按钮
['addBtn', 'importBtn', 'exportBtn', 'undoBtn', 'resetBtn'].forEach(id => {
  t('保留按钮 ' + id, html.includes('id="' + id + '"'));
});
['csvBtn', 'compactBtn', 'mergeBtn', 'restoreBtn', 'importReplaceBtn', 'compactOneBtn'].forEach(id => {
  t('已移除按钮 ' + id, !html.includes('id="' + id + '"'));
});

// 16. 自动写文件（Node 无 File System Access，应安全降级）
t('fsSupported 在无 API 环境返回 false', A.fsSupported() === false);
t('未绑定时 scheduleFileWrite 不抛错', (function () { try { A.scheduleFileWrite(); return true; } catch (e) { return false; } })());
t('未绑定时 writeToFile 不返回 true', (function () { try { return A.writeToFile() === true; } catch (e) { return false; } })() === false);
t('renderFileStatus 可渲染', (function () { try { A.renderFileStatus(); return true; } catch (e) { return false; } })());
t('save() 不抛错', (function () { try { A.save(); return true; } catch (e) { return false; } })());
t('diffSince 可调用', (function () { try { A.diffSince(); return true; } catch (e) { return false; } })());
t('flushSync 存在', typeof A.flushSync === 'function');

// 17. 开源安全：看板内不得含真实公司名
const realNames = ['阿里巴巴', '蚂蚁集团', '字节跳动', '腾讯', '百度', '美团', '京东', '网易', '华为', '海康威视'];
const leaked = realNames.filter(n => html.includes(n));
t('看板内无真实公司名', leaked.length === 0, leaked.join(','));


// 18. i18n：默认英文界面，数据键值仍为中文
t('界面默认英文（看板列名）', /Applied|Not applied|Interviewing|Closed/.test(els['boardView'].innerHTML || ''));
t('看板文本节点不再出现中文状态', !/>\s*(未投递|已投递|面试中|已结束)\s*</.test(els['boardView'].innerHTML || ''));
t('option 的 value 仍为中文（数据不变）', A.localize('<option value="未投递">未投递</option>').includes('value="未投递"'));
t('数据键仍为中文（企业/投递状态）', A.state.applications.every(x => '企业' in x && '投递状态' in x));
t('状态值仍为中文（未投递/已投递）', A.state.applications.every(x => /^[\u4e00-\u9fff]|^offer$/.test(x['投递状态'])));
t('语言切换按钮存在', html.includes('id="langBtn"'));
t('i18n 词表存在', html.includes('const EN = {') && html.includes('function localize('));
t('状态 option 带显式 value（防翻译污染数据）', html.includes('value="${esc(s)}"'));
t('textarea 内容受保护（备注为数据）', A.localize('<textarea data-k="备注">备注：笔试通过</textarea>').includes('备注：笔试通过'));
t('localize 不碰 value 属性', A.localize('<input value="已投递">').includes('value="已投递"'));
t('T() 精确翻译状态', A.T('已投递') === 'Applied', A.T('已投递'));
t('T() 正则翻译动态文案', A.T('共 12 家') === '12 companies', A.T('共 12 家'));

console.log('\n通过 ' + ok.length + ' 项：');
ok.forEach(x => console.log('  ✓ ' + x));
if (bad.length) { console.log('\n失败 ' + bad.length + ' 项：'); bad.forEach(x => console.log('  ✗ ' + x)); process.exit(1); }
console.log('\n全部通过');
