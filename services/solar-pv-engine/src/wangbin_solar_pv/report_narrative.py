"""Evidence-constrained editorial content for the frozen preliminary-report outline.

This module organizes *writing*, never calculates energy or finance. Item guidance
identifies a distinct professional question and the material needed to answer it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# One independently authored research question per frozen item, in chapter order.
ITEM_QUESTIONS: dict[str, tuple[str, ...]] = {
    "CH01": (
        "确认项目身份、编制时点及演示数据与真实项目的界限。",
        "交代直交流规模和预测电量的计量边界，避免把发电预测当作保证值。",
        "区分工程费用估算与尚未形成的完整投资回报评价。",
        "解释发电、可交付和可结算电量之间的边界及售电前提。",
        "将待核实事项与可引用的模型结果分开，避免提前给出投资建议。",
    ),
    "CH02": (
        "说明建设动机来自哪一项用能或供电需求；没有业主资料时不认定必要性。",
        "明确价格、评价期及现金事件口径，不用收入替代现金流。",
        "核对适用标准的版本和项目适用性，引用标准不等于取得审批。",
        "追溯资料的时间范围、授权和更新日期，指出缺少站址实证的影响。",
        "区分计算假设、编辑性设想和经核验的现场事实。",
    ),
    "CH03": (
        "明确投资和运营主体是否有授权文件，不能以虚构企业充当业主。",
        "说明拟建对象与场址分类，核实其是否符合项目类型边界。",
        "厘清建筑使用权或土地使用权与运营期限的衔接。",
        "说明负荷消纳或集中送出的拟议方式及结算前提。",
        "只有建设任务与需求依据一致，才能进一步论证建设必要性。",
    ),
    "CH04": (
        "核实项目位置、边界和排除区；没有测绘成果不能认定可建设范围。",
        "结合面积口径、地形或屋面障碍复核阵列布置的可实施空间。",
        "取得权属及使用期限依据，分析其与评价期的匹配。",
        "取得遮挡测量和结构承载结论，再确定可布置区域及加固需求。",
        "核查施工通道、灾害暴露和生态限制对工程组织的影响。",
        "汇总仍需开展的场址专题，不以概念条件替代勘察结论。",
    ),
    "CH05": (
        "核实资源数据集的覆盖期、时区、质量控制及使用许可。",
        "分清水平面与阵列面辐照口径；没有辐照分量不作资源等级判断。",
        "气温和风速的时序质量会影响温度损失与结构设计，应核对原始资料。",
        "评价多年代表性需要逐年观测或授权典型年，单年合成时序不足以替代。",
        "检查倾角、方位角及转置方法对阵列面资源的影响，不反推辐照值。",
        "通过独立数据交叉验证预测不确定性，缺失时应保持限定性判断。",
    ),
    "CH06": (
        "先核实可用面积与建设任务的对应，再确认装机容量是否可落地。",
        "组件数量与布置间距需同时满足阵列遮挡、通行和消防要求。",
        "说明直流装机、逆变器容量及容配比的当前配置，不据此证明接入可行。",
        "仅在替代方案有同口径计算与工程条件时比较，不虚构比选结果。",
        "比较设备、占地、发电与投资口径时应明确权重及约束。",
        "区分屋顶结构消防或地面用地送出等项目类型专属方案。",
    ),
    "CH07": (
        "说明拟用组件和逆变器的容量参数，型号与认证仍需设备资料校核。",
        "支架倾角、方位角及排布密度须与实际结构和遮挡条件相协调。",
        "串并联方案需复核极端温度下的电压、电流和逆变器跟踪范围。",
        "明确各项损失所属的物理边界及是否已在上游数据中计入。",
        "核实组串汇流、逆变、计量和保护之间的实际接口。",
        "未申报储能时不拟制储能收益；分类专项设计另按实证条件开展。",
    ),
    "CH08": (
        "说明时序资源、系统损失及首年退化进入预测的先后关系。",
        "月度电量反映合成输入下的季节变化，首年总量需与月度合计核对。",
        "年度衰减与设备更换事件应分别解释，不能以单一衰减率覆盖两者。",
        "等效小时、容量因数和性能比口径不同，不可互相代替或视为实测。",
        "可利用电量、限发和可交付电量应逐边界对账，不推定已全部结算。",
        "复核异常高的等效利用小时及资源代表性，再讨论长期预测可信度。",
    ),
    "CH09": (
        "拟议接入点与电压等级须以电网接入论证为准。",
        "现有变压器或线路参数不等于获准接入容量，应取得电网校核意见。",
        "保护配置、送出路径和升压设施仍需专题设计。",
        "并网协议与交易准入分别核验，不能用技术方案替代批复。",
        "限发条件取决于接网和调度约束，应取得具名电网资料。",
    ),
    "CH10": (
        "屋顶负荷应按同一时区和计量粒度与发电时序匹配；地面项目不适用自用模型。",
        "区分自用、上网、限发及实际结算边界，不把预测发电量等同于收入电量。",
        "分时电价与节省电费须结合生效合同和计量规则复核。",
        "交易主体、结算周期和合同价格未确认前只能描述拟议售电模式。",
        "逐时市场价格和其他收益只有明确来源与执行规则才能计入。",
        "未配置储能时不开展储能调度收益评价。",
    ),
    "CH11": (
        "功能分区应以建筑可使用面或地面征地红线及排除区为边界。",
        "屋顶支架锚固与地面基础分别需要结构或地勘成果支撑。",
        "消防疏散及承载安全需具名专业复核，不据概念布置认定合格。",
        "复核运输、吊装、施工道路、排水对施工组织的限制。",
        "缺少专项勘察及工程量时暂不锁定土建费用和工期。",
    ),
    "CH12": (
        "减排量需要经确认的电量边界与排放因子，未核算不列确定效益。",
        "生态和水土保持措施需结合场址调查及适用审批确定。",
        "消防设计与施工运行安全分别落实责任和专项审查。",
        "说明周边主体与利益影响仍需沟通，不能虚构协商结果。",
        "未取得专题评价和审批时不得认定项目合规。",
    ),
    "CH13": (
        "开发责任分工应落实权属、技术、并网及投资前置条件。",
        "初设、采购、施工、调试和验收应按依赖关系安排而非预填日期。",
        "接入审批、设备采购和施工窗口形成关键路径，需逐项核实。",
        "识别施工停工、供应与并网延误的条件及缓释责任。",
        "只有前置资料闭合后才形成可执行里程碑与启动条件。",
    ),
    "CH14": (
        "估算仅依据当前合成费用项目和计价口径，不等于市场报价。",
        "组件、逆变器与材料费用需对数量、单价和税口径逐项复核。",
        "屋顶加固或地面基础、道路及送出工程需独立核量。",
        "管理、前期与预备费应按已声明的费用边界核对有无重复。",
        "建设期利息取决于真实提款和进度，不由工程总额推断。",
        "区分含税、可抵扣与单位投资的分母口径。",
    ),
    "CH15": (
        "运维、保险和使用权成本需以费用项目及合同依据分别说明。",
        "折旧和残值属于非现金口径，不能直接作为终期收款。",
        "更换年份与设备寿命需和发电预测、现金支出保持一致。",
        "实际所得税与增值税现金缴纳需由税基及支付事件支持。",
        "核对现金费用与非现金折旧，防止年度成本重复计列。",
    ),
    "CH16": (
        "收入预测不等于实际回款；终期残值尚需可执行的处置依据。",
        "项目投资现金流需完整覆盖投资、运营、税与终期事件。",
        "股东现金流需单独核实出资、借款、偿债与分配事件。",
        "净现值与内部收益率必须以完整且有日期的现金事件计算。",
        "回收期须有逐期净现金流，不据工程投资与单年收入推算。",
        "平准化成本须用同期无杠杆成本及同边界可交付电量。",
        "偿债覆盖指标要求合同还本付息及可供偿债现金流。",
        "盈亏平衡与目标差距须有独立重算及明确目标口径。",
    ),
    "CH17": (
        "单因素扰动需要独立运行及响应结果，基准参数表不是敏感性分析。",
        "乐观与悲观情景必须各自声明参数组合和运行身份。",
        "稳健性与阈值须经完整重算，不以基准结果外推。",
        "权属、资源、工程、并网及交易风险应分别描述影响路径。",
        "检验任何判断是否超出数据授权、计量边界和项目类型。",
    ),
    "CH18": (
        "当前仅可形成条件性阶段意见，不将合成测算表述为项目可行。",
        "列出仍可能独立否决工程推进的权属、资源及接网事项。",
        "明确进入下一阶段需要的资料和专题，不虚构触发阈值。",
        "按工程、并网、价格与财务专题提出分工明确的核查事项。",
        "决策里程碑以审批和专业审查完成为前提，不许诺开工日期。",
    ),
}


def guidance(item_id: str, chapter_titles: tuple[str, ...]) -> str:
    chapter, number = item_id.split(".")
    questions = ITEM_QUESTIONS[chapter]
    if len(questions) != len(chapter_titles):
        raise ValueError("REPORT_EDITORIAL_COVERAGE")
    return questions[int(number) - 1]


def load_editorial_fixture(pv_type: str, result_hash: str, root: Path | None = None) -> dict[str, Any]:
    """Load and bind an explicitly selected editorial fixture to one canonical result."""
    base = root or Path(__file__).with_name("fixtures") / "solar_pv_editorial"
    path = base / f"{pv_type}.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    fixture["result_hash"] = result_hash
    return validate_fixture(fixture, pv_type=pv_type, result_hash=result_hash) or fixture


def validate_fixture(fixture: dict[str, Any] | None, *, pv_type: str, result_hash: str) -> dict[str, Any] | None:
    """Require an explicit, identity-bound synthetic opt-in; never load automatically."""
    if fixture is None:
        return None
    if (not isinstance(fixture, dict) or fixture.get("schema_version") != "solar-pv-editorial-1"
            or fixture.get("mode") != "SYNTHETIC_DEMO"
            or fixture.get("evidence_kind") != "EDITORIAL_TEST_ASSUMPTION"
            or fixture.get("pv_type") != pv_type or fixture.get("result_hash") != result_hash):
        raise ValueError("REPORT_EDITORIAL_IDENTITY")
    chapters = fixture.get("chapters")
    if not isinstance(chapters, dict) or set(chapters) != set(ITEM_QUESTIONS):
        raise ValueError("REPORT_EDITORIAL_COVERAGE")
    for chapter_id, record in chapters.items():
        if (not isinstance(record, dict) or not isinstance(record.get("background"), str)
                or not isinstance(record.get("proposal"), str)
                or not isinstance(record.get("verification"), str)
                or not all(record[k].strip() for k in ("background", "proposal", "verification"))
                or any(len(record[k]) > 280 for k in ("background", "proposal", "verification"))):
            raise ValueError(f"REPORT_EDITORIAL_CHAPTER:{chapter_id}")
    samples = fixture.get("golden_sample_chapters", ())
    if not isinstance(samples, list) or not set(samples).issubset(set(ITEM_QUESTIONS)):
        raise ValueError("REPORT_EDITORIAL_GOLDEN_SAMPLES")
    return fixture
