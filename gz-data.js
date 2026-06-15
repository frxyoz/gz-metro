// Guangzhou Metro — historical schematic dataset
// Stylized 45/90 diagram. Coordinates in an 1680 x 1060 SVG space (north = up).
// Each station: [en, zh, x, y, opened 'YYYY-MM-DD', interchange?]
// Dates are phase-level and sourced from public records (Wikipedia / operator history).
// A segment between two consecutive open stations draws when the slider date >= the later station's opening.

export const SYSTEM_START = "1997-06-28";

// ---- Line color palette — exact hex values from the reference diagram ----
// Excluded from mapping: #FFFFFF/#FCFCFC/#F0F0F0 (white casing), #1262AD (label/interchange ink), #000000 (decorative dots)
// Unassigned reference colors (likely Foshan Metro or future lines): #3F51B5, #FF1744, #F44336, #DD2C00, #D901DE, #00E5FF, #1DE9B6, #00E676, #D08693, #33691E, #90CAF9
export const LINE_COLORS = {
  '1':   '#FDD835',  // yellow
  '2':   '#1E88E5',  // blue
  '3':   '#FB8C00',  // orange
  '4':   '#43A047',  // green
  '5':   '#E53935',  // red
  '6':   '#8E24AA',  // purple
  '7':   '#7CB342',  // lime green
  '8':   '#00897B',  // teal
  '9':   '#00BFA5',  // teal-green
  '10':  '#7389B2',  // blue-gray
  '11':  '#FAC525',  // golden yellow
  '12':  '#435428',  // dark olive green
  '13':  '#827717',  // olive
  '14':  '#6D4C41',  // brown
  '18':  '#3949AB',  // indigo
  '21':  '#1A237E',  // dark navy
  '22':  '#CD5228',  // burnt orange — official GZ Metro Line 22 color
  'APM': '#00B0FF',  // light blue
  'GF':  '#C0CA33',  // yellow-green
};

// ---- Official line palette (the ONLY saturated colour in the piece) ----
export const LINES = [
  {
    id: "1", name_en: "Line 1", name_zh: "1号线", color: LINE_COLORS['1'], opened: "1997-06-28",
    stations: [
      ["Xilang", "西塱", 300, 560, "1997-06-28", true],
      ["Kengkou", "坑口", 356, 560, "1997-06-28"],
      ["Huadiwan", "花地湾", 412, 560, "1997-06-28"],
      ["Fangcun", "芳村", 468, 560, "1997-06-28"],
      ["Huangsha", "黄沙", 524, 560, "1997-06-28", true],
      ["Changshou Rd", "长寿路", 572, 512, "1999-06-28"],
      ["Chen Clan Academy", "陈家祠", 620, 464, "1999-06-28"],
      ["Ximenkou", "西门口", 660, 440, "1999-06-28"],
      ["Gongyuanqian", "公园前", 700, 440, "1999-06-28", true],
      ["Peasant Movement Inst.", "农讲所", 748, 440, "1999-06-28"],
      ["Martyr's Park", "烈士陵园", 796, 440, "1999-06-28"],
      ["Dongshankou", "东山口", 844, 440, "1999-06-28", true],
      ["Yangji", "杨箕", 892, 440, "1999-06-28", true],
      ["Tiyu Xilu", "体育西路", 940, 440, "1999-06-28", true],
      ["Tianhe Sports Center", "体育中心", 940, 400, "1999-06-28"],
      ["Guangzhou East Rly.", "广州东站", 940, 360, "1999-06-28", true],
    ],
  },
  {
    id: "2", name_en: "Line 2", name_zh: "2号线", color: LINE_COLORS['2'], opened: "2002-12-29",
    stations: [
      ["Jiahewanggang", "嘉禾望岗", 700, 220, "2010-09-25", true],
      ["Huangbian", "黄边", 700, 264, "2010-09-25"],
      ["Baiyun Culture Sq.", "白云文化广场", 700, 300, "2010-09-25"],
      ["Sanyuanli", "三元里", 700, 344, "2002-12-29"],
      ["Guangzhou Rly. Station", "广州火车站", 700, 384, "2002-12-29", true],
      ["Yuexiu Park", "越秀公园", 700, 412, "2002-12-29"],
      ["Sun Yat-sen Mem. Hall", "纪念堂", 700, 432, "2002-12-29"],
      ["Gongyuanqian", "公园前", 700, 440, "2002-12-29", true],
      ["Haizhu Square", "海珠广场", 700, 500, "2002-12-29", true],
      ["Shi'ergong", "市二宫", 700, 540, "2002-12-29"],
      ["Jiangnanxi", "江南西", 700, 600, "2003-06-28", true],
      ["Changgang", "昌岗", 700, 648, "2010-09-25", true],
      ["Jiangtai Rd", "江泰路", 660, 700, "2010-09-25"],
      ["Nanzhou", "南洲", 620, 740, "2010-09-25"],
      ["Luoxi", "洛溪", 580, 776, "2010-09-25"],
      ["Nanpu", "南浦", 540, 812, "2010-09-25"],
      ["Guangzhou South Rly.", "广州南站", 480, 860, "2010-09-25", true],
    ],
  },
  {
    id: "3", name_en: "Line 3", name_zh: "3号线", color: LINE_COLORS['3'], opened: "2005-12-26",
    // Main rider path: Airport North -> Tiyu Xilu -> Panyu Square
    stations: [
      ["Airport North", "机场北", 880, 56, "2018-04-26", true],
      ["Airport South", "机场南", 880, 104, "2010-10-30"],
      ["Renhe", "人和", 840, 152, "2010-10-30"],
      ["Jiahewanggang", "嘉禾望岗", 700, 220, "2010-10-30", true],
      ["Baiyun Avenue North", "白云大道北", 760, 300, "2010-10-30"],
      ["Tonghe", "同和", 800, 344, "2010-10-30"],
      ["Meihuayuan", "梅花园", 880, 320, "2010-10-30"],
      ["Guangzhou East Rly.", "广州东站", 940, 360, "2005-12-26", true],
      ["Linhexi", "林和西", 940, 400, "2005-12-26", true],
      ["Tiyu Xilu", "体育西路", 940, 440, "2005-12-26", true],
      ["Zhujiang New Town", "珠江新城", 940, 500, "2005-12-26", true],
      ["Canton Tower", "广州塔", 900, 600, "2005-12-26", true],
      ["Kecun", "客村", 860, 600, "2005-12-26", true],
      ["Datang", "大塘", 860, 660, "2006-12-30"],
      ["Lijiao", "沥滘", 820, 720, "2006-12-30"],
      ["Xiajiao", "厦滘", 800, 768, "2006-12-30"],
      ["Dashi", "大石", 800, 812, "2006-12-30"],
      ["Hanxi Changlong", "汉溪长隆", 800, 856, "2006-12-30", true],
      ["Shiqiao", "市桥", 800, 900, "2006-12-30"],
      ["Panyu Square", "番禺广场", 800, 940, "2006-12-30", true],
    ],
    // Branch: Tianhe Coach Terminal -> Tiyu Xilu (opened 2006-12-30, north section 2010)
    branch: [
      ["Tianhe Coach Terminal", "天河客运站", 1060, 300, "2010-10-30", true],
      ["Wushan", "五山", 1020, 344, "2010-10-30"],
      ["Huashi", "华师", 1000, 384, "2006-12-30", true],
      ["Gangding", "岗顶", 980, 412, "2006-12-30"],
      ["Shipaiqiao", "石牌桥", 960, 428, "2006-12-30"],
      ["Tiyu Xilu", "体育西路", 940, 440, "2006-12-30", true],
    ],
  },
  {
    id: "4", name_en: "Line 4", name_zh: "4号线", color: LINE_COLORS['4'], opened: "2005-12-26",
    stations: [
      ["Huangcun", "黄村", 1060, 420, "2009-12-28", true],
      ["Chebeinan", "车陂南", 1060, 472, "2009-12-28", true],
      ["Wanshengwei", "万胜围", 1060, 540, "2005-12-26", true],
      ["Guanzhou", "官洲", 1060, 600, "2005-12-26"],
      ["Higher Ed. Mega Ctr. N", "大学城北", 1060, 648, "2005-12-26", true],
      ["Higher Ed. Mega Ctr. S", "大学城南", 1060, 696, "2005-12-26", true],
      ["Xinzao", "新造", 1060, 744, "2005-12-26"],
      ["Shiqi", "石碁", 1020, 800, "2006-12-30"],
      ["Haibang", "海傍", 980, 852, "2006-12-30"],
      ["Dichong", "低涌", 940, 900, "2007-12-30"],
      ["Jinzhou", "金洲", 900, 952, "2007-12-30"],
      ["Nansha Pass. Port", "南沙客运港", 860, 1000, "2017-12-28", true],
    ],
  },
  {
    id: "5", name_en: "Line 5", name_zh: "5号线", color: LINE_COLORS['5'], opened: "2009-12-28",
    stations: [
      ["Jiaokou", "滘口", 380, 460, "2009-12-28", true],
      ["Tanwei", "坦尾", 460, 460, "2009-12-28", true],
      ["Zhongshanba", "中山八", 520, 460, "2009-12-28"],
      ["Xicun", "西村", 600, 420, "2009-12-28"],
      ["Guangzhou Rly. Station", "广州火车站", 700, 384, "2009-12-28", true],
      ["Xiaobei", "小北", 760, 384, "2009-12-28"],
      ["Taojin", "淘金", 820, 400, "2009-12-28"],
      ["Yangji", "杨箕", 892, 440, "2009-12-28", true],
      ["Wuyangcun", "五羊邨", 940, 472, "2009-12-28"],
      ["Zhujiang New Town", "珠江新城", 940, 500, "2009-12-28", true],
      ["Liede", "猎德", 980, 540, "2009-12-28"],
      ["Chebei", "车陂", 1100, 472, "2009-12-28"],
      ["Sanxi", "三溪", 1160, 472, "2009-12-28"],
      ["Yuzhu", "鱼珠", 1220, 460, "2009-12-28", true],
      ["Wenchong", "文冲", 1280, 460, "2009-12-28"],
      ["Huangpu New Port", "黄埔新港", 1340, 480, "2022-12-28"],
    ],
  },
  {
    id: "6", name_en: "Line 6", name_zh: "6号线", color: LINE_COLORS['6'], opened: "2013-12-28",
    stations: [
      ["Xunfenggang", "浔峰岗", 380, 300, "2013-12-28", true],
      ["Hengsha", "横沙", 440, 320, "2013-12-28"],
      ["Shabei", "沙贝", 500, 360, "2013-12-28"],
      ["Cultural Park", "文化公园", 640, 520, "2013-12-28"],
      ["Yidelu", "一德路", 680, 500, "2013-12-28"],
      ["Beijing Rd", "北京路", 740, 480, "2013-12-28"],
      ["Tuanyida", "团一大广场", 800, 500, "2013-12-28"],
      ["Dongshankou", "东山口", 844, 440, "2013-12-28", true],
      ["Ouzhuang", "区庄", 880, 400, "2013-12-28", true],
      ["Tianpingjia", "天平架", 940, 300, "2013-12-28"],
      ["Yantang", "燕塘", 980, 280, "2013-12-28", true],
      ["Changban", "长湴", 1040, 280, "2013-12-28"],
      ["Suyuan", "苏元", 1120, 300, "2016-12-28"],
      ["Xiangxue", "香雪", 1220, 340, "2016-12-28", true],
    ],
  },
  {
    id: "7", name_en: "Line 7", name_zh: "7号线", color: LINE_COLORS['7'], opened: "2016-12-28",
    stations: [
      ["Meidi Avenue", "美的大道", 300, 760, "2020-12-28", true],
      ["Beijiao? Foshan", "北滘", 360, 800, "2020-12-28"],
      ["Chencun", "陈村", 420, 820, "2020-12-28"],
      ["Guangzhou South Rly.", "广州南站", 480, 860, "2016-12-28", true],
      ["Shibi", "石壁", 540, 820, "2016-12-28"],
      ["Hanxi Changlong", "汉溪长隆", 800, 856, "2016-12-28", true],
      ["Nancun Wanbo", "南村万博", 920, 800, "2016-12-28"],
      ["Higher Ed. Mega Ctr. S", "大学城南", 1060, 696, "2016-12-28", true],
      ["Shuixi", "水西", 1140, 660, "2023-12-28"],
      ["Luogang? Yanshan", "燕山", 1200, 620, "2023-12-28"],
    ],
  },
  {
    id: "8", name_en: "Line 8", name_zh: "8号线", color: LINE_COLORS['8'], opened: "2010-09-25",
    stations: [
      ["Jiaoxin", "滘心", 560, 240, "2020-11-26", true],
      ["Tongde", "同德", 600, 300, "2020-11-26"],
      ["Cultural Park", "文化公园", 640, 520, "2020-11-26"],
      ["Tongfuxi", "同福西", 680, 560, "2010-09-25"],
      ["Fenghuang Xincun", "凤凰新村", 700, 600, "2010-09-25"],
      ["Changgang", "昌岗", 700, 648, "2010-09-25", true],
      ["Xiaogang", "晓港", 740, 660, "2003-06-28"],
      ["Zhongda", "中大", 800, 660, "2003-06-28"],
      ["Kecun", "客村", 860, 600, "2003-06-28", true],
      ["Pazhou", "琶洲", 980, 600, "2003-06-28", true],
      ["Xingangdong", "新港东", 1020, 580, "2003-06-28"],
      ["Wanshengwei", "万胜围", 1060, 540, "2004-12-26", true],
    ],
  },
  {
    id: "9", name_en: "Line 9", name_zh: "9号线", color: LINE_COLORS['9'], opened: "2017-12-28",
    stations: [
      ["Fei'eling", "飞鹅岭", 460, 120, "2017-12-28"],
      ["Huadu Square", "花都广场", 520, 140, "2017-12-28"],
      ["Guangzhou North Rly.", "广州北站", 580, 160, "2017-12-28", true],
      ["Ma'anshan Park", "马鞍山公园", 640, 180, "2017-12-28"],
      ["Qingtang", "清塘", 680, 200, "2017-12-28"],
      ["Gaozeng", "高增", 700, 220, "2017-12-28", true],
    ],
  },
  {
    id: "10", name_en: "Line 10", name_zh: "10号线", color: LINE_COLORS['10'], opened: "2025-06-29",
    stations: [],
  },
  {
    id: "11", name_en: "Line 11", name_zh: "11号线", color: LINE_COLORS['11'], opened: "2024-12-28",
    stations: [],
  },
  {
    id: "12", name_en: "Line 12", name_zh: "12号线", color: LINE_COLORS['12'], opened: "2025-06-29",
    stations: [],
  },
  {
    id: "13", name_en: "Line 13", name_zh: "13号线", color: LINE_COLORS['13'], opened: "2017-12-28",
    stations: [
      ["Yuzhu", "鱼珠", 1220, 460, "2017-12-28", true],
      ["Nangang", "南岗", 1280, 420, "2017-12-28"],
      ["Xiayuan", "夏园", 1340, 400, "2017-12-28"],
      ["Shacun", "沙村", 1400, 380, "2017-12-28"],
      ["Xinsha", "新沙", 1460, 360, "2017-12-28", true],
    ],
  },
  {
    id: "14", name_en: "Line 14", name_zh: "14号线", color: LINE_COLORS['14'], opened: "2018-12-28",
    stations: [
      ["Dongfeng", "东风", 700, 60, "2018-12-28"],
      ["Conghua Coach Stn.", "从化客运站", 740, 100, "2018-12-28"],
      ["Taiping", "太平", 720, 150, "2018-12-28"],
      ["Zhuliao", "竹料", 700, 180, "2018-12-28"],
      ["Jiahewanggang", "嘉禾望岗", 700, 220, "2018-12-28", true],
      // Knowledge City branch (opened a year earlier)
    ],
    branch: [
      ["Xinhe", "新和", 760, 220, "2017-12-28", true],
      ["Hongwei", "红卫", 840, 220, "2017-12-28"],
      ["Zhenlong", "镇龙", 1000, 240, "2017-12-28", true],
    ],
  },
  {
    id: "21", name_en: "Line 21", name_zh: "21号线", color: LINE_COLORS['21'], opened: "2018-12-28",
    stations: [
      ["Tianhe Park", "天河公园", 1000, 460, "2019-12-20", true],
      ["Yuancun", "员村", 1000, 440, "2019-12-20", true],
      ["Huangcun", "黄村", 1060, 420, "2019-12-20", true],
      ["Suyuan", "苏元", 1120, 300, "2019-12-20"],
      ["Zhenlong", "镇龙", 1000, 240, "2018-12-28", true],
      ["Zhenlongxi", "镇龙西", 1080, 220, "2018-12-28"],
      ["Zhongxin", "中新", 1200, 200, "2018-12-28"],
      ["Zengcheng Square", "增城广场", 1360, 180, "2018-12-28", true],
    ],
  },
  {
    id: "22", name_en: "Line 22", name_zh: "22号线", color: LINE_COLORS['22'], opened: "2022-03-31",
    stations: [],
  },
  {
    id: "18", name_en: "Line 18", name_zh: "18号线", color: LINE_COLORS['18'], opened: "2021-09-28",
    stations: [
      ["Xiancun", "冼村", 960, 520, "2021-09-28", true],
      ["Modiesha", "磨碟沙", 980, 560, "2021-09-28"],
      ["Hengli", "横沥", 880, 760, "2021-09-28"],
      ["Panyu Square", "番禺广场", 800, 940, "2021-09-28", true],
      ["Nansha Hub", "南沙", 760, 990, "2021-09-28"],
      ["Wanqingsha", "万顷沙", 820, 1020, "2021-09-28"],
    ],
  },
  {
    id: "APM", name_en: "APM Line", name_zh: "APM线", color: LINE_COLORS['APM'], opened: "2010-11-08",
    stations: [
      ["Linhexi", "林和西", 940, 400, "2010-11-08", true],
      ["Tianhe Sports Ctr. S", "体育中心南", 940, 420, "2010-11-08"],
      ["Huangpu Ave.", "黄埔大道", 960, 460, "2010-11-08"],
      ["Zhujiang New Town", "珠江新城", 940, 500, "2010-11-08", true],
      ["Huacheng Avenue", "花城大道", 920, 540, "2010-11-08"],
      ["Canton Tower", "广州塔", 900, 600, "2010-11-08", true],
    ],
  },
  {
    id: "GF", name_en: "Guangfo Line", name_zh: "广佛线", color: LINE_COLORS['GF'], opened: "2010-11-03",
    stations: [
      ["Xincheng East", "新城东", 180, 600, "2016-12-28", true],
      ["Kuiqi Road", "魁奇路", 220, 560, "2010-11-03", true],
      ["Zumiao", "祖庙", 200, 500, "2010-11-03"],
      ["Guicheng", "桂城", 240, 540, "2010-11-03"],
      ["Longxi", "龙溪", 280, 560, "2010-11-03"],
      ["Xilang", "西塱", 300, 560, "2010-11-03", true],
      ["Shayuan", "沙园", 640, 600, "2018-12-28", true],
      ["Lijiao", "沥滘", 820, 720, "2018-12-28", true],
    ],
  },
];

// ---- Notable network events for the timeline track ----
export const EVENTS = [
  { date: "1997-06-28", title: "Line 1 opens", detail: "Xilang – Huangsha. The Guangzhou Metro begins." },
  { date: "1999-06-28", title: "Line 1 completed", detail: "Extended through the city to Guangzhou East Railway Station." },
  { date: "2002-12-29", title: "Line 2 opens", detail: "Sanyuanli – Xiaogang, the first north–south corridor." },
  { date: "2005-12-26", title: "Lines 3 & 4 open", detail: "The Y-shaped Line 3 and linear-motor Line 4 enter service." },
  { date: "2006-12-30", title: "Line 3 & 4 extended south", detail: "Reach Panyu Square and the southern districts." },
  { date: "2009-12-28", title: "Line 5 opens", detail: "Jiaokou – Wenchong, an east–west trunk line." },
  { date: "2010-09-25", title: "Line 2 / 8 reorganised", detail: "Line 2 re-routed; its southern arm becomes Line 8." },
  { date: "2010-11-08", title: "APM Line opens", detail: "Automated people mover through Zhujiang New Town." },
  { date: "2013-12-28", title: "Line 6 opens", detail: "Xunfenggang – Changban across the dense core." },
  { date: "2016-12-28", title: "Lines 6 & 7 extended / open", detail: "Line 7 opens; Line 6 reaches Xiangxue." },
  { date: "2017-12-28", title: "Lines 9, 13, 14-branch open", detail: "A single day adds three new corridors." },
  { date: "2018-12-28", title: "Lines 14 & 21 open", detail: "Reaching Conghua and Zengcheng in the far north-east." },
  { date: "2021-09-28", title: "Line 18 express opens", detail: "160 km/h service toward Nansha." },
  { date: "2022-03-31", title: "Line 22 express opens", detail: "Second 160 km/h express line opens: Chentougang – Panyu Square." },
  { date: "2022-12-28", title: "Line 5 east extension", detail: "Extended to Huangpu New Port." },
  { date: "2023-12-28", title: "Line 7 east extension", detail: "Phase 2 reaches Yanshan in Huangpu district." },
  { date: "2024-11-01", title: "Line 3 extended east", detail: "New section from Panyu Square to Haibang in the south." },
  { date: "2024-12-28", title: "Line 11 loop opens", detail: "Guangzhou's first circular line completes. Tianhe Park – Yuancun transferred from Line 21." },
  { date: "2025-06-29", title: "Lines 10 & 12 open", detail: "Line 10 (Xilang – Yangji East) and Line 12 (Xunfenggang – Higher Ed Mega Center South) launch." },
  { date: "2025-09-29", title: "Lines 13 & 14 extended", detail: "Line 13 Phase 2 (Tianhe Park – Yuzhu) and Line 14 Phase 2 (toward Guangzhou Railway Station) open." },
  { date: "2025-12-29", title: "Line 22 Phase 2", detail: "Express line extended west: Fangcun – Chentougang section opens." },
];

// All dated milestones, ascending — used to compute the open network at any date.
export function allDates() {
  const s = new Set();
  for (const ln of LINES) {
    for (const st of ln.stations) s.add(st[4]);
    if (ln.branch) for (const st of ln.branch) s.add(st[4]);
  }
  return [...s].sort();
}
