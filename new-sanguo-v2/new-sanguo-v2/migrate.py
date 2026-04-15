#!/usr/bin/env python3
"""
新三国梗数据迁移脚本 v2.0
将旧格式 YAML 转换为新格式（带权重和语义关键词）
"""

import yaml
import re
from datetime import datetime

# 完整的梗数据映射表（54条）
MEME_DATA = {
    # 元梗 (4条)
    "sg_meta_001": {"new_id": "xsg_meta_001", "weight": 5, "keywords": ["各位", "大家", "在场诸公", "开场白"]},
    "sg_meta_002": {"new_id": "xsg_meta_002", "weight": 5, "keywords": ["命运", "历史", "上天"]},
    "sg_meta_003": {"new_id": "xsg_meta_003", "weight": 3, "keywords": ["历史转折", "剧变", "重大改变", "历史分叉"]},
    "xx_ye_template": {"new_id": "xsg_meta_004", "weight": 5, "keywords": ["称呼", "尊敬", "元梗", "主子爷", "先帝爷"]},
    
    # 曹操梗 (13条)
    "sg_cao_002": {"new_id": "xsg_cc_001", "weight": 5, "keywords": ["害人", "乱世", "甩锅"]},
    "sg_cao_004": {"new_id": "xsg_cc_002", "weight": 4, "keywords": ["震惊", "否认", "难以置信", "不可能"]},
    "sg_cao_014": {"new_id": "xsg_cc_003", "weight": 3, "keywords": ["冷静", "劝解", "别生气", "智慧"]},
    "sg_cao_003": {"new_id": "xsg_cc_004", "weight": 5, "keywords": ["挽留", "吃货", "别走", "吃什么"]},
    "sg_cao_008": {"new_id": "xsg_cc_005", "weight": 5, "keywords": ["死", "死亡", "安眠", "豁达", "夏夜"]},
    "sg_cao_006": {"new_id": "xsg_cc_006", "weight": 4, "keywords": ["歪理", "医生", "经验", "医术"]},
    "sg_cao_007": {"new_id": "xsg_cc_007", "weight": 1, "keywords": ["自信", "霸气", "战无不胜", "一息尚存"]},
    "sg_cao_011": {"new_id": "xsg_cc_008", "weight": 2, "keywords": ["假哭", "道歉", "呱"]},
    "sg_cao_013": {"new_id": "xsg_cc_009", "weight": 2, "keywords": ["夸赞", "忌惮", "能力强", "孔明"]},
    "sg_cao_005": {"new_id": "xsg_cc_010", "weight": 3, "keywords": ["尬吹", "乱夸", "历史人物", "韩信", "白起"]},
    "sg_cao_009": {"new_id": "xsg_cc_011", "weight": 5, "keywords": ["仁", "义", "双股剑", "强行解读"]},
    "sg_cao_010": {"new_id": "xsg_cc_012", "weight": 1, "keywords": ["生擒", "抓活的", "命令", "放箭"]},
    "sg_cao_012": {"new_id": "xsg_cc_013", "weight": 4, "keywords": ["否定", "经典", "胡说", "兵法呆子", "春秋"]},
    
    # 刘备梗 (8条)
    "sg_liu_006": {"new_id": "xsg_lb_001", "weight": 3, "keywords": ["庆祝", "享受", "嗨起来", "奏乐", "舞"]},
    "sg_liu_007": {"new_id": "xsg_lb_002", "weight": 2, "keywords": ["辛苦", "享受", "委屈", "一辈子仗"]},
    "sg_liu_004": {"new_id": "xsg_lb_003", "weight": 3, "keywords": ["护短", "盲目自信", "二弟", "天下无敌"]},
    "sg_liu_002": {"new_id": "xsg_lb_004", "weight": 5, "keywords": ["拼命", "死战", "决绝", "自刎", "战至最后"]},
    "sg_liu_005": {"new_id": "xsg_lb_005", "weight": 5, "keywords": ["护短", "议论", "扎聋", "诸葛亮", "孔明"]},
    "sg_liu_003": {"new_id": "xsg_lb_006", "weight": 4, "keywords": ["尬诗", "装逼", "中二", "龙虎", "风从虎"]},
    "sg_liu_008": {"new_id": "xsg_lb_007", "weight": 2, "keywords": ["愤怒", "威严", "被质疑", "搜身", "放肆"]},
    "sg_liu_009": {"new_id": "xsg_lb_008", "weight": 1, "keywords": ["感谢", "夸张", "叩首", "大恩", "子敬"]},
    
    # 关羽梗 (3条)
    "sg_guan_002": {"new_id": "xsg_gy_001", "weight": 5, "keywords": ["龙", "聋", "long音", "接梗", "帝王之征"]},
    "sg_guan_003": {"new_id": "xsg_gy_002", "weight": 4, "keywords": ["赞同", "说得好", "喝酒", "浮一大白", "痛切"]},
    "sg_guan_004": {"new_id": "xsg_gy_003", "weight": 1, "keywords": ["武德", "不杀", "老幼", "讲武德", "大刀"]},
    
    # 张飞梗 (4条)
    "sg_zhang_002": {"new_id": "xsg_zf_001", "weight": 2, "keywords": ["揭穿", "舍不得", "权位", "借口", "帅案"]},
    "sg_zhang_004": {"new_id": "xsg_zf_002", "weight": 2, "keywords": ["装逼", "入场", "嚣张", "接驾", "会盟"]},
    "sg_zhang_003": {"new_id": "xsg_zf_003", "weight": 5, "keywords": ["称呼", "尊敬", "主子爷", "先帝爷"]},  # 合并到元梗
    "zhangfei_xian": {"new_id": "xsg_zf_004", "weight": 4, "keywords": ["说两句", "废话", "听不见", "过度表达", "先帝爷"]},
    
    # 诸葛亮梗 (2条)
    "sg_zhu_003": {"new_id": "xsg_zgl_001", "weight": 3, "keywords": ["受气", "诸葛小姐", "硬气", "不捡", "拾它作甚"]},
    "sg_zhu_002": {"new_id": "xsg_zgl_002", "weight": 3, "keywords": ["火", "烧", "热度", "专业", "夷陵之火"]},
    
    # 孙策梗 (2条)
    "sg_sun_001": {"new_id": "xsg_sc_001", "weight": 5, "keywords": ["恭喜", "称帝", "拱火", "撑地", "爹"]},
    "sg_sun_002": {"new_id": "xsg_sc_002", "weight": 4, "keywords": ["申请", "被拒", "竟然不许", "委屈", "上表"]},
    
    # 孙权梗 (1条)
    "sg_sun_003": {"new_id": "xsg_sq_001", "weight": 2, "keywords": ["权威", "质问", "听谁的", "做主", "江东"]},
    
    # 王允梗 (2条)
    "sg_wang_001": {"new_id": "xsg_wr_001", "weight": 5, "keywords": ["失踪", "死了", "毒奶", "flag", "生死不明"]},
    "sg_wang_002": {"new_id": "xsg_wr_002", "weight": 3, "keywords": ["生日", "倒霉", "忌日", "反转"]},
    
    # 董卓梗 (1条)
    "sg_dong_001": {"new_id": "xsg_dz_001", "weight": 3, "keywords": ["酸", "逞强", "嘴硬", "吃醋", "咱家"]},
    
    # 公孙瓒梗 (1条)
    "sg_gong_001": {"new_id": "xsg_gs_001", "weight": 5, "keywords": ["两面三刀", "伪君子", "跳跳虎", "脆脆鲨", "笑面虎"]},
    
    # 袁术梗 (1条)
    "sg_yuan_001": {"new_id": "xsg_ys_001", "weight": 3, "keywords": ["忠厚", "看走眼", "讽刺", "xx爷"]},
    
    # 荀彧梗 (3条)
    "sg_xun_002": {"new_id": "xsg_xy_001", "weight": 1, "keywords": ["坏消息", "败报", "直接", "到了"]},
    "sg_xun_003": {"new_id": "xsg_xy_002", "weight": 2, "keywords": ["委婉", "提醒", "喜好", "不一样", "女人"]},
    "sg_xun_001": {"new_id": "xsg_xy_003", "weight": 4, "keywords": ["硬吹", "尬吹", "地理错误", "不懂装懂", "雄关"]},
    
    # 陈宫梗 (1条)
    "sg_chen_001": {"new_id": "xsg_cg_001", "weight": 3, "keywords": ["蛐蛐", "有情有义", "人不如蛐蛐"]},
    
    # 司马懿梗 (1条)
    "sg_sim_001": {"new_id": "xsg_smy_001", "weight": 2, "keywords": ["冲杀", "四轮车", "执着", "抓", "蜀军"]},
    
    # 邢道荣梗 (1条)
    "sg_xing_002": {"new_id": "xsg_xdr_001", "weight": 2, "keywords": ["装逼", "报名", "狂妄", "自我介绍", "吓你一跳"]},
    
    # 徐庶梗 (1条)
    "sg_xu_001": {"new_id": "xsg_xs_001", "weight": 4, "keywords": ["创业", "培养", "养成", "自己创造", "主公"]},
    
    # 马超梗 (1条)
    "sg_ma_001": {"new_id": "xsg_mc_001", "weight": 2, "keywords": ["骂人", "愤怒", "重复", "四字", "曹贼"]},
    
    # 通用梗 (2条)
    "sg_generic_001": {"new_id": "xsg_gen_001", "weight": 1, "keywords": ["焦急", "时间", "等不及", "年龄", "四旬"]},
    "sg_generic_002": {"new_id": "xsg_gen_002", "weight": 4, "keywords": ["硬夸", "才华", "错误", "空耳", "伯牙子期"]},
}

def parse_old_yaml(filepath):
    """解析旧格式 YAML"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割多个文档
    docs = list(yaml.safe_load_all(content))
    return [doc for doc in docs if doc and '梗ID' in doc]

def extract_variant_info(genku):
    """提取变体模板信息"""
    template = ""
    var_desc = {}
    
    # 从使用模式中提取
    usage = genku.get('使用模式', {})
    rules = usage.get('变体规则', {})
    
    if '模板' in rules:
        template = rules['模板']
        # 转换旧模板格式到新格式
        template = template.replace("'XX'", "[对象]").replace("'YY'", "[属性]")
    
    # 提取变量说明
    if '变量' in rules:
        for var_name, desc in rules['变量'].items():
            var_desc[var_name] = desc
    
    return template, var_desc

def convert_to_new_format(old_genku, meme_info):
    """转换为新格式"""
    old_id = old_genku.get('梗ID', '')
    
    # 获取新ID和权重
    info = meme_info.get(old_id, {})
    new_id = info.get('new_id', old_id)
    weight = info.get('weight', 3)
    keywords = info.get('keywords', [])
    
    # 提取变体信息
    template, var_desc = extract_variant_info(old_genku)
    
    # 构建新格式
    new_genku = {
        '梗ID': new_id,
        '原文': old_genku.get('原文', ''),
        '人物': old_genku.get('人物', ''),
        '出处': old_genku.get('出处', ''),
        '情境': old_genku.get('情境', ''),
        '情绪': old_genku.get('情绪', []),
        '权重': weight,
        '语义关键词': keywords,
        '场景标签': old_genku.get('标签', []),
    }
    
    # 添加变体模板（如果有）
    if template:
        new_genku['变体模板'] = template
        if var_desc:
            new_genku['变量说明'] = var_desc
    
    # 添加元数据
    new_genku['引用频次'] = 0
    new_genku['effectiveness'] = 0.0
    new_genku['录入时间'] = datetime.now().strftime('%Y-%m-%d')
    
    return new_genku

def main():
    # 读取旧数据
    old_file = '../new-sanguo/data/genku.yaml'
    old_genkus = parse_old_yaml(old_file)
    
    print(f"读取到 {len(old_genkus)} 条旧数据")
    
    # 转换
    new_genkus = []
    skipped = []
    
    for old in old_genkus:
        old_id = old.get('梗ID', '')
        if old_id in MEME_DATA:
            new_genku = convert_to_new_format(old, MEME_DATA)
            new_genkus.append(new_genku)
        else:
            skipped.append(old_id)
    
    # 添加特殊梗（不在旧数据中）
    special_memes = [
        {
            '梗ID': 'xsg_meta_004',
            '原文': '"xx爷"格式（如主子爷、先帝爷、楼主爷）',
            '人物': '元梗',
            '出处': '张飞台词衍生',
            '情境': '通用称呼模板',
            '情绪': ['尊敬', '搞笑'],
            '权重': 5,
            '语义关键词': ['称呼', '尊敬', '元梗', '主子爷', '先帝爷', '楼主爷'],
            '场景标签': ['称呼', '元梗'],
            '变体模板': '[称呼]爷',
            '变量说明': {'称呼': '任意称呼（楼主、层主、大哥等）'},
            '引用频次': 0,
            'effectiveness': 0.0,
            '录入时间': datetime.now().strftime('%Y-%m-%d'),
        },
        {
            '梗ID': 'xsg_zf_004',
            '原文': '这说两句就行了，谁知道先帝爷他听得见听不见',
            '人物': '张飞',
            '出处': '刘备哭祭先皇，张飞打断',
            '情境': '打断过度表达/废话连篇',
            '情绪': ['打断', '讽刺', '搞笑'],
            '权重': 4,
            '语义关键词': ['说两句', '废话', '听不见', '过度表达', '先帝爷'],
            '场景标签': ['打断', '废话', '讽刺'],
            '引用频次': 0,
            'effectiveness': 0.0,
            '录入时间': datetime.now().strftime('%Y-%m-%d'),
        },
    ]
    
    new_genkus.extend(special_memes)
    
    # 按权重排序
    new_genkus.sort(key=lambda x: x['权重'], reverse=True)
    
    print(f"成功转换 {len(new_genkus)} 条数据")
    if skipped:
        print(f"跳过 {len(skipped)} 条未匹配数据: {skipped}")
    
    # 输出新 YAML
    output = "# 新三国梗数据库 v2.0\n"
    output += "# 格式：统一 Agent 专用\n"
    output += f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += f"# 总计：{len(new_genkus)} 条\n\n"
    
    for genku in new_genkus:
        output += "---\n"
        output += yaml.dump(genku, allow_unicode=True, sort_keys=False)
    
    # 保存
    output_file = 'data/genku_v2.yaml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n已保存到: {output_file}")
    
    # 打印统计
    weights = {}
    persons = {}
    for g in new_genkus:
        w = g['权重']
        p = g['人物']
        weights[w] = weights.get(w, 0) + 1
        persons[p] = persons.get(p, 0) + 1
    
    print("\n权重分布:")
    for w in sorted(weights.keys(), reverse=True):
        print(f"  权重{w}: {weights[w]}条")
    
    print("\n人物分布:")
    for p in sorted(persons.keys(), key=lambda x: persons[x], reverse=True):
        print(f"  {p}: {persons[p]}条")

if __name__ == '__main__':
    main()
