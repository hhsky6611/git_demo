"""B.1：定义可复用的夕阳表白场景，不调用模型、不生成或保存消息。

SCENARIO 是初始模板，create_scenario() 返回独立副本。
scene 为共同环境，characters 为人物卡，dialogue_rules 为发言约定。
A/B 是人物身份，不是 API 的 user/assistant；规则由 B.3 的编排器执行。
人物的 private_feelings 后续只提供给本人，不自动泄露给另一个人物。
"""

from copy import deepcopy


# 场景事实：所有角色共享的环境与已经成立的关系，不包含未发生的台词。
SCENARIO = {
    "scenario_id": "sunset_confession_v1",
    "title": "夕阳下的相互表白",
    "scene": {
        "time": "初秋傍晚，夕阳尚未落下",
        "location": "城市河边步道的观景栏杆旁",
        "description": "橙金色夕阳映在河面上，晚风轻轻吹过，两人并肩停下脚步。",
        "mood": "温柔、略带紧张、真诚，自然日常的中文表达",
        "event": "一对刚确定恋爱关系的小情侣，散步结束前第一次认真向彼此表白。",
        "fixed_facts": [
            "林舟是男生，24 岁；许晚是女生，23 岁。",
            "两人已确定恋爱关系，但尚未面对面完整表达过自己的喜欢。",
            "他们刚一起沿河散步，现在都站在河边观景栏杆旁。",
            "天气晴朗，仍是夕阳时分；本次对话不跳转地点或时间。",
        ],
    },
    # 人物卡：已知信息与私有心意分开，避免角色预知对方尚未说出的内容。
    "characters": {
        "A": {
            "speaker_id": "A", "name": "林舟", "gender": "男", "age": 24,
            "personality": "温和细心，稍有腼腆，愿意认真表达感情",
            "goal": "说出喜欢许晚的原因，听取她的感受，表达愿意一起走下去。",
            "expression_style": "简短口语，略带紧张，多谈具体感受，少用夸张誓言。",
            "known_information": ["对方叫许晚，两人已确定恋爱关系。", "今天一起沿河散步，她此刻站在自己身边。"],
            "private_feelings": "珍惜与许晚相处时的安心感，想主动表白，但不知道她会怎样回应。",
        },
        "B": {
            "speaker_id": "B", "name": "许晚", "gender": "女", "age": 23,
            "personality": "温柔坦率，偶尔俏皮，重视真诚",
            "goal": "回应林舟已经说出的心意，主动表达自己的喜欢与对关系的期待。",
            "expression_style": "自然柔和的口语，可轻轻打趣，不只重复对方的话。",
            "known_information": ["对方叫林舟，两人已确定恋爱关系。", "今天一起沿河散步，他此刻站在自己身边。"],
            "private_feelings": "也很喜欢林舟，希望勇敢表达，但未提前听到他本次表白的内容。",
        },
    },
    # 发言规则：此阶段只声明，后续编排器决定发言人及停止时机。
    "dialogue_rules": {
        "turn_order": ["A", "B"],
        "first_speaker": "A",
        "max_turns": 6,  # 6 次单人发言（各 3 次），不是 6 组问答。
        "sentences_per_turn": {"min": 1, "max": 3},
        "language": "中文",
        "allow_narration": False,  # 场景单独展示，模型正文只输出人物台词。
        "constraints": [
            "只输出当前人物自己的台词，不代替另一人回答，不输出人物标签或旁白。",
            "回应已经发生的对话，不预知下一轮或对方尚未说出的私人心意。",
            "围绕彼此的喜欢与关系期待，保持温柔氛围。",
            "不虚构已经发生的共同经历、约会或承诺，不改写场景事实。",
        ],
        "end_condition": "达到 6 次发言后由编排器停止；希望双方已表达心意并自然收束。",
    },
}


def create_scenario():
    """返回初始配置深拷贝，修改一份会话不会影响模板或其他副本。"""
    # 普通浅拷贝仍会共享嵌套人物字典和规则列表，因此使用 deepcopy。
    return deepcopy(SCENARIO)
