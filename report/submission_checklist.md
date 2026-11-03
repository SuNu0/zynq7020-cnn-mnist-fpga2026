# AMD自主选题指南逐项对照

依据用户提供的《2026 FPGA赛道选题指南 AMD》3.3节，PDF物理页22—25（正文页19—22），及第28页的决赛海报说明。此文件是按所提供版本整理，不代表赛方正式验收。

| 要求 | 本仓库对应 | 状态 |
|---|---|---|
| 完整实际工程与源码 | rtl/ software/ model/ scripts/ tb/ output/ | 已提供实际V3部署链路，未公开不使用的V1历史电路 |
| 仿真和功能验证 | reports/v3_simulation.log、tb/vectors/、reports/physical_board_test.txt | 历史75组RTL、40张板测记录；本次新增检查另列 |
| 资源 时钟 性能指标 | output/utilization.rpt、timing_summary.rpt、report/design_report.md | 已提供，明确软件/周期/板测边界 |
| 上板与实测对照 | output/、scripts/、software/、board/photos/ | BIT/ELF、板测标签与预测数据、两张板卡照片 |
| 可复现构建脚本 | scripts/create_project.tcl、build_hardware.tcl、build_firmware.py | 指南允许的2025.2版本；独立目录清晰声明依赖 |
| 公开及再分发许可 | 根LICENSE及third_party_notices.md | 原创V3部分MIT，第三方原许可保留 |
| skill/及说明 | skill/README.md及通用校验脚本、踩坑清单 | 适用场景 方法 效果 失效条件均列出 |
| 大模型协作记录 | report/ai_collaboration.md | 实际材料会话节选和自纠错，非完整研发原始日志 |
| 优化前后比较和判断依据 | report/design_report.md | V2/V3精度与资源对比，不虚构加速比 |
| 英文目录文件名 | 全仓库及Release工程内部路径 | 校验脚本检查，标准README.md、LICENSE例外沿用指南示例 |
| 演示视频与承诺书 | 比赛平台另行提交 | 尚未提供；不在公开仓库发布带个人签字的承诺书 |
| 决赛一页英文PPT海报 | 尚未提供 | 当前海报为中文可编辑PSD及PDF初稿，不能代替决赛英文PPT |

已有两张实拍放在board/photos，原Word/PDF和PSD中的占位区域仍可继续完善。提交GitHub链接不等于演示视频、签字授权书及决赛附件已全部完成。
