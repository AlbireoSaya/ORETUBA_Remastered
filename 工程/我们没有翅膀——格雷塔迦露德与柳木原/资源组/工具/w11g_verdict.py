# -*- coding: utf-8 -*-
"""W11g · 产出 门控_38组目视终裁.tsv（38 行，逐组目视依据）。
判定规则：
  R1 候选呈现**不同的具体内容**（不同角色名/剧集名/游戏 LOGO/描绘物件/文案）→ 拆
  R2 候选为**同一具体内容**，差异仅在画幅/裁切/分辨率/字体/配色/描边/装饰 → 不拆
"""
import os, json, sys
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11g"))
assert UNI.startswith(r"E:\ZCode Workspace\Galgame")

V = {
 "miy02a": ("拆",
   "ot/pic=蓝裙魔法少女CG（尖顶帽＋披风、双臂前伸、蓝色能量背景）；np/pic=白发少女**立绘**（白＋粉水手服、双手交叠、闭眼微笑、透明底）。两者为不同角色、不同画，**确为不同素材**",
   "已分离：立绘\\miy02a.png(np) ＋ CG背景\\cg_miy02a.png(ot/pic)，无需再动"),
 "bg41": ("不拆",
   "6 个候选同为「空教室」：绿天花板、黑板、左侧窗列、成排课桌，桌椅/窗格/黑板位置逐一致；ot/ota/otp/otr 取景最宽，otv/np 向内裁切更紧",
   "保留现状（选 np）"),
 "bg41a": ("不拆",
   "6 个候选同为「夕阳红光照的空教室」：同一黑板/课桌/窗格/窗帘，仅整体色温偏红；ot 取景宽、np 裁切更紧",
   "保留现状（选 np）"),
 "bg72": ("不拆",
   "6 个候选同为「蓝天白云」：云团形状与分布、天地渐变逐一致；ot 见更多地面，otv/np 裁切更近",
   "保留现状（选 np）"),
 "bg72b": ("不拆",
   "6 个候选同为「夜空云」：深蓝夜空、青白云带、星点位置一致；仅取景范围不同",
   "保留现状（选 np）"),
 "ef05a": ("不拆",
   "4 个候选同为「蓝色星云/星芒特效」：中心光晕、螺旋云带、星芒十字方向与散布星点逐一致，仅画幅/裁切不同",
   "保留现状（选 np）"),
 "bg01": ("不拆",
   "ot/ota/otp(1200×600) 与 otv(1440×544) 同为「白天街景」：中央弧形玻璃商场、左侧药妆招牌(HEART/モチ/薬/NECO)、右侧深蓝玻璃高楼、前方天桥，逐一致；otv 画幅更宽（左右多出街景）",
   "保留现状（选 otv）"),
 "bg01b": ("不拆",
   "ot/ota/otp/otr(1200×600) 与 otv(1440×544) 同为「夜景街景」：同机位同建筑，窗内灯光与右侧暖黄高楼一致；仅画幅不同",
   "保留现状（选 otv）"),
 "tl_galry": ("不拆",
   "三源同为标题菜单「GALLERY」按钮的三态图(常态/悬停/选中)：ot=粗描边衬线体(黑/橙/藏青)，ota=同字加雪花装饰(灰/青/紫)，otp=细线体＋椭圆描边。**文字内容一致**，差异属各作标题画面皮肤",
   "保留现状（选 ot）"),
 "tl_cfg": ("不拆",
   "同为「CONFIG」按钮三态图：ot=粗描边(黑/橙/藏青)，ota=雪花装饰，otp=细线＋椭圆。文字一致",
   "保留现状（选 ot）"),
 "tl_exit": ("不拆",
   "同为「EXIT」按钮三态图：ot=粗描边，ota=雪花装饰，otp=细线＋椭圆。文字一致",
   "保留现状（选 otp）"),
 "tl_load": ("不拆",
   "同为「LOAD」按钮三态图：ot=粗描边，ota=雪花装饰，otp=细线＋椭圆。文字一致",
   "保留现状（选 ot）"),
 "tl_chk": ("不拆",
   "两源同为「红色对勾」勾选标记：红勾＋白/蓝描边，勾形与描边一致，仅画布与缩放不同(ota 41×42 / otp 52×34)",
   "保留现状（选 otp）"),
 "ec2_name": ("不拆",
   "两源同为章标题文字「千歳 鷲介 編」：字形一致，ot=黑色描边体(172×24)，otp=蓝色(96×19)。**文案相同**",
   "保留现状（选 ot）"),
 "ss_bg1": ("拆",
   "ot=「私立美空学園」校门**纯场景底板**(800×600，无 UI 图层)；otv=同一校门画面带＋下方 468px UI 面板(日期表/角色头像行/Q-Save 等按钮/章卡缩略图)。两者粒度不同",
   "已由 W11d 拆为 ss_bg1_base.png / ss_bg1_full.png，无需再动"),
 "ss_bg2": ("拆", "同 ss_bg1：ot=场景底板、otv=画面带＋UI 面板整页（角色头像/按钮/日期表）", "已由 W11d 拆分"),
 "ss_bg3": ("拆", "同 ss_bg1：ot=场景底板、otv=画面带＋UI 面板整页", "已由 W11d 拆分"),
 "ss_bg4": ("拆", "同 ss_bg1：ot=场景底板、otv=画面带＋UI 面板整页", "已由 W11d 拆分"),
 "ss_bg5": ("拆", "同 ss_bg1：ot=场景底板、otv=画面带＋UI 面板整页", "已由 W11d 拆分"),
 "tl_01": ("拆",
   "ota=「その後のタカシ」三态按钮(白/青/紫)；otp=「ある日の明日香」三态按钮。**文案不同，属不同剧集入口**",
   "拆出 tl_01_altotp.png"),
 "tl_02": ("拆",
   "ota=「その後の鷲介」；otp=「ある日の京」。文案不同",
   "拆出 tl_02_altotp.png"),
 "tl_03": ("拆",
   "ota=「その後の隼人」；otp=「ある日の美咲」。文案不同",
   "拆出 tl_03_altotp.png"),
 "tl_04": ("拆",
   "ota=「その後のヨージ」；otp=「千歳 鷲介編 プロローグ」。文案不同",
   "拆出 tl_04_altotp.png"),
 "ec3_name": ("不拆",
   "两源同为「成田 隼人 編」：字形一致，ot=黑色(172×24)，otp=白/浅蓝(100×19)。**文案相同**",
   "保留现状（选 ot）"),
 "ec1_bg": ("不拆",
   "ot/ota(800×600) 与 otv(1013×658) 同为第1章标题卡底图：粉底网点＋斜置宝剑，位置一致；otv 额外叠加章标题「羽田 鷹志 編 / Chapter: Takashi Haneda」「Wing of Hawk」与底部日期表",
   "保留现状（选 otv）"),
 "ec2_bg": ("拆",
   "ot/ota=粉底＋斜置钢笔(无字)；otv=同钢笔＋章标题「千歳 鷲介 編」＋日期表；**otp=完全不同的图：暖色餐厅店面「Alexander Restaurant」街景**",
   "拆出 ec2_bg_altotp.png（餐厅图）"),
 "ec3_bg": ("拆",
   "ot/ota=粉底＋黄色安全帽(无字)；otv=同安全帽＋「成田 隼人 編」＋日期表；**otp=完全不同的图：夜晚霓虹街道（剧场前街景）**",
   "拆出 ec3_bg_altotp.png（夜景街道）"),
 "ec4_bg": ("不拆",
   "ot/ota(800×600) 与 otv(1013×658) 同为第4章标题卡底图：粉底＋金边盾徽(鹰/鸟纹)，位置一致；otv 叠加「羽田 鷹志 編 / Wing of Condor」与日期表",
   "保留现状（选 otv）"),
 "ec6_bg": ("不拆",
   "ot(800×600) 与 otv(1013×658) 同为暗红「奈落の底」纹理底图；otv 叠加「奈落の底 / Abyss」与日期表",
   "保留现状（选 otv）"),
 "tl_new": ("拆",
   "ota=「New!」**含感叹号**(80×29)；otp=「New」**无感叹号**(72×23)；字体、红色填充、蓝白描边完全一致，仅文案不同",
   "拆出 tl_new_altotp.png"),
 "gl_music": ("拆",
   "ot=「音楽鑑賞 / music」；ota=「AfterStory 音楽 / after story music」。文案不同",
   "拆出 gl_music_altot.png"),
 "gl_chr2": ("拆",
   "ot=「山科 京 / yamashina miyako」；ota=「玉泉 日和子 / tamaizumi hiyoko」。**不同角色的名字**（按序号误并）",
   "拆出 gl_chr2_altot.png"),
 "gl_chrbg": ("拆",
   "ot=「背景 / background」；ota=「AfterStory 背景 / after story back」。文案不同",
   "拆出 gl_chrbg_altot.png"),
 "gl_scene": ("不拆",
   "两源同为「シーン回想 / scene replay」：文案、字体、三态配色逐一致，仅画布高差 3px",
   "保留现状（选 ota）"),
 "tl_logo": ("拆",
   "ota=「俺たちに翼はない After Story」游戏 LOGO(蓝，雪花装饰，291×115)；otp=「俺たちに翼はない ～Prelude～」游戏 LOGO(紫，361×132)。**不同作品的 LOGO**",
   "拆出 tl_logo_altota.png"),
 "gl_chr1": ("不拆",
   "两源同为「渡来 明日香 / watarai asuka」：文案、字体、三态配色逐一致，仅画布高差 2px",
   "保留现状（选 ota）"),
 "gl_chr5": ("拆",
   "ot=「羽田 小鳩 / haneda kobato」；ota=「その他 / others」。**不同条目**",
   "拆出 gl_chr5_altot.png"),
 "gl_chr4": ("拆",
   "ot=「鳳 鳴 / ootori naru」；ota=「羽田 小鳩 / haneda kobato」。**不同角色的名字**",
   "拆出 gl_chr4_altot.png"),
}


def atomic_write(path, text):
    tmp = path + ".tmp_w11g"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def main():
    gs = json.load(open(os.path.join(WORK, "_38组清单.json"), encoding="utf-8"))
    assert len(gs) == 38, len(gs)
    rows = ["统一名\t类别\t候选数\t候选(源:尺寸:ar)\t目视结论(不拆|拆)\t依据（描述看到了什么）\t处置"]
    n_split = n_keep = 0
    for g in gs:
        name = g["统一名"]
        stem = name[:-4]
        cands = g["候选"]
        # 候选列: 源:原名 尺寸 ar
        import re
        items = []
        for it in [c.strip() for c in cands.split(";")]:
            m = re.match(r"(\w+):(\S+)\s+(\d+x\d+)\s+ar=([\d.]+)", it)
            if m:
                items.append("%s:%s:%s:ar=%s" % (m.group(1), m.group(2), m.group(3), m.group(4)))
        verdict, why, action = V[stem]
        if verdict == "拆":
            n_split += 1
        else:
            n_keep += 1
        rows.append("\t".join([name, g["类别"], str(g["候选数"]), " ; ".join(items), verdict, why, action]))
    print("拆=%d 不拆=%d 合计=%d" % (n_split, n_keep, n_split + n_keep))
    atomic_write(os.path.join(UNI, "门控_38组目视终裁.tsv"), "\n".join(rows) + "\n")
    print("写出:", os.path.join(UNI, "门控_38组目视终裁.tsv"))


if __name__ == "__main__":
    main()