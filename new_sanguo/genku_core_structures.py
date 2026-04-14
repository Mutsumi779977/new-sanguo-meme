"""
梗核心结构标注 + 使用示例库 v2.0

核心原则：
- 固定部分（不可动）：保持梗的辨识度
- ## 表示可替换内容（中间可以是其他字/词）
- 槽位标注格式：[槽位名] 或 ###（表示任意长度可替换）

特殊规则：
- xsg_gy_001: 如果前文出现 lb_005（扎聋），则匹配"聋"；否则找"long"音的字
- xsg_gs_001: 数量对偶规则（一对X，两头Y）
"""
from typing import Dict, List


# 梗ID -> 核心结构
GENKU_CORE_STRUCTURES: Dict[str, Dict] = {
    # ========== Meta梗 ==========
    "xsg_meta_001": {
        "fixed": ["列位诸公"],
        "variables": [],
        "structure": "称呼开场",
        "usage_examples": [
            {
                "user_situation": "对方在群里无礼/装逼",
                "usage": "开场警告",
                "template": "列位诸公，如果你们容得下[对象]在此放肆，那就容我告老还乡了"
            }
        ]
    },
    "xsg_meta_002": {
        "fixed": ["天意"],
        "variables": [],
        "structure": "感叹宿命",
        "usage_examples": [{"user_situation": "事情无法改变", "usage": "甩锅给天意"}]
    },
    "xsg_meta_003": {
        "fixed": ["从这一刻起", "历史发生了剧变"],
        "variables": [],
        "structure": "宣告重大变化",
        "usage_examples": [{"user_situation": "某重大事件发生", "usage": "夸张宣告"}]
    },
    "xsg_meta_004": {
        "fixed": ["##爷"],
        "variables": ["称呼"],
        "structure": "尊称格式",
        "usage_examples": [{"user_situation": "称呼某人", "usage": "加爷表示尊敬"}],
        "note": "合并了xsg_zf_003"
    },
    "xsg_meta_005": {
        "fixed": ["叉出去"],
        "variables": [],
        "structure": "命令驱逐",
        "usage_examples": [{"user_situation": "不想理某人/对方说傻话", "usage": "直接驱逐"}]
    },
    "xsg_meta_006": {
        "fixed": ["事不过三"],
        "variables": [],
        "structure": "定律宣告",
        "usage_examples": [{"user_situation": "某事重复出现", "usage": "提醒次数限制"}]
    },
    
    # ========== 曹操 ==========
    "xsg_cc_001": {
        "fixed": ["不是", "害了你", "是", "害了你"],
        "variables": ["对象", "环境"],
        "structure": "甩锅句式：不是A是B",
        "usage_examples": [{"user_situation": "需要甩锅/辩解", "usage": "转移责任到环境"}]
    },
    "xsg_cc_002": {
        "fixed": ["不可能", "绝对不可能"],
        "variables": [],
        "structure": "递进式否认",
        "usage_examples": [{"user_situation": "听到震惊消息", "usage": "表达难以置信"}],
        "related": "xsg_cc_018 (动作名场面)",
        "note": "与xsg_cc_018(曹操盖饭)是不同用法：002是语言递进否认，018是动作表情"
    },
    "xsg_cc_003": {
        "fixed": ["不要", "会降低你的智慧"],
        "variables": ["情绪"],
        "structure": "劝诫句式：不要做X，X会降低智慧",
        "usage_examples": [{"user_situation": "被惹生气了", "usage": "自我克制/劝人冷静"}]
    },
    "xsg_cc_004": {
        "fixed": ["你##了", "我们##什么"],
        "variables": ["动作A", "动作B"],
        "structure": "吃货式挽留",
        "usage_examples": [{"user_situation": "某人要走", "usage": "幽默挽留"}]
    },
    "xsg_cc_005": {
        "fixed": ["死不可怕，死是凉爽的夏夜，可供人无忧地安眠"],
        "variables": [],
        "structure": "诗意比喻生死",
        "usage_examples": [{"user_situation": "谈论生死", "usage": "豁达表达"}]
    },
    "xsg_cc_006": {
        "fixed": ["越多", "越高明"],
        "variables": ["行为", "评价标准"],
        "structure": "反讽：越多越高明",
        "usage_examples": [{"user_situation": "吐槽某行业乱象", "usage": "反讽"}]
    },
    "xsg_cc_007": {
        "fixed": ["只要", "一息尚存", "他就"],
        "variables": ["人物", "能力"],
        "structure": "自信宣言",
        "usage_examples": [{"user_situation": "给自己打气", "usage": "立flag"}]
    },
    "xsg_cc_008": {
        "fixed": ["孩儿对不住你了", "呱"],
        "variables": [],
        "structure": "假哭+青蛙叫",
        "usage_examples": [{"user_situation": "假意道歉", "usage": "搞笑哭丧"}]
    },
    "xsg_cc_009": {
        "fixed": ["何等人物", "只要", "在手", "他马上会"],
        "variables": ["对象", "条件", "结果"],
        "structure": "先抑后扬夸赞",
        "usage_examples": [{"user_situation": "夸赞某人能力", "usage": "夸张肯定"}]
    },
    "xsg_cc_010": {
        "fixed": ["是谁啊", "是我的"],
        "variables": ["对象", "夸张类比"],
        "structure": "尬吹介绍",
        "usage_examples": [{"user_situation": "介绍某人", "usage": "夸张类比"}]
    },
    "xsg_cc_011": {
        "fixed": ["一把叫", "一把叫"],
        "variables": ["名称A", "名称B"],
        "structure": "强行解读命名",
        "usage_examples": [{"user_situation": "解读某物", "usage": "胡说式解读"}]
    },
    "xsg_cc_012": {
        "fixed": ["不准", "务必"],
        "variables": ["禁止行为", "强制行为"],
        "structure": "军事命令",
        "usage_examples": [{"user_situation": "下命令", "usage": "强调执行"}]
    },
    "xsg_cc_013": {
        "fixed": ["教出来的都是呆子"],
        "variables": ["被教对象"],
        "structure": "否定贬低",
        "usage_examples": [{"user_situation": "否定某教育方式", "usage": "直接贬低"}]
    },
    "xsg_cc_015": {
        "fixed": ["此####，不可不尝，快给###送去"],
        "variables": ["物品", "形容词", "人物"],
        "structure": "强行安利",
        "usage_examples": [{"user_situation": "推荐某物", "usage": "热情安利"}]
    },
    "xsg_cc_016": {
        "fixed": ["就算是八万个馒头，刘备也得啃上半个月"],
        "variables": [],
        "structure": "夸张类比",
        "usage_examples": [{"user_situation": "吐槽效率", "usage": "夸张对比"}]
    },
    "xsg_cc_018": {
        "fixed": ["曹操盖饭"],
        "variables": [],
        "structure": "动作名场面（物理震惊）",
        "usage_examples": [{"user_situation": "震惊/无语", "usage": "表达崩溃"}],
        "related": "xsg_cc_002 (递进否认)",
        "note": "与xsg_cc_002关联：002是语言上的'不可能'，018是动作上的'震惊'"
    },
    "xsg_cc_019": {
        "fixed": ["我原本以为", "已经天下无敌了", "没想到", "比他还", "这是谁的部将"],
        "variables": ["基准对象", "超越对象", "形容词"],
        "structure": "递进式赞扬",
        "usage_examples": [{"user_situation": "看到更强的", "usage": "递进夸奖"}]
    },
    "xsg_cc_020": {
        "fixed": ["魏武挥鞭"],
        "variables": [],
        "structure": "动作/现象描述（非完整句子）",
        "usage_examples": [{"user_situation": "描述曹操", "usage": "文学化表达"}],
        "note": "这不是一句话，是一个动作/现象描述，属于角色模式"
    },
    "xsg_cc_021": {
        "fixed": ["二言绝句"],
        "variables": [],
        "structure": "讽刺诗词水平",
        "usage_examples": [{"user_situation": "吐槽文采", "usage": "讽刺"}]
    },
    "xsg_cc_022": {
        "fixed": ["昨日看错", "今日又看错", "也许明日还会看错", "可我仍然是我", "不怕别人看错"],
        "variables": ["人物"],
        "structure": "排比式自白",
        "usage_examples": [{"user_situation": "被误解", "usage": "坚持自我"}]
    },
    "xsg_cc_023": {
        "fixed": ["差点没把我笑死"],
        "variables": [],
        "structure": "夸张反应",
        "usage_examples": [{"user_situation": "看到好笑的事", "usage": "表达好笑"}]
    },
    "xsg_cc_024": {
        "fixed": ["听你讲话", "如饮美酒", "令人陶醉"],
        "variables": [],
        "structure": "讽刺式夸奖",
        "usage_examples": [{"user_situation": "对方说得好", "usage": "文雅赞同"}]
    },
    "xsg_cc_025": {
        "fixed": ["好方略", "不过我想稍作修改"],
        "variables": [],
        "structure": "先赞后改",
        "usage_examples": [{"user_situation": "对方提建议", "usage": "礼貌修改"}]
    },
    
    # ========== 刘备 ==========
    "xsg_lb_001": {
        "fixed": ["接着奏乐", "接着舞"],
        "variables": [],
        "structure": "重复享受",
        "usage_examples": [{"user_situation": "享受时光", "usage": "继续玩乐"}]
    },
    "xsg_lb_002": {
        "fixed": ["我打了一辈子仗", "就不能", "享受享受吗"],
        "variables": ["付出", "享受"],
        "structure": "反问式抱怨",
        "usage_examples": [{"user_situation": "想放松", "usage": "理直气壮休息"}]
    },
    "xsg_lb_003": {
        "fixed": ["不可能", "天下无敌"],
        "variables": ["对象"],
        "structure": "护短否认",
        "usage_examples": [{"user_situation": "听到坏消息", "usage": "拒绝接受"}]
    },
    "xsg_lb_004": {
        "fixed": ["战至最后一刻", "自刎归天"],
        "variables": [],
        "structure": "壮烈宣言",
        "usage_examples": [{"user_situation": "表示决心", "usage": "立flag"}]
    },
    "xsg_lb_005": {
        "fixed": ["我再听到你们议论###，我就扎聋我自己的耳朵"],
        "variables": ["人或事"],
        "structure": "自残式威胁",
        "usage_examples": [{"user_situation": "不想听某话题", "usage": "夸张拒绝"}]
    },
    "xsg_lb_006": {
        "fixed": ["风从虎", "云从龙", "英雄傲苍穹"],
        "variables": [],
        "structure": "诗意对仗",
        "usage_examples": [{"user_situation": "描述英雄", "usage": "文艺表达"}]
    },
    "xsg_lb_007": {
        "fixed": ["放肆", "敢", "我砍你的头"],
        "variables": ["冒犯行为"],
        "structure": "愤怒威胁",
        "usage_examples": [{"user_situation": "被冒犯", "usage": "强势反击"}]
    },
    "xsg_lb_008": {
        "fixed": ["多谢", "大恩", "给你叩首了"],
        "variables": ["对象"],
        "structure": "夸张感谢",
        "usage_examples": [{"user_situation": "感谢帮助", "usage": "过度致谢"}]
    },
    
    # ========== 关羽 ==========
    "xsg_gy_001": {
        "fixed": ["可是帝王之征啊"],
        "variables": ["征兆"],
        "structure": "过度解读",
        "usage_examples": [{"user_situation": "解读某现象", "usage": "上升高度"}],
        "special_rule": "如果前文出现lb_005(扎聋)，则匹配'聋'字；否则找'long'音的字。例如'鸡兔同笼'→'笼，可是帝王之征啊'"
    },
    "xsg_gy_002": {
        "fixed": ["说得痛切", "当浮一大白"],
        "variables": ["说话者"],
        "structure": "文雅认同",
        "usage_examples": [{"user_situation": "同意某观点", "usage": "文雅附和"}]
    },
    "xsg_gy_003": {
        "fixed": ["不斩"],
        "variables": ["武器", "对象特征"],
        "structure": "选择性原则（装逼）",
        "usage_examples": [{"user_situation": "选择性执行", "usage": "设定例外"}],
        "feature": "装逼特征"
    },
    
    # ========== 张飞 ==========
    "xsg_zf_001": {
        "fixed": ["我看你是舍不得", "吧"],
        "variables": ["物品"],
        "structure": "点破小心思",
        "usage_examples": [{"user_situation": "对方舍不得", "usage": "直接点破"}]
    },
    "xsg_zf_002": {
        "fixed": ["快去叫###出来##，我###前来##了"],
        "variables": ["人物", "动作A", "自称/人物", "行为"],
        "structure": "高调通报",
        "usage_examples": [{"user_situation": "高调出场", "usage": "夸张通报"}]
    },
    # xsg_zf_003 已合并到 xsg_meta_004
    "xsg_zf_004": {
        "fixed": ["这说两句就行了", "谁知道", "听得见听不见"],
        "variables": ["对象"],
        "structure": "吐槽形式主义",
        "usage_examples": [{"user_situation": "吐槽表面功夫", "usage": "讽刺"}]
    },
    "xsg_zf_005": {
        "fixed": ["捅他", "一万个", "透明窟窿"],
        "variables": ["对象"],
        "structure": "夸张威胁",
        "usage_examples": [{"user_situation": "放狠话", "usage": "夸张威胁"}]
    },
    
    # ========== 诸葛亮 ==========
    "xsg_zgl_001": {
        "fixed": ["你#它作甚", "你今天###", "他明天还要来##的"],
        "variables": ["单字动作", "三字动作", "两字动词"],
        "structure": "长远考虑",
        "usage_examples": [{"user_situation": "对方纵容", "usage": "指出后果"}]
    },
    "xsg_zgl_002": {
        "fixed": ["好#啊", "比####还好"],
        "variables": ["形容词/名词", "类比事件"],
        "structure": "讽刺式对比",
        "usage_examples": [
            {"user_situation": "讽刺某事", "usage": "对比嘲讽"},
            {"user_situation": "帖子/话题热度高", "usage": "用'火'指热度"}
        ],
        "note": "'火'可指物理火，也可指帖子/话题热度"
    },
    
    # ========== 孙策 ==========
    "xsg_sc_001": {
        "fixed": ["恭喜###，可以撑地了！"],
        "variables": ["人物"],
        "structure": "讽刺祝贺",
        "usage_examples": [{"user_situation": "对方装逼", "usage": "阴阳怪气祝贺"}]
    },
    "xsg_sc_002": {
        "fixed": ["我上表", "让他", "的事情", "已经回消息了", "竟然不许"],
        "variables": ["对象", "请求", "结果"],
        "structure": "告状式吐槽",
        "usage_examples": [{"user_situation": "申请被拒", "usage": "委屈吐槽"}],
        "note": "不一定是针对上级，平级也可以使用（开玩笑形式）"
    },
    
    # ========== 孙权 ==========
    "xsg_sq_001": {
        "fixed": ["这", "到底你是主", "还是我是主"],
        "variables": ["领域"],
        "structure": "主权质问",
        "usage_examples": [{"user_situation": "被越权", "usage": "强调主权"}]
    },
    
    # ========== 王允 ==========
    "xsg_wr_001": {
        "fixed": ["生死不明", "那就是死了"],
        "variables": [],
        "structure": "二极管推理",
        "usage_examples": [{"user_situation": "推测结果", "usage": "极端推断"}],
        "extended_rule": "好坏不明，那就是坏了（好坏指事情发展方向）"
    },
    "xsg_wr_002": {
        "fixed": ["今天不是####", "相反", "是####啊"],
        "variables": ["事件A", "事件B"],
        "structure": "反转宣告",
        "usage_examples": [{"user_situation": "两件事情相反", "usage": "反转说明"}]
    },
    
    # ========== 董卓 ==========
    "xsg_dz_001": {
        "fixed": ["咱家说了咱家不怕#", "不怕！"],
        "variables": ["事情"],
        "structure": "硬撑式回应",
        "usage_examples": [
            {"user_situation": "面对困难", "usage": "强撑面子"},
            {"user_situation": "不怕deadline", "usage": "咱家说了咱家不怕deadline，不怕！"}
        ]
    },
    "xsg_dz_002": {
        "fixed": ["咱家是上天遣下来的##"],
        "variables": ["身份/职位"],
        "structure": "天命宣告",
        "usage_examples": [{"user_situation": "装逼", "usage": "强调身份"}],
        "weight": 2
    },
    "xsg_dz_003": {
        "fixed": ["##的命苦啊", "##是天底下命最苦的人", "苦得就像是车轮里的野草", "我苦得就像是", "石头缝里的黄连哪"],
        "variables": ["人称"],
        "structure": "卖惨哭诉",
        "usage_examples": [{"user_situation": "抱怨命苦", "usage": "夸张卖惨"}],
        "weight": 3
    },
    
    # ========== 公孙瓒 ==========
    "xsg_gs_001": {
        "fixed": ["一对##", "两头##"],
        "variables": ["形象A", "形象B"],
        "structure": "数量对偶讽刺",
        "usage_examples": [{"user_situation": "吐槽两人", "usage": "对偶讽刺"}],
        "rule": "数量对偶：一对X，两头Y"
    },
    
    # ========== 袁术 ==========
    "xsg_ys_001": {
        "fixed": ["还是个忠厚人啊"],
        "variables": ["对象"],
        "structure": "反讽评价",
        "usage_examples": [{"user_situation": "对方不厚道", "usage": "反讽"}]
    },
    "xsg_ys_002": {
        "fixed": ["列位诸公", "如果你们能容得下", "在这里肆意放肆", "那就容我", "告老还乡了"],
        "variables": ["对象", "自称"],
        "structure": "傲娇威胁",
        "usage_examples": [{"user_situation": "受不了某人", "usage": "威胁退出"}]
    },
    
    # ========== 荀彧 ==========
    "xsg_xy_001": {
        "fixed": ["##", "败报到了"],
        "variables": ["称呼"],
        "structure": "坏消息通报",
        "usage_examples": [{"user_situation": "报告失败", "usage": "委婉通报"}]
    },
    "xsg_xy_002": {
        "fixed": ["你知道吗", "喜欢的", "跟你喜欢的不一样"],
        "variables": [],
        "structure": "点破差异",
        "usage_examples": [{"user_situation": "提醒差异", "usage": "委婉指出"}]
    },
    "xsg_xy_003": {
        "fixed": ["不愧为", "第一"],
        "variables": ["地点", "属性"],
        "structure": "夸张赞美",
        "usage_examples": [{"user_situation": "夸赞某地", "usage": "夸张表扬"}]
    },
    
    # ========== 陈宫 ==========
    "xsg_cg_001": {
        "fixed": ["我在想我的那些个", "它们个个"],
        "variables": ["物品", "属性"],
        "structure": "借物喻人",
        "usage_examples": [{"user_situation": "吐槽人不如物", "usage": "对比讽刺"}]
    },
    "xsg_cg_002": {
        "fixed": ["只当我", "从来就没有这些"],
        "variables": ["人物", "事物"],
        "structure": "断绝关系",
        "usage_examples": [{"user_situation": "失望透顶", "usage": "一刀两断"}]
    },
    
    # ========== 司马懿 ==========
    "xsg_smy_001": {
        "fixed": ["全军冲杀####", "直奔###（人）###（该人的物）"],
        "variables": ["目标地点", "人物", "人物相关物品"],
        "structure": "战术指令",
        "usage_examples": [{"user_situation": "明确目标", "usage": "直接命令"}]
    },
    
    # ========== 邢道荣 ==========
    "xsg_xdr_001": {
        "fixed": ["说出吾名", "吓汝一跳"],
        "variables": [],
        "structure": "自夸开场",
        "usage_examples": [{"user_situation": "自我介绍", "usage": "装逼开场"}]
    },
    
    # ========== 徐庶 ==========
    "xsg_xs_001": {
        "fixed": ["与其", "不如为自己", "一个"],
        "variables": ["被动行为", "主动创造"],
        "structure": "主动创造哲学",
        "usage_examples": [{"user_situation": "鼓励主动", "usage": "转变思路"}]
    },
    
    # ========== 马超 ==========
    "xsg_mc_001": {
        "fixed": ["奸贼", "恶贼", "逆贼"],
        "variables": ["对象"],
        "structure": "同义词堆叠辱骂",
        "usage_examples": [{"user_situation": "愤怒辱骂", "usage": "叠词输出"}]
    },
    
    # ========== 曹丕 ==========
    "xsg_gen_001": {
        "fixed": ["岂能"],
        "variables": ["现状", "等待"],
        "structure": "反问否定",
        "usage_examples": [{"user_situation": "等不及", "usage": "表达急迫"}]
    },
    
    # ========== 潘凤 ==========
    "xsg_pf_001": {
        "fixed": ["我的", "早已饥渴难耐了"],
        "variables": ["武器"],
        "structure": "战前宣言",
        "usage_examples": [{"user_situation": "准备行动", "usage": "蓄势待发"}]
    },
    
    # ========== 郭嘉 ==========
    "xsg_gj_001": {
        "fixed": ["之后", "也就随之"],
        "variables": ["事件", "贬值对象"],
        "structure": "连锁贬值",
        "usage_examples": [{"user_situation": "分析连锁反应", "usage": "指出贬值"}]
    },
    
    # ========== 程普 ==========
    "xsg_cp_001": {
        "fixed": ["我听后大惊", "却不敢相信"],
        "variables": [],
        "structure": "震惊怀疑",
        "usage_examples": [{"user_situation": "震惊消息", "usage": "难以置信"}]
    },
}


def get_genku_core(genku_id: str) -> Dict:
    """获取梗的核心结构"""
    return GENKU_CORE_STRUCTURES.get(genku_id, {
        "fixed": [],
        "variables": [],
        "structure": "未标注",
        "usage_examples": []
    })
