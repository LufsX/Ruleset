# [Ruleset](https://ruleset.isteed.cc)

## 借物表

- [SukkaW/Surge](https://github.com/SukkaW/Surge)
- [langkhach270389/Surge-LK](https://github.com/langkhach270389/Surge-LK)
- [DivineEngine/Profiles](https://github.com/DivineEngine/Profiles)

## 本地构建

```bash
python -m pip install -r Tools/requirements.txt
python -m unittest discover -s Tools/tests -v
python Tools/build.py
```

完整构建需要网络连接和 `mihomo` 命令。构建过程先写入临时目录，所有平台产物校验通过后才替换 `Public/`；失败时会保留上一次成功的输出。

构建器通过 `PluginSpec` 显式声明任务、阶段、依赖和写入目标，并集中列在 `Tools/build_manifest.py`。流水线选择目标后会自动包含所有前置阶段，只执行需要的任务，并并行运行同一阶段中无依赖关系的任务；注册时会拒绝重复插件、重复任务和写入目标冲突。
