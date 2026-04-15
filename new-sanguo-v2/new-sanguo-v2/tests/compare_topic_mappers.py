"""
TopicMapper 回归测试（v2.5.14 扩展版）

测试范围：
- 原7类话题准确率
- 新增3类（美食、电影、动漫）准确率
- 边界情况处理
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_sanguo.topic_mapper import TopicMapper, TopicCategory

# 测试用例：覆盖10类话题 + 边界情况
TEST_CASES = [
    # === 电竞赛事 (ESPORTS) ===
    ("T1今天比赛太猛了，3:0零封对手", "ESPORTS", "电竞赛事"),
    ("Faker这波操作你怎么看", "ESPORTS", "电竞赛事"),
    ("LPL春季赛决赛预测", "ESPORTS", "电竞赛事"),
    
    # === 科技数码 (TECH) ===
    ("GPT-5要发布了，这次参数又翻倍", "TECH", "科技数码"),
    ("苹果新品发布会看了吗", "TECH", "科技数码"),
    ("这显卡性能提升不大啊", "TECH", "科技数码"),
    
    # === 娱乐 (ENTERTAINMENT) ===
    ("这部电影豆瓣才5分，烂片", "ENTERTAINMENT", "娱乐"),
    ("那首歌的版权又出问题了", "ENTERTAINMENT", "娱乐"),
    
    # === 时政 (POLITICS) ===
    ("特朗普又发推特了", "POLITICS", "时政"),
    ("俄乌冲突最新进展", "POLITICS", "时政"),
    
    # === 体育 (SPORTS) ===
    ("湖人今天逆转取胜", "SPORTS", "体育"),
    ("世界杯决赛点球大战", "SPORTS", "体育"),
    
    # === 游戏 (GAME) ===
    ("这单机游戏剧情太好了", "GAME", "游戏"),
    ("手游抽卡又歪了", "GAME", "游戏"),
    
    # === 日常 (DAILY) ===
    ("今天吃什么好呢", "DAILY", "日常"),
    ("外面下雨了记得带伞", "DAILY", "日常"),
    ("好累啊不想上班", "DAILY", "日常"),
    
    # === 新增：美食 (FOOD) ===
    ("这家火锅太好吃了", "FOOD", "美食"),
    ("川菜和粤菜哪个更好", "FOOD", "美食"),
    
    # === 新增：电影 (MOVIE) ===
    ("诺兰的新片看了吗", "MOVIE", "电影"),
    ("这部电影票房破纪录了", "MOVIE", "电影"),
    
    # === 新增：动漫 (ANIME) ===
    ("这部番剧追了好久了", "ANIME", "动漫"),
    ("火影忍者完结十周年", "ANIME", "动漫"),
    
    # === 边界/模糊情况 ===
    ("游戏和电影哪个更好玩", "GAME", "边界-游戏vs电影"),
    ("今天天气不错", "DAILY", "日常-天气"),
    ("你说什么", None, "无意义"),
    ("", None, "空输入"),
    ("12345", None, "纯数字"),
]


def test_mapper():
    """测试 TopicMapper（扩展版）"""
    print("=" * 60)
    print("【TopicMapper 回归测试（10类话题）】")
    print("=" * 60)
    
    mapper = TopicMapper()
    results = []
    total_time = 0
    
    for text, expected, desc in TEST_CASES:
        start = time.perf_counter()
        try:
            topic, confidence = mapper.identify_topic(text)
        except Exception as e:
            topic, confidence = f"ERROR: {e}", 0.0
        elapsed = time.perf_counter() - start
        total_time += elapsed
        
        matched = (expected is None and topic == TopicCategory.UNKNOWN) or \
                  (expected and topic.name == expected)
        
        result = {
            'text': text[:30] + '...' if len(text) > 30 else text,
            'expected': expected or 'UNKNOWN/None',
            'actual': topic.name if hasattr(topic, 'name') else str(topic),
            'confidence': confidence,
            'matched': matched,
            'time_ms': elapsed * 1000,
            'desc': desc
        }
        results.append(result)
        
        status = "✅" if matched else "❌"
        print(f"{status} [{desc}] 输入: '{text[:25]}...' -> {topic.name if hasattr(topic, 'name') else topic} (置信度: {confidence:.2f}, 耗时: {elapsed*1000:.2f}ms)")
    
    correct = sum(1 for r in results if r['matched'])
    accuracy = correct / len(results) * 100
    avg_time = total_time / len(results) * 1000
    
    print(f"\n【统计】准确率: {correct}/{len(results)} ({accuracy:.1f}%), 平均耗时: {avg_time:.2f}ms")
    return results, accuracy, avg_time


def test_suggest_genku_tags():
    """测试新增类别的 suggest_genku_tags"""
    print("\n" + "=" * 60)
    print("【suggest_genku_tags 新增类别测试】")
    print("=" * 60)
    
    mapper = TopicMapper()
    tag_cases = [
        ("这家火锅太好吃了", "FOOD", "美食"),
        ("诺兰新片烂透了", "MOVIE", "电影-烂片"),
        ("这部番剧完结了", "ANIME", "动漫-完结"),
    ]
    
    for text, expected_topic, desc in tag_cases:
        tags = mapper.suggest_genku_tags(text)
        matched = tags['topic'] == TopicCategory[expected_topic].value
        status = "✅" if matched else "❌"
        print(f"{status} [{desc}] topic={tags['topic']}, emotions={tags['emotions'][:2]}, scenes={tags['scenes'][:2]}")


if __name__ == "__main__":
    test_mapper()
    test_suggest_genku_tags()
    print("\n🎉 TopicMapper 回归测试完成")
