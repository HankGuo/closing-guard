import { Link } from "react-router-dom";

export default function About() {
  return (
    <>
      <div className="eyebrow">ABOUT</div>
      <h1 style={{ fontSize: 40, margin: "8px 0 12px" }}>一个会拒绝签字的闭店安全员</h1>
      <p className="muted" style={{ maxWidth: 820, lineHeight: 1.8 }}>
        打烊 Closing Guard 是一个本地优先的 Agent。它不满足于“拍照留痕”，而是由 MiniCPM 判断照片里的
        阀门、电箱、门锁是否真的符合闭店标准；不确定就要求重拍，异常就要求整改，最后交付一份带哈希链的台账。
      </p>

      <div className="grid-2" style={{ marginTop: 24 }}>
        <div className="card pad">
          <h3>它解决什么问题</h3>
          <p className="small muted" style={{ lineHeight: 1.8 }}>
            街边小店没有物业代检，也没有预算装“三关一闭”传感器平台。打烊前的最后十分钟靠纸质表/拍照，
            照片里阀门到底关没关，没人知道。这个系统用旧手机做采集端，用本地 MiniCPM 做核验，
            把“三关一闭”变成一条可追溯的任务链。
          </p>
        </div>
        <div className="card pad">
          <h3>模型分工</h3>
          <div className="small muted" style={{ lineHeight: 1.9 }}>
            <div><b style={{ color: "var(--text)" }}>MiniCPM-V 4.7 1B</b>：看画面，判断阀门/门锁/电箱的语义状态。</div>
            <div><b style={{ color: "var(--text)" }}>MiniCPM-OCR 1.0</b>：读表计、温度计、压力表。</div>
            <div><b style={{ color: "var(--text)" }}>OpenCV</b>：阀门把手角度、画质门控。</div>
            <div><b style={{ color: "var(--text)" }}>规则融合</b>：模型不确定 → 重拍/人工确认，绝不猜。</div>
          </div>
        </div>
      </div>

      <div className="section-title"><div><h2>和现有工作的差别</h2></div></div>
      <div className="card pad">
        <table className="table">
          <thead><tr><th>现有工作</th><th>它做了什么</th><th>我们的差别</th></tr></thead>
          <tbody>
            <tr><td>S1 家庭视觉助手</td><td>被动监控 + 轻量预筛 + MiniCPM-V + 日报</td><td>主动带着人做任务、逐项核验、异常复查、签字台账</td></tr>
            <tr><td>CheckFlow / 问卷星</td><td>数字检查表 + 拍照留痕</td><td>模型判断照片内容；不通过不能提交</td></tr>
            <tr><td>商场三关一闭平台</td><td>传感器 + 云 + 物业逐店检查 + 年费</td><td>零硬件、本地、商户自用</td></tr>
            <tr><td>阀门检查专利</td><td>贴标记 + 固定摄像头 + 基准图</td><td>无标记、手持、多模态、边缘推理</td></tr>
            <tr><td>明厨亮灶</td><td>云摄像头 + 营业中食安 AI</td><td>闭店安全、本地、不上传视频</td></tr>
          </tbody>
        </table>
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        <div className="card pad">
          <h3>安全声明</h3>
          <p className="small muted" style={{ lineHeight: 1.8 }}>
            这是辅助检查与记录工具，不替代消防、燃气、市场监管的法定检查，也不构成安全保证。
            模型会出错；所有“未通过/待确认”项必须人工复核。闻到燃气味、发现明火或电气异常，请立即撤离并拨打 119。
          </p>
        </div>
        <div className="card pad">
          <h3>开源与复现</h3>
          <p className="small muted" style={{ lineHeight: 1.8 }}>
            代码与文档遵循 Apache-2.0。模型权重不随仓库分发，使用 <span className="mono">scripts/download_models.sh</span>
            从 ModelScope 下载；端到端测试需要真实的 llama.cpp 模型服务，不使用 mock。
          </p>
          <div className="row" style={{ marginTop: 10 }}>
            <Link className="btn btn-sm" to="/">返回首页</Link>
            <a className="btn btn-sm btn-ghost" href="https://github.com/HankGuo/closing-guard" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </div>
      </div>
    </>
  );
}
