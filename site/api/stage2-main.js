const { STAGE2_SYSTEM_PROMPT, readCorpus, callOpenRouter } = require("./_shared");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  try {
    const { design, stage1_report, hyde_doc } = req.body;
    if (!design || !stage1_report || !hyde_doc) {
      return res.status(400).json({ error: "design, stage1_report and hyde_doc are required" });
    }

    const corpus = readCorpus("stage1.txt") + readCorpus("stage2_technical.txt");
    const userMessage =
      `${corpus}\n\n===== HYPOTHETICAL TECHNICAL FRAMING (context only) =====\n\n${hyde_doc}` +
      `\n\n===== ORIGINAL DESIGN DESCRIPTION =====\n\n${design}` +
      `\n\n===== STAGE 1 FINDINGS =====\n\n${stage1_report}`;

    const { text, usage } = await callOpenRouter(STAGE2_SYSTEM_PROMPT, userMessage, 16000);
    res.status(200).json({ report: text, usage });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
};

module.exports.config = { maxDuration: 300 };
