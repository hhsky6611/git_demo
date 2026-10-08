# B.1：夕阳下的相互表白

配置位于 `app/scenario.py`，使用带中文注释的 Python 字典定义，导入时不调用接口。

初秋傍晚的河边步道，林舟（男，24 岁）与许晚（女，23 岁）是一对刚确定恋爱关系的小情侣，夕阳下第一次认真向彼此表白。林舟温和腼腆，先主动表达；许晚温柔坦率，回应已经说出的心意并表达自己的喜欢。姓名、年龄和具体地点是可修改的模拟设定。

`scene` 保存环境与固定事实；`characters` 保存人物目标、风格、已知信息与私人心意；`dialogue_rules` 约定 A → B 交替，共 6 次单人发言，每次 1–3 句，只输出中文台词。场景描述单独提供，不混入台词正文。私人心意后续只提供给本人，人物 A/B 不等于接口 user/assistant。

`create_scenario()` 返回独立副本，方便多次会话从相同条件开始。目前仅完成配置，轮流发言和停止规则尚未执行，实际模型表现留给 B.3–B.4 验证。

在 eqq/ 目录检查配置，无需启动 Docker：

```bash
python3 -B -c 'import json; from app.scenario import create_scenario; print(json.dumps(create_scenario(), ensure_ascii=False, indent=2))'
```
